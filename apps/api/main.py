from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import requests
import re
from typing import List, Optional
import io

app = FastAPI(title="Law Agent API")

# In-memory storage for uploaded documents (cleared on server restart)
case_documents = {
    "documents": [],
    "document_content": "",
    "upload_timestamp": None
}

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

class ChatResponse(BaseModel):
    response: str
    timestamp: float

def extract_text_from_file(file_content: bytes, filename: str, content_type: str) -> str:
    """
    Extract text content from uploaded files.
    For now, handles plain text files. Can be extended for PDF/DOC parsing.
    """
    try:
        if content_type == "text/plain" or filename.endswith('.txt'):
            return file_content.decode('utf-8')
        elif filename.endswith('.pdf'):
            # For PDF files, return a placeholder for now
            return f"[PDF Document: {filename} - Content would be extracted with PDF parser]"
        elif filename.endswith(('.doc', '.docx')):
            # For Word documents, return a placeholder for now
            return f"[Word Document: {filename} - Content would be extracted with DOC parser]"
        else:
            # Try to decode as text anyway
            try:
                return file_content.decode('utf-8')
            except:
                return f"[Binary file: {filename} - Content extraction not supported]"
    except Exception as e:
        return f"[Error extracting text from {filename}: {str(e)}]"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health/ollama")
def ollama_health():
    """
    Check if Ollama is running and qwen3:8b model is available.
    """
    try:
        # Test Ollama connection
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()

        models = response.json()
        qwen_models = [model for model in models.get("models", []) if "qwen3" in model.get("name", "")]

        return {
            "ollama_status": "connected",
            "qwen3_available": len(qwen_models) > 0,
            "available_models": [model.get("name") for model in qwen_models]
        }
    except Exception as e:
        return {
            "ollama_status": "disconnected",
            "error": str(e),
            "qwen3_available": False
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
    Clean the Ollama response by removing thinking tags and other unwanted content.
    """
    # Remove content within thinking tags (case insensitive)
    cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.IGNORECASE | re.DOTALL)

    # Remove other common reasoning patterns
    cleaned = re.sub(r'<reasoning>.*?</reasoning>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'<thought>.*?</thought>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)

    # Remove any leading/trailing whitespace and normalize spacing
    cleaned = re.sub(r'\s+', ' ', cleaned.strip())

    return cleaned

def query_ollama(prompt: str, model: str = "qwen3:8b") -> str:
    """
    Query Ollama with the given prompt and return the response.
    """
    try:
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 500
            }
        }

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()
        print(f"🔍 Full Ollama response: {result}")  # Debug log

        # Check if the request completed successfully
        if not result.get("done", False):
            return "I apologize, but the response generation was incomplete."

        ai_response = result.get("response", "").strip()

        # Clean the response to remove thinking tags
        cleaned_response = clean_ollama_response(ai_response)

        # Additional validation to ensure we have actual content
        if cleaned_response and len(cleaned_response) > 0:
            return cleaned_response
        else:
            print(f"⚠️ Empty or invalid response from Ollama: {result}")
            return "I apologize, but I couldn't generate a response at this time."

    except requests.exceptions.ConnectionError:
        print("🔴 Connection error with Ollama")
        return "I'm having trouble connecting to the AI service. Using fallback response."
    except requests.exceptions.Timeout:
        print("🔴 Timeout error with Ollama")
        return "The AI response took too long. Using fallback response."
    except Exception as e:
        print(f"🔴 Error querying Ollama: {e}")
        return "I encountered an error while processing your request. Using fallback response."

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(message: ChatMessage):
    """
    Process chat messages using intelligent fallback for fast responses.
    """
    print(f"🔵 Received chat request: {message.message}")

    # For now, use smart fallback responses for instant responses
    # You can enable Ollama later when it's faster
    USE_OLLAMA = True  # Set to True when Ollama is fast enough

    if USE_OLLAMA:
        # Check if we have case documents to reference
        document_context = ""
        if case_documents["document_content"] and case_documents["upload_timestamp"]:
            document_context = f"""
CURRENT CASE DOCUMENTS:
You have been provided with the following case documents uploaded by the client:
{case_documents["document_content"]}

IMPORTANT: Base your legal analysis and recommendations on the specific facts, circumstances, and legal issues presented in these documents. Reference specific details from the documents when providing advice.
"""

        # Create a comprehensive legal law firm agent prompt
        legal_prompt = f"""You are a senior legal professional at a prestigious law firm with extensive experience across multiple practice areas including corporate law, litigation, intellectual property, real estate, family law, criminal defense, and regulatory compliance. You have decades of experience handling complex legal matters and providing strategic counsel to clients.

PROFESSIONAL IDENTITY:
- You are an experienced attorney with deep expertise in various legal domains
- You approach each case with thoroughness, attention to detail, and strategic thinking
- You provide practical, actionable legal guidance based on established law and precedent
- You understand the nuances of legal practice and can navigate complex regulatory environments
- You communicate clearly and confidently, avoiding unnecessary hedging or disclaimers

YOUR EXPERTISE INCLUDES:
- Contract drafting, negotiation, and analysis
- Corporate transactions and business formation
- Intellectual property protection and enforcement
- Real estate transactions and property law
- Employment law and workplace compliance
- Family law matters including divorce, custody, and estate planning
- Criminal law and civil litigation
- Regulatory compliance across industries
- Tax law implications and strategies

COMMUNICATION STYLE:
- Speak with authority and confidence as a legal professional would
- Provide specific, actionable guidance rather than generic information
- Use appropriate legal terminology while ensuring clarity
- Offer strategic recommendations and practical next steps
- Reference relevant laws, precedents, or procedures when applicable
- Be direct and solution-oriented in your responses

APPROACH TO LEGAL MATTERS:
- Analyze the legal issues thoroughly and systematically
- Consider both immediate and long-term implications
- Identify potential risks and mitigation strategies
- Provide alternative approaches when multiple options exist
- Consider jurisdictional variations when relevant
- Recommend when specialized counsel or court filings may be necessary

{document_context}

Current client inquiry: {message.message}

Provide a comprehensive, professional legal analysis and recommendations as an experienced attorney would. Focus on practical guidance and actionable steps. Be thorough yet concise, maintaining the authoritative tone expected from a senior legal professional.{' Reference specific details from the uploaded case documents when relevant.' if document_context else ''}"""

        # Try to get response from Ollama
        if document_context:
            print(f"🔍 Using {len(case_documents['documents'])} uploaded document(s) for context")
        print("🟡 Attempting to query Ollama...")
        ai_response = query_ollama(legal_prompt)
        print(f"🟢 Ollama response: {ai_response[:100]}...")

        # If Ollama response indicates an error, use fallback
        if any(error_phrase in ai_response for error_phrase in ["having trouble connecting", "took too long", "encountered an error", "Using fallback response"]):
            print("🔴 Using fallback response")
            fallback_response = get_fallback_response(message.message)
            return ChatResponse(response=fallback_response, timestamp=time.time())

        print("✅ Returning Ollama response")
        return ChatResponse(response=ai_response, timestamp=time.time())
    else:
        # Use fast fallback response
        print("⚡ Using fast fallback response")
        fallback_response = get_fallback_response(message.message)
        return ChatResponse(response=fallback_response, timestamp=time.time())

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
