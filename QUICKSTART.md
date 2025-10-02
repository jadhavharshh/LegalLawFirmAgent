# Legal Law Firm Agent - Quick Start Guide

## 🚀 Running the Application

### Start Everything at Once
```bash
pnpm run dev
```

This will start:
- **Web App** on http://localhost:3000 (Main dashboard with sidebar)
- **Docs** on http://localhost:3001
- **API** on http://localhost:8000

### Individual Services

#### Web App Only
```bash
cd apps/web
pnpm run dev
```

#### API Only
```bash
cd apps/api
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 Issues Fixed

### 1. ✅ bcrypt Version Issue
**Problem**: bcrypt 5.0.0 has breaking changes with passlib
**Solution**: Downgraded to bcrypt 4.3.0
```bash
cd apps/api
python3 -m pip install "bcrypt>=4.0.0,<5.0.0"
```

### 2. ✅ email-validator Missing
**Problem**: Pydantic email validation requires email-validator package
**Solution**: Installed email-validator
```bash
cd apps/api
python3 -m pip install email-validator
```

### 3. ✅ Sidebar Dashboard Implementation
**Problem**: Landing page needed to be replaced with dashboard
**Solution**: 
- Converted landing page to full dashboard with sidebar
- Customized for Legal Law Firm branding
- Integrated all shadcn dashboard components
- Data table showing 68 legal documents

## 📦 Application Structure

```
LegalLawFirmAgent/
├── apps/
│   ├── web/          # Next.js frontend (port 3000) - Dashboard with sidebar
│   ├── docs/         # Documentation (port 3001)
│   └── api/          # FastAPI backend (port 8000)
├── packages/
│   ├── ui/           # Shared UI components
│   └── typescript-config/
└── pnpm-workspace.yaml
```

## 🎨 Dashboard Features

### Sidebar Navigation
- **Dashboard** - Main overview
- **Documents** - Document management
- **Analytics** - Usage analytics
- **Cases** - Case management
- **Team** - Team collaboration

### Document Section
- Document Library
- Case Reports
- Legal Templates
- Compliance Docs

### Data Table
- 68 legal documents with full CRUD
- Drag & drop reordering
- Status tracking (Done/In Process)
- Reviewer assignment
- Type categorization (Narrative, Technical, Legal, etc.)

## 🔑 API Endpoints

- `POST /auth/register` - User registration
- `POST /auth/token` - Login/Get JWT
- `POST /chat` - Chat with AI
- `POST /upload` - Upload documents
- `GET /documents` - List documents
- `POST /documents/{doc_id}/analyze` - Analyze document

## 🐛 Troubleshooting

### API Won't Start
```bash
cd apps/api
python3 -m pip install -r requirements.txt
```

### Web App Won't Start
```bash
cd apps/web
pnpm install
rm -rf .next
pnpm run dev
```

### Port Already in Use
Kill existing processes:
```bash
# Kill web app
lsof -ti:3000 | xargs kill -9

# Kill API
lsof -ti:8000 | xargs kill -9
```

## 📝 Environment Variables

### Web App (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### API (.env)
```env
MONGODB_URL=your_mongodb_connection_string
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 🎯 Next Steps

1. Configure MongoDB connection
2. Set up environment variables
3. Test user registration and login
4. Upload test legal documents
5. Try the AI chat feature

## 📚 Tech Stack

- **Frontend**: Next.js 15, React 19, TailwindCSS, shadcn/ui
- **Backend**: FastAPI, Python 3.13
- **Database**: MongoDB
- **AI**: Ollama (local LLM)
- **Monorepo**: Turborepo + pnpm

---

**Created**: October 2024
**Last Updated**: $(date)
