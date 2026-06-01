# Setup Guide

## Prerequisites

- Docker and Docker Compose
- (Optional) Python 3.12+ for local backend development
- (Optional) Node.js 20+ for local frontend development

## Quick Start

1. Copy environment files:

   ```bash
   cp .env.example .env
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env.local
   ```

2. Start the stack:

   ```bash
   docker compose up --build
   ```

3. Open the app:

   - Frontend: http://localhost:3000
   - Backend health: http://localhost:8000/health

## Local Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Next Steps

Future prompts will add:

- Kubernetes investigation layer
- AI reasoning via OpenRouter
- Investigation orchestration
- Diagnosis UI
