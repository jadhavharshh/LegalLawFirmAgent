from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import requests
import re
from typing import List, Optional
import io
import fitz  # PyMuPDF
from datetime import timedelta
from fastapi import Depends

from auth import (
    UserCreate, UserLogin, Token, authenticate_user, create_access_token,
    create_user, get_user_by_email, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)

app = FastAPI(title="Law Agent API")

# In-memory storage for uploaded documents (cleared on server restart)
case_documents = {
    "documents": [],
    "document_content": "",
    "upload_timestamp": None
}

# In-memory storage for chat sessions
chat_sessions = {}

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    message: str
    sender: str = "user"
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    response: str
    timestamp: float
    session_id: str

def clean_extracted_text(text: str) -> str:
    """
    Clean and format extracted text for better AI parsing.
    """
    # Remove excessive whitespace and normalize line breaks
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Reduce multiple empty lines to max 2
    text = re.sub(r' +', ' ', text)  # Multiple spaces to single space
    text = re.sub(r'\t+', ' ', text)  # Tabs to single space

    # Remove page numbers and headers/footers (common patterns)
    text = re.sub(r'^\s*Page\s+\d+.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)  # Standalone page numbers

    # Clean up common PDF artifacts
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between camelCase words
    text = re.sub(r'(\.)([A-Z])', r'\1 \2', text)  # Add space after period before capital

    # Normalize quotes and dashes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    text = text.replace('–', '-').replace('—', '-')

    return text.strip()

def extract_text_from_pdf(file_content: bytes, filename: str) -> str:
    """
    Extract text from PDF using PyMuPDF with smart formatting.
    """
    try:
        # Open PDF from bytes
        pdf_doc = fitz.open(stream=file_content, filetype="pdf")

        extracted_text = []
        total_pages = pdf_doc.page_count

        print(f"📖 Extracting text from PDF: {filename} ({total_pages} pages)")

        for page_num in range(total_pages):
            page = pdf_doc.load_page(page_num)

            # Extract text with layout preservation
            text = page.get_text("text")

            if text.strip():  # Only add non-empty pages
                # Add page separator for multi-page documents
                if page_num > 0:
                    extracted_text.append(f"\n--- Page {page_num + 1} ---\n")
                else:
                    extracted_text.append(f"--- Page {page_num + 1} ---\n")

                extracted_text.append(text)

        pdf_doc.close()

        if not extracted_text:
            return f"[PDF Document: {filename} - No extractable text found]"

        full_text = "".join(extracted_text)
        cleaned_text = clean_extracted_text(full_text)

        print(f"✅ Successfully extracted {len(cleaned_text)} characters from {filename}")
        return cleaned_text

    except Exception as e:
        print(f"❌ Error extracting text from PDF {filename}: {str(e)}")
        return f"[Error extracting text from PDF {filename}: {str(e)}]"

def extract_text_from_file(file_content: bytes, filename: str, content_type: str) -> str:
    """
    Extract text content from uploaded files with smart parsing.
    """
    try:
        if content_type == "text/plain" or filename.endswith('.txt'):
            text = file_content.decode('utf-8')
            return clean_extracted_text(text)

        elif filename.endswith('.pdf') or content_type == 'application/pdf':
            return extract_text_from_pdf(file_content, filename)

        elif filename.endswith(('.doc', '.docx')):
            # For Word documents, return a placeholder for now
            return f"[Word Document: {filename} - Content would be extracted with DOC parser]"

        else:
            # Try to decode as text anyway
            try:
                text = file_content.decode('utf-8')
                return clean_extracted_text(text)
            except:
                return f"[Binary file: {filename} - Content extraction not supported]"

    except Exception as e:
        return f"[Error extracting text from {filename}: {str(e)}]"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/register", response_model=Token)
async def register(user: UserCreate):
    existing_user = get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    db_user = create_user(user)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user={
            "email": db_user["email"],
            "full_name": db_user["full_name"],
            "id": db_user["_id"]
        }
    )

