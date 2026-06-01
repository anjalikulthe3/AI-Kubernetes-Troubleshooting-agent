# AI Kubernetes Troubleshooting Agent

An on-demand Kubernetes troubleshooting system powered by AI reasoning.

## Architecture

```
Frontend (Next.js)
    ↓
FastAPI Backend (Orchestrator)
    ↓
Kubernetes Investigation Layer
    ↓
AI Kubernetes Agent
    ↓
LLM Reasoning (OpenRouter via InsForge)
    ↓
Root Cause + Suggested Fix
    ↓
Frontend Diagnosis
```

## Tech Stack

| Layer | Tools |
| --- | --- |
| Backend | FastAPI, Python 3.12+, Uvicorn, Pydantic, Loguru, HTTPX |
| Frontend | Next.js, TypeScript, Tailwind CSS, Axios, React Query |
| Infrastructure | Docker, Docker Compose |

## Project Structure

```
ai-kubernetes-agent/
├── backend/
│   ├── api/
│   ├── core/
│   ├── kubernetes/
│   ├── ai/
│   ├── services/
│   ├── models/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   ├── components/
│   ├── services/
│   ├── hooks/
│   ├── types/
│   ├── package.json
│   └── Dockerfile
├── docs/
├── prompts/
├── docker-compose.yml
└── README.md
```

## Quick Start

1. Copy environment files:

   ```bash
   cp .env.example .env
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env.local
   ```

2. Build and run:

   ```bash
   docker compose up --build
   ```

3. Access:

   - Frontend: http://localhost:3000
   - Backend health: http://localhost:8000/health

See [docs/setup-guide.md](docs/setup-guide.md) for local development instructions.

## Environment Variables

### Backend

```env
OPENROUTER_API_KEY=
OPENROUTER_MODEL=
KUBECONFIG_PATH=
```

### Frontend

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## API Endpoints

### Health Check

```
GET /health
```

Response:

```json
{
  "status": "healthy",
  "service": "ai-kubernetes-agent"
}
```

## Development Status

Foundation setup complete. Planned next:

- Kubernetes cluster inspection
- AI-powered diagnosis
- OpenRouter integration
- Investigation orchestration
- Diagnosis UI
