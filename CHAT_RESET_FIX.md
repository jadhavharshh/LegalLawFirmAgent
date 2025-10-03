# Chat History Reset Fix

## Problem
When reloading the frontend page, the chat seemed to "remember" previous conversations and generate responses about mergers and legal cases that weren't mentioned in the current conversation.

## Root Cause Analysis
The issue had **two main causes**:

### 1. **Ollama Context Persistence**
Ollama's `/api/generate` endpoint can maintain conversation context through a `context` array that gets passed between requests. Even though we were trying to reset this, the context was still being generated and potentially reused.

### 2. **Overly Formal Prompt Causing Hallucinations**
The original system prompt was very detailed and formal, instructing the AI to act as a "Senior Partner" with "decades of experience." This formal tone may have triggered the model to generate **boilerplate legal responses** that it learned during training, including sample scenarios about mergers and indemnification clauses.

## Solutions Implemented

### Backend Changes (`apps/api/main.py`)

#### 1. Session-Based Chat History
```python
# Added in-memory storage for chat sessions
chat_sessions = {}
```
- Each chat session now has its own isolated history
- Sessions are identified by `session_id` (default: "default")

#### 2. Stateless Ollama Requests
```python
def query_ollama(prompt: str, model: str = "phi4-mini", system_prompt: str = "") -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_predict": 500,
            "num_ctx": 4096,
            "seed": int(time.time() * 1000000) % 2147483647  # Random seed
        }
    }
    # System prompt added separately, no context field
    if system_prompt:
        payload["system"] = system_prompt
```
- Removed `context` field entirely from requests
- Added random `seed` parameter to ensure true randomness
- Each request is completely independent

#### 3. New Endpoints

**`POST /chat/reset`** - Reset chat history
```python
# Clear specific session
POST /chat/reset
Body: { "session_id": "default" }

# Clear all sessions
POST /chat/reset
Body: { "session_id": "all" }
```

**`GET /chat/history/{session_id}`** - Retrieve chat history for debugging
```python
GET /chat/history/default
```

#### 4. Simplified Prompts
**Old prompt:**
- Very formal "Senior Partner and Lead Legal Counsel"
- Multiple paragraphs of instructions
- May have triggered trained legal response patterns

**New prompt:**
```python
system_prompt = """You are a helpful legal assistant. 

IMPORTANT RULES:
1. This is a brand new conversation - you have NO memory of any previous chats
2. Answer ONLY what is being asked right now
3. If someone says "hey" or "hello", just greet them back warmly and ask how you can help
4. Do NOT invent scenarios, cases, mergers, or legal matters that weren't mentioned
5. Be natural and conversational, not overly formal
6. Keep responses concise and relevant"""
```

### Frontend Changes (`apps/web/app/chat/page.tsx`)

#### 1. Dynamic Session ID Generation
```typescript
// Generate a unique session ID that persists only for this component instance
// This will be new on every page reload, but persist through React re-renders
const [sessionId] = useState(() => 
  `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
);
```

**How it works:**
- Every time you reload the page, a **new session ID** is generated
- The backend stores separate chat history for each session ID
- React re-renders use the same session ID (so chat persists during navigation)
- **No need to explicitly call `/chat/reset`** - new session = fresh chat automatically!

#### 2. Session ID in Requests
```typescript
body: JSON.stringify({
  message: message,
  sender: 'user',
  session_id: sessionId  // Dynamic session ID, not hardcoded
})
```

## Testing Instructions

### 1. Restart the Backend
```bash
cd /Users/harshjadhav/Documents/Code/LegalLawFirmAgent
# Stop any running backend (Ctrl+C)
# Start fresh
python3 apps/api/main.py
# or
uvicorn apps.api.main:app --reload --port 8000
```

### 2. Restart the Frontend
```bash
cd /Users/harshjadhav/Documents/Code/LegalLawFirmAgent
# Stop any running frontend (Ctrl+C)
# Start fresh
cd apps/web
npm run dev
```

### 3. Test the Reset Behavior

**Test 1: Simple Greeting**
1. Open browser to `http://localhost:3000/chat`
2. Type "hey" and send
3. Expected: Should get a simple greeting like "Hello! How can I help you today?" NOT a long response about mergers
4. Reload the page (F5)
5. Type "hey" again
6. Expected: Same simple greeting, no reference to previous conversation

**Test 2: Specific Question**
1. Ask a specific legal question like "What is a contract?"
2. Get response
3. Reload page
4. Ask "What did I just ask you?"
5. Expected: Should say something like "I don't have any record of previous questions" NOT recall the contract question

**Test 3: Check Backend Logs**
Look for these log messages:
```
🔄 Cleared chat session 'default' with X message(s)
📝 User prompt preview: ...
📝 System prompt preview: ...
```

## Debugging

If issues persist:

### 1. Check Ollama is responding correctly
```bash
curl -X POST http://localhost:11434/api/generate \
  -d '{"model": "phi4-mini", "prompt": "Say hello", "stream": false}' \
  | jq .response
```

### 2. Check session reset endpoint
```bash
curl -X POST http://localhost:8000/chat/reset \
  -H "Content-Type: application/json" \
  -d '{"session_id": "default"}'
```

### 3. Check chat history
```bash
curl http://localhost:8000/chat/history/default | jq
```

### 4. Monitor backend logs
Watch the terminal running your FastAPI backend for:
- Session reset messages
- Prompt previews
- Ollama responses

## Expected Behavior After Fix

✅ **Page reload (F5) = Fresh conversation with new session ID**
✅ **Chat history persists during normal usage (typing messages)**
✅ **React re-renders don't reset the chat**
✅ **No memory between page reloads**
✅ **Natural, contextual responses** (not boilerplate legal advice)
✅ **Simple greetings get simple responses**

## How Session Management Works Now

### Before (BROKEN):
- Fixed session ID: `"default"`
- Called `/chat/reset` on component mount
- This caused resets even on React re-renders
- Chat would disappear randomly

### After (FIXED):
- Dynamic session ID: `"session_1234567890_abc123def"`
- New session ID generated on each page load
- Backend automatically isolates conversations by session ID
- No explicit reset needed - new session = new conversation
- React re-renders keep the same session ID

## Additional Notes

- The simplified prompt should also make responses faster and more natural
- If you still see the merger response, it might be:
  1. Browser cache (try hard refresh: Cmd+Shift+R)
  2. Ollama model needs restart: `ollama stop phi4-mini` then `ollama run phi4-mini`
  3. Model itself has that as a common response pattern in its training data

## Rollback Instructions

If you need to revert these changes:
```bash
git diff HEAD apps/api/main.py > /tmp/backend_changes.patch
git diff HEAD apps/web/app/chat/page.tsx > /tmp/frontend_changes.patch

# To revert:
git checkout HEAD -- apps/api/main.py
git checkout HEAD -- apps/web/app/chat/page.tsx
```