@app.post("/auth/login", response_model=Token)
async def login(user: UserLogin):
    db_user = authenticate_user(user.email, user.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user={
            "email": db_user["email"],
            "full_name": db_user["full_name"],
            "id": str(db_user["_id"])
        }
    )

@app.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "id": str(current_user["_id"])
    }

@app.get("/health/ollama")
def ollama_health():
    """
    Check if Ollama is running and phi4-mini model is available.
    """
    try:
        # Test Ollama connection
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()

        models = response.json()
        phi4_models = [model for model in models.get("models", []) if "phi4-mini" in model.get("name", "")]

        return {
            "ollama_status": "connected",
            "phi4_mini_available": len(phi4_models) > 0,
            "available_models": [model.get("name") for model in phi4_models]
        }
    except Exception as e:
        return {
            "ollama_status": "disconnected",
            "error": str(e),
            "phi4_mini_available": False
        }

def get_fallback_response(user_message: str) -> str:
    """
    Provide fallback responses for common legal questions.
    """
    user_message = user_message.lower()

    if "contract" in user_message:
        return "A valid contract requires four essential elements: offer, acceptance, consideration, and mutual consent. Each party must have the legal capacity to enter into the agreement, and the contract's purpose must be legal."
    elif "lawsuit" in user_message or "sue" in user_message:
        return "To file a lawsuit, you typically need to establish: 1) Legal standing, 2) A valid cause of action, 3) Proper jurisdiction, and 4) Sufficient evidence. I recommend consulting with a qualified attorney for your specific situation."
    elif "copyright" in user_message:
        return "Copyright protection automatically applies to original works of authorship fixed in a tangible medium. This includes literary, dramatic, musical, and artistic works. Protection generally lasts for the author's lifetime plus 70 years."
    elif "trademark" in user_message:
        return "A trademark protects words, phrases, symbols, or designs that identify and distinguish goods or services. To maintain trademark rights, you must use the mark in commerce and can register it with the USPTO for additional protection."
    elif "divorce" in user_message:
        return "Divorce proceedings vary by jurisdiction but typically involve filing a petition, serving papers to your spouse, and addressing issues like asset division, child custody, and support. Consider consulting with a family law attorney for guidance specific to your situation."
    elif "criminal" in user_message:
        return "If you're facing criminal charges, you have the right to an attorney, the right to remain silent, and the right to a fair trial. It's crucial to contact a criminal defense attorney immediately to protect your rights."
    else:
        return "I understand your legal question. As your legal assistant, I can help you with various legal matters including contracts, intellectual property, litigation, and more. Could you provide more specific details about your legal concern?"

def clean_ollama_response(response: str) -> str:
    """
    Clean the Ollama response by removing thinking tags.
    """
    # Remove common thinking patterns
    cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'<reasoning>.*?</reasoning>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)

    # Clean up whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned.strip())

    return cleaned

