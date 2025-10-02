# Authentication System Setup

## Overview
This project now includes a complete JWT-based authentication system with:
- Beautiful login/register page with shadcn UI components
- MongoDB for user storage
- JWT tokens for secure authentication
- Protected routes on the frontend
- User session management

## Features Implemented

### Backend (FastAPI)
- **Location**: `apps/api/auth.py` and `apps/api/main.py`
- **Endpoints**:
  - `POST /auth/register` - Register new user
  - `POST /auth/login` - Login and get JWT token
  - `GET /auth/me` - Get current user info (protected)
  
- **Security**:
  - Password hashing with bcrypt
  - JWT tokens with 7-day expiration
  - HTTP Bearer authentication

### Frontend (Next.js)
- **Location**: `apps/web/app/login/page.tsx`
- **Features**:
  - Beautiful gradient UI with glassmorphism effects
  - Tabbed interface for login/register
  - Real-time form validation
  - Error handling and loading states
  - Responsive design

- **Authentication Context**: `apps/web/lib/auth.tsx`
  - Global state management for auth
  - Token persistence in localStorage
  - Auto-login on page refresh

- **Protected Routes**: `apps/web/components/protected-route.tsx`
  - Redirect to login if not authenticated
  - Loading states
  - Automatic route protection

## Environment Variables

Create a `.env` file in `apps/api/`:

```env
# Optional: Customize these values
JWT_SECRET_KEY=your-super-secret-key-change-in-production
MONGODB_URI=mongodb://localhost:27017/
```

## Database Schema

### User Collection
```json
{
  "email": "user@example.com",
  "hashed_password": "bcrypt_hashed_password",
  "full_name": "John Doe",
  "created_at": "2025-01-01T00:00:00",
  "is_active": true
}
```

## Running the Application

### Prerequisites
- MongoDB running on localhost:27017
- Python 3.13+ with virtual environment
- Node.js 18+ with pnpm

### Start Backend
```bash
cd apps/api
.venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend
```bash
cd apps/web
pnpm dev
```

### Access the Application
1. Open http://localhost:3000 - Beautiful landing page
2. Click "Get Started" to go to http://localhost:3000/login
3. Register a new account or login
4. After login, access the chat platform at http://localhost:3000/chat

## User Flow

1. **Landing Page**: User sees beautiful home page at `/`
2. **Get Started**: User clicks "Get Started" → redirected to `/login`
3. **Register**: User creates account with email, password, and name
4. **Login**: User logs in with email and password
5. **JWT Token**: Server generates JWT token and sends it to client
6. **Token Storage**: Client stores token in localStorage
7. **Chat Platform**: User accesses `/chat` for AI legal assistant
8. **Protected Access**: Chat route is protected, requires authentication
9. **Logout**: Token is removed from storage

## UI Components Used

- **shadcn/ui components**:
  - Button
  - Input
  - Label
  - Card
  - Tabs
  - Avatar
  - Badge
  
- **Icons**: Lucide React
  - Scale (logo)
  - Mail, Lock, User (form icons)
  - Sparkles (decoration)
  - LogOut (logout button)

## Security Best Practices

✅ Passwords are hashed with bcrypt
✅ JWT tokens have expiration
✅ Tokens stored in localStorage (consider httpOnly cookies for production)
✅ Protected routes redirect to login
✅ MongoDB connection with optional authentication
✅ CORS configured for localhost development

## Future Enhancements

- [ ] Email verification
- [ ] Password reset functionality
- [ ] OAuth integration (Google, GitHub)
- [ ] Refresh token mechanism
- [ ] httpOnly cookie storage for tokens
- [ ] Rate limiting on auth endpoints
- [ ] 2FA support
- [ ] User profile management

## Troubleshooting

### MongoDB Connection Error
```bash
# Start MongoDB
brew services start mongodb-community
# OR
mongod --dbpath /path/to/data
```

### Token Expired
- Tokens expire after 7 days
- User will be automatically logged out
- Simply login again

### Build Errors
```bash
# Clean build
rm -rf apps/web/.next
cd apps/web && pnpm run build
```

## API Testing

### Register User
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

### Get Current User
```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## File Structure

```
apps/
├── api/
│   ├── auth.py              # Authentication logic
│   ├── main.py              # FastAPI app with auth endpoints
│   └── .venv/               # Python virtual environment
│
└── web/
    ├── app/
    │   ├── page.tsx         # Public landing page
    │   ├── login/
    │   │   └── page.tsx     # Login/Register page (minimal design)
    │   ├── chat/
    │   │   └── page.tsx     # Protected chat/AI assistant page
    │   └── layout.tsx       # Root layout with AuthProvider
    ├── lib/
    │   └── auth.tsx         # Auth context and hooks
    └── components/
        ├── protected-route.tsx  # Route protection
        └── ui/                  # shadcn components
```

## Notes

- Default JWT token expires in 7 days
- MongoDB uses the `legal_law_firm` database
- Email must be unique (enforced by MongoDB index)
- All auth routes are prefixed with `/auth`
- User info displayed in header after login
