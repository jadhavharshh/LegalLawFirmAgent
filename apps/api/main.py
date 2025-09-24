from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import requests

app = FastAPI(title="Law Agent API")

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
                "max_tokens": 500
            }
        }

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        result = response.json()
        ai_response = result.get("response", "").strip()

        if ai_response:
            return ai_response
        else:
            return "I apologize, but I couldn't generate a response at this time."

    except requests.exceptions.ConnectionError:
        return "I'm having trouble connecting to the AI service. Using fallback response."
    except requests.exceptions.Timeout:
        return "The AI response took too long. Using fallback response."
    except Exception as e:
        print(f"Error querying Ollama: {e}")
        return "I encountered an error while processing your request. Using fallback response."

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(message: ChatMessage):
    """
    Process chat messages using Qwen3:8b model via Ollama with fallback.
    """
    print(f"🔵 Received chat request: {message.message}")

    # Create a legal-focused prompt
    legal_prompt = f"""You are a knowledgeable legal assistant. Please provide accurate, helpful legal information while being clear that you are not providing legal advice and users should consult with qualified attorneys for specific legal matters.

User question: {message.message}

Please provide a comprehensive but concise response:"""

    # Try to get response from Ollama
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