def query_ollama(prompt: str, model: str = "phi4-mini", system_prompt: str = "", conversation_history: List[dict] = None) -> str:
    """
    Query Ollama with the given prompt and conversation history.
    Maintains context for natural conversation flow.
    """
    try:
        url = "http://localhost:11434/api/generate"
        
        # Build conversation context from history
        context_prompt = prompt
        if conversation_history and len(conversation_history) > 0:
            # Include last 6 messages (3 exchanges) for context
            recent_history = conversation_history[-6:]
            history_text = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in recent_history
            ])
            context_prompt = f"Previous conversation:\n{history_text}\n\nCurrent user message: {prompt}\n\nProvide a direct response to the current message:"
        
        payload = {
            "model": model,
            "prompt": context_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 500,
                "num_ctx": 4096,
                "stop": ["User:", "Client:", "\n\nUser:", "\n\nClient:"],
                "repeat_penalty": 1.2,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()
        print(f"🔍 Ollama response length: {len(result.get('response', ''))}")

        if not result.get("done", False):
            return None

        ai_response = result.get("response", "").strip()
        cleaned_response = clean_ollama_response(ai_response)

        if cleaned_response and len(cleaned_response) > 10:
            return cleaned_response
        else:
            print(f"⚠️ Empty or invalid response from Ollama")
            return None

    except requests.exceptions.ConnectionError:
        print("🔴 Connection error with Ollama")
        return None
    except requests.exceptions.Timeout:
        print("🔴 Timeout error with Ollama")
        return None
    except Exception as e:
        print(f"🔴 Error querying Ollama: {e}")
        return None

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(message: ChatMessage):
    """
    Process chat messages with session-based history tracking.
    Each session maintains its own chat history.
    """
    session_id = message.session_id or "default"
    print(f"🔵 Received chat request (session: {session_id}): {message.message}")

    # Initialize session if it doesn't exist
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "messages": [],
            "created_at": time.time()
        }

    USE_OLLAMA = True

    if USE_OLLAMA:
        # Check if we have case documents to reference
        document_context = ""
        if case_documents["document_content"] and case_documents["upload_timestamp"]:
            doc_names = [doc["filename"] for doc in case_documents["documents"]]
            document_context = f"""
UPLOADED CASE DOCUMENTS FOR REVIEW:
{', '.join(f'"{name}"' for name in doc_names)}

DOCUMENT CONTENTS:
{case_documents["document_content"]}

CRITICAL INSTRUCTION: You have full access to the above case documents. Analyze them thoroughly and reference specific sections, clauses, terms, dates, parties, and provisions when providing your legal counsel. Quote directly from the documents when relevant to support your analysis.
"""

        # Build system prompt - professional but conversational
        system_prompt = """You are a professional legal assistant at a law firm. Provide clear, helpful, and accurate legal guidance. Be conversational and approachable while maintaining professionalism. Keep responses concise but complete - typically 2-4 sentences unless more detail is needed. Never mention that you're an AI from Microsoft or other companies."""

        # Build user prompt with document context if available
        if document_context:
            user_prompt = f"""{document_context}

User question: {message.message}"""
            print(f"🔍 Using {len(case_documents['documents'])} uploaded document(s) for context")
        else:
            user_prompt = message.message
        
        print("🟡 Attempting to query Ollama...")
        
        # Pass conversation history for context (only previous messages, not current)
        ai_response = query_ollama(
            user_prompt, 
            system_prompt=system_prompt,
            conversation_history=chat_sessions[session_id]["messages"]
        )
        
        # Add user message to history AFTER getting response
        chat_sessions[session_id]["messages"].append({
            "role": "user",
            "content": message.message,
            "timestamp": time.time()
        })

        # If Ollama fails or returns None, use fallback
        if not ai_response:
            print("🔴 Using fallback response")
            fallback_response = get_fallback_response(message.message)
            # Add user message if not already added
            if not chat_sessions[session_id]["messages"] or chat_sessions[session_id]["messages"][-1]["role"] != "user":
                chat_sessions[session_id]["messages"].append({
                    "role": "user",
                    "content": message.message,
                    "timestamp": time.time()
                })
            chat_sessions[session_id]["messages"].append({
                "role": "assistant",
                "content": fallback_response,
                "timestamp": time.time()
            })
            return ChatResponse(response=fallback_response, timestamp=time.time(), session_id=session_id)
        
        print(f"🟢 Ollama response: {ai_response[:100]}...")

        # Add AI response to session history
        chat_sessions[session_id]["messages"].append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": time.time()
        })

        print("✅ Returning Ollama response")
        return ChatResponse(response=ai_response, timestamp=time.time(), session_id=session_id)
    else:
        # Use fast fallback response
        print("⚡ Using fast fallback response")
        fallback_response = get_fallback_response(message.message)
        # Add user message
        chat_sessions[session_id]["messages"].append({
            "role": "user",
            "content": message.message,
            "timestamp": time.time()
        })
        chat_sessions[session_id]["messages"].append({
            "role": "assistant",
            "content": fallback_response,
            "timestamp": time.time()
        })
        return ChatResponse(response=fallback_response, timestamp=time.time(), session_id=session_id)

