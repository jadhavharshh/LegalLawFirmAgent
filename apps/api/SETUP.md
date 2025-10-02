# API Setup Guide

## Prerequisites
- Python 3.9 or higher
- MongoDB running on localhost:27017 (or custom URI)

## Installation

### 1. Create Virtual Environment
```bash
cd apps/api
python3 -m venv .venv
```

### 2. Activate Virtual Environment

**macOS/Linux:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

Or install individual packages:
```bash
pip install fastapi uvicorn pydantic python-multipart
pip install python-jose[cryptography] passlib[bcrypt]
pip install pymongo dnspython requests PyMuPDF
```

## Environment Variables (Optional)

Create a `.env` file in `apps/api/`:

```env
JWT_SECRET_KEY=your-super-secret-key-change-in-production
MONGODB_URI=mongodb://localhost:27017/
```

## Running the API

### Development Mode (with auto-reload)
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or using the venv directly:
```bash
.venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
python main.py
```

## API Endpoints

### Health Check
- `GET /health` - Basic health check
- `GET /health/ollama` - Check Ollama connection

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info (requires auth)

### Chat
- `POST /chat` - Send message to AI assistant

### Documents
- `POST /upload-documents` - Upload case documents
- `POST /clear-documents` - Clear uploaded documents

## Testing

### Register a User
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

### Chat (requires JWT token)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "message": "What is a contract?",
    "sender": "user"
  }'
```

## Troubleshooting

### MongoDB Connection Error
Make sure MongoDB is running:
```bash
# macOS
brew services start mongodb-community

# Linux
sudo systemctl start mongod

# Or run manually
mongod --dbpath /path/to/data
```

### Port Already in Use
If port 8000 is already in use, change the port:
```bash
uvicorn main:app --reload --port 8001
```

### Import Errors
Make sure you're using the virtual environment:
```bash
which python  # Should point to .venv/bin/python
```

If not, activate it:
```bash
source .venv/bin/activate
```

## Dependencies Explained

| Package | Purpose |
|---------|---------|
| `fastapi` | Modern web framework |
| `uvicorn` | ASGI server |
| `pydantic` | Data validation |
| `python-jose` | JWT token creation/validation |
| `passlib` | Password hashing |
| `bcrypt` | Bcrypt algorithm for passlib |
| `pymongo` | MongoDB driver |
| `dnspython` | Required for MongoDB SRV connections |
| `requests` | HTTP client for Ollama |
| `PyMuPDF` | PDF text extraction |
| `python-multipart` | File upload support |

## Security Notes

🔒 **Important:**
- Change `JWT_SECRET_KEY` in production
- Use environment variables for secrets
- Enable MongoDB authentication in production
- Use HTTPS in production
- Configure proper CORS origins

## Database

The API uses MongoDB database: `legal_law_firm`

Collections:
- `users` - User accounts with hashed passwords
