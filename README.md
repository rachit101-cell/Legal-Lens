# LegalLens

**AI Legal Document Risk & Action Navigator**

> Deterministic where possible, AI where useful, evidence always, uncertainty when necessary, and security by design.

LegalLens converts uploaded legal documents into structured **Legal Situation Maps** containing document facts, parties, obligations, dates, attention items, missing information, preparation tasks, and questions for a legal professional. It is an information tool, not an AI lawyer.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+ with pgvector (via Docker)

### Setup

```bash
# 1. Clone and enter the project
cd legallens

# 2. Copy environment template
cp .env.example .env

# 3. Start infrastructure
docker compose up -d postgres minio redis

# 4. Install API dependencies
cd apps/api
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 5. Run database migrations
alembic upgrade head

# 6. Start the API server
uvicorn app.main:app --reload --port 8000

# 7. In a new terminal, install and start the web app
cd apps/web
npm install
npm run dev
```

### Verify

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Web app
open http://localhost:3000
```

## Project Structure

```
legallens/
├── apps/
│   ├── api/          # FastAPI backend
│   └── web/          # Next.js frontend
├── packages/
│   ├── schemas/      # Shared Pydantic & TypeScript types
│   └── prompts/      # Versioned prompt templates
├── data/
│   ├── sample-documents/
│   └── evaluation/
├── tests/
├── docs/             # Architecture & design docs
├── alembic/          # Database migrations
└── docker/           # Dockerfiles
```

## Documentation

- [Product Requirements (PRD)](docs/PRD.md)
- [System Architecture](docs/ARCHITECTURE.md)
- [Technical Design](docs/DESIGN.md)
- [Implementation Plan](docs/IMPLEMENTATION.md)
- [UI/UX Specification](docs/UI_UX.md)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, TypeScript, React |
| Backend | FastAPI, Python 3.11 |
| Database | PostgreSQL + pgvector |
| Storage | S3-compatible (MinIO for dev) |
| LLM | Hosted structured-output model |
| Testing | Pytest, Vitest, Playwright, axe |

## License

Private — Hackathon Project