@app.post("/upload-documents")
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Handle document upload for case analysis and store in memory for AI context.
    """
    try:
        global case_documents

        uploaded_documents = []
        document_texts = []

        for file in files:
            # Read file content
            content = await file.read()

            # Extract text content
            text_content = extract_text_from_file(content, file.filename, file.content_type)
            document_texts.append(f"\n--- Document: {file.filename} ---\n{text_content}")

            # Collect file info
            doc_info = {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(content)
            }
            uploaded_documents.append(doc_info)

            # Log the document details
            print(f"📄 Received document: {file.filename}")
            print(f"   Content Type: {file.content_type}")
            print(f"   Size: {len(content)} bytes")

        # Store documents in memory for AI context
        case_documents["documents"] = uploaded_documents
        case_documents["document_content"] = "\n".join(document_texts)
        case_documents["upload_timestamp"] = time.time()

        print(f"🔍 Total documents received: {len(uploaded_documents)}")
        print("📋 Documents stored in memory for AI context")
        print(f"📝 Combined document content length: {len(case_documents['document_content'])} characters")

        return {
            "message": f"Successfully received and processed {len(uploaded_documents)} document(s)",
            "documents": uploaded_documents,
            "timestamp": time.time()
        }

    except Exception as e:
        print(f"❌ Error processing document upload: {e}")
        return {
            "error": "Failed to process uploaded documents",
            "message": str(e),
            "timestamp": time.time()
        }

@app.post("/clear-documents")
def clear_documents():
    """
    Clear all stored case documents from memory.
    """
    global case_documents

    documents_cleared = len(case_documents["documents"])
    case_documents = {
        "documents": [],
        "document_content": "",
        "upload_timestamp": None
    }

    print(f"🗑️ Cleared {documents_cleared} document(s) from memory")

    return {
        "message": f"Cleared {documents_cleared} document(s) from case context",
        "timestamp": time.time()
    }

@app.post("/chat/reset")
def reset_chat(session_id: Optional[str] = "default"):
    """
    Reset chat history for a specific session or all sessions.
    Call this endpoint when frontend reloads to start fresh conversation.
    """
    global chat_sessions

    if session_id == "all":
        # Clear all sessions
        sessions_cleared = len(chat_sessions)
        chat_sessions = {}
        print(f"🔄 Cleared all {sessions_cleared} chat session(s)")
        return {
            "message": f"Cleared all {sessions_cleared} chat session(s)",
            "timestamp": time.time()
        }
    else:
        # Clear specific session
        if session_id in chat_sessions:
            messages_cleared = len(chat_sessions[session_id]["messages"])
            del chat_sessions[session_id]
            print(f"🔄 Cleared chat session '{session_id}' with {messages_cleared} message(s)")
            return {
                "message": f"Cleared chat session '{session_id}' with {messages_cleared} message(s)",
                "session_id": session_id,
                "timestamp": time.time()
            }
        else:
            return {
                "message": f"Chat session '{session_id}' not found or already cleared",
                "session_id": session_id,
                "timestamp": time.time()
            }

@app.get("/chat/history/{session_id}")
def get_chat_history(session_id: str = "default"):
    """
    Get chat history for a specific session.
    """
    if session_id in chat_sessions:
        return {
            "session_id": session_id,
            "messages": chat_sessions[session_id]["messages"],
            "created_at": chat_sessions[session_id]["created_at"],
            "message_count": len(chat_sessions[session_id]["messages"])
        }
    else:
        return {
            "session_id": session_id,
            "messages": [],
            "message_count": 0,
            "error": "Session not found"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
