from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import time

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

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(message: ChatMessage):
    """
    Process chat messages and return legal assistant responses.
    This is a simple implementation - you can enhance this with your AI model.
    """
    user_message = message.message.lower()

    # Simple response logic - replace this with your AI model
    if "contract" in user_message:
        response = "A valid contract requires four essential elements: offer, acceptance, consideration, and mutual consent. Each party must have the legal capacity to enter into the agreement, and the contract's purpose must be legal."
    elif "lawsuit" in user_message:
        response = "To file a lawsuit, you typically need to establish: 1) Legal standing, 2) A valid cause of action, 3) Proper jurisdiction, and 4) Sufficient evidence. I recommend consulting with a qualified attorney for your specific situation."
    elif "copyright" in user_message:
        response = "Copyright protection automatically applies to original works of authorship fixed in a tangible medium. This includes literary, dramatic, musical, and artistic works. Protection generally lasts for the author's lifetime plus 70 years."
    elif "trademark" in user_message:
        response = "A trademark protects words, phrases, symbols, or designs that identify and distinguish goods or services. To maintain trademark rights, you must use the mark in commerce and can register it with the USPTO for additional protection."
    else:
        response = "I understand your legal question. As your legal assistant, I can help you with various legal matters including contracts, intellectual property, litigation, and more. Could you provide more specific details about your legal concern?"

    return ChatResponse(response=response, timestamp=time.time())
