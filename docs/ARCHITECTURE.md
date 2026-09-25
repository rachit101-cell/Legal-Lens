# LegalLens — System Architecture

**Version:** 1.0.0  
**Status:** Implementation-Ready  
**Last Updated:** 2026-09-23

---

## 1. Architecture Overview

LegalLens uses a **modular monolith** architecture — not a collection of networked microservices. Each module has a stable interface and can be extracted later. This improves code quality and efficiency because local calls avoid network overhead and reduce deployment failure modes.

```
                         Browser / Next.js
                   upload, dashboard, viewer, chat
                                  |
                         HTTPS JSON / SSE
                                  |
                         FastAPI modular API
      auth | documents | analysis | chat | citations | health
                                  |
       +--------------------------+--------------------------+
       |                          |                          |
 Document Engine             Analysis Engine            Retrieval Engine
 PyMuPDF, python-docx,       rules, entities,           pgvector chunks,
 OCR fallback, layout        timeline, findings          hybrid retrieval
       |                          |                          |
       +--------------------------+--------------------------+
                                  |
                         AI Orchestration Layer
             structured prompts, model adapter, validators
                                  |
              PostgreSQL + pgvector | S3 object storage
                                  |
                    optional Redis worker queue
```

---

## 2. Technology Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| **Web** | Next.js, TypeScript, React | Strong routing, typed UI, accessible component ecosystem |
| **API** | FastAPI, Python 3.11 | Natural fit for document and NLP libraries with typed HTTP contracts |
| **Database** | PostgreSQL | Relational integrity for evidence and analysis state |
| **Vector Search** | pgvector | One operational database for MVP; easy future adapter swap |
| **PDF** | PyMuPDF | Fast text and coordinate extraction |
| **DOCX** | python-docx | Direct paragraph, heading, and table access |
| **OCR** | Tesseract adapter | Local fallback with provider abstraction |
| **Validation** | Pydantic | Shared typed schemas and runtime validation |
| **ORM/Migrations** | SQLAlchemy + Alembic | Explicit repositories and controlled schema evolution |
| **Queue** | In-process task first, Redis next | Avoid deployment complexity until needed |
| **Storage** | Private S3-compatible (MinIO dev) | Durable originals with TTL and provider portability |
| **LLM** | Hosted structured-output model adapter | Best reasoning-to-effort ratio |
| **Embeddings** | Hosted or local general embedding adapter | Adequate for bounded document retrieval |
| **Testing** | Pytest, Vitest/Playwright, axe | Unit, integration, browser, accessibility |
| **Deployment** | Managed web, API, PostgreSQL, object store | Low operations burden and fast demo recovery |

---

## 3. Request Lifecycle

### 3.1 Upload Flow

```
Client                    API                     Storage          Database
  |                        |                        |                 |
  |-- POST /upload ------->|                        |                 |
  |                        |-- validate file ------>|                 |
  |                        |   (size, mime, magic,  |                 |
  |                        |    pages, sha256)      |                 |
  |                        |-- store quarantine --->|                 |
  |                        |                        |                 |
  |                        |-- create document -----|---------------->|
  |                        |-- create analysis_run -|---------------->|
  |                        |                        |                 |
  |<-- 202 {doc_id, run_id, status: QUEUED} --------|                |
  |                        |                        |                 |
  |                        |== background task ====>|                 |
  |                        |   extraction           |                 |
  |                        |   normalization        |                 |
  |                        |   deterministic intel  |                 |
  |                        |   retrieval indexing   |                 |
  |                        |   LLM generation       |                 |
  |                        |   citation validation  |                 |
  |                        |   persistence          |                 |
```

### 3.2 Q&A Flow

```
Client                    API                Retrieval     AI Engine     Verifier
  |                        |                    |             |             |
  |-- POST /chat --------->|                    |             |             |
  |                        |-- check analysis -->|             |             |
  |                        |-- retrieve chunks ->|             |             |
  |                        |<-- evidence --------|             |             |
  |                        |-- generate ---------|------------>|             |
  |                        |<-- structured resp -|-------------|             |
  |                        |-- verify citations -|-------------|------------>|
  |                        |<-- verified result -|-------------|-------------|
  |                        |-- persist answer ---|             |             |
  |<-- 200 {answer, citations, limitations} -----|             |             |
```

---

## 4. Trust Boundaries

| Boundary | Trust Level | Control |
|----------|------------|---------|
| **Browser** | Untrusted | API validates every request |
| **Uploaded File** | Untrusted data | Processed in restricted worker; never executed |
| **Extracted Text** | Untrusted data | Never treated as instructions |
| **Model Provider** | External processor | Requests minimized; no-retention where available |
| **Database** | Private | Access only through API repositories |
| **Object Store** | Private | Access only through authorized proxy or signed URLs |
| **Logs** | Internal | Contain IDs, stages, hashes, sizes, timings — not document text |

---

## 5. Component Architecture

### 5.1 Web Application (Next.js)

**Responsibilities:**
- Route-level pages with server-side metadata
- Typed API clients
- Accessible UI components
- Document viewer with evidence highlighting
- `DocumentContext` for selected document and analysis status
- React Query / equivalent for cache and invalidation

**Key principle:** Browser receives signed or proxied page assets only after authorization check.

### 5.2 API Layer (FastAPI)

**Responsibilities:**
- Authentication and session management
- Request validation (Pydantic models as boundary contracts)
- Authorization and ownership checks
- Upload streaming and orchestration
- Read models and response formatting
- Q&A orchestration
- Error mapping

**Key principle:** SQLAlchemy/SQLModel used only in repository modules; route handlers do not issue raw SQL. Every request receives a `request_id`; every analysis receives an `analysis_id`.

### 5.3 Document Engine

**Interface:**
```python
class DocumentEngine(Protocol):
    def ingest_file(self, file_path: Path, metadata: UploadMetadata) -> IngestResult: ...
    def extract_pages(self, file_path: Path) -> list[CanonicalPage]: ...
    def extract_layout(self, page: CanonicalPage) -> list[TextBlock]: ...
    def ocr_pages(self, pages: list[CanonicalPage]) -> list[CanonicalPage]: ...
    def detect_sections(self, pages: list[CanonicalPage]) -> list[Section]: ...
    def segment_clauses(self, sections: list[Section], pages: list[CanonicalPage]) -> list[Clause]: ...
```

Returns parser-independent canonical objects. Parser-specific behavior hidden behind adapters.

### 5.4 Analysis Engine

**Responsibilities:**
- Deterministic entity extraction
- Timeline derivation
- Taxonomy classification
- Consistency checks
- Attention detectors

**Key principle:** LLM calls invoked only through `AIOrchestrator`; output accepted only after schema and evidence validation.

### 5.5 Retrieval Engine

**Responsibilities:**
- Store clause- and paragraph-level chunks with metadata
- Document and ownership filters before similarity search
- Hybrid retrieval: lexical matching + vector similarity
- Retrieve up to 12 candidates → rerank to 5 evidence units
- Return source IDs, not untrusted free-form text alone

**Metadata per chunk:** `document_id`, `page_number`, `section_id`, `clause_id`, `source_block_ids`, `content_hash`, `language`, `embedding_model_version`

### 5.6 AI Orchestration Layer

**Interface:**
```python
class AIOrchestrator(Protocol):
    async def generate_structured(
        self, 
        prompt: PromptTemplate, 
        evidence: list[Evidence],
        schema: type[BaseModel], 
        model: str,
        timeout: int
    ) -> ValidatedAIResult: ...
```

Records model name, latency, token counts, validation attempts — without logging document text. All calls use low temperature.

---

## 6. Storage Architecture

### 6.1 PostgreSQL

Stores metadata and normalized structured data. `pgvector` stores embeddings alongside chunk metadata.

### 6.2 Object Storage (S3-compatible)

Stores:
- Original uploaded files
- Optionally: page renderings (can be regenerated; short TTL)

### 6.3 Data Lifecycle

| Data | Storage | TTL | Deletion |
|------|---------|-----|----------|
| Original file | Object storage | Configurable (default 24h) | Soft delete → hard delete by retention job |
| Normalized text | PostgreSQL | While document exists | Cascade on document delete |
| Embeddings | PostgreSQL (pgvector) | While document exists | Cascade on document delete |
| Page renderings | Object storage | Short TTL | Auto-expire or regenerate |
| Chat sessions | PostgreSQL | Configurable (default 24h) | Cascade on session expire |
| Audit events | PostgreSQL | Long retention | Separate policy |

---

## 7. Database Design

UUID/ULID primary keys. All timestamps UTC. Every user-owned table has `owner_id` directly or through a document relation. Soft deletion for documents.

### 7.1 Entity-Relationship Overview

```
users ─────────────────────────── documents
                                     │
                    ┌────────────────┼────────────────────┐
                    │                │                     │
              document_pages    sections              analysis_runs
                                     │
                                  clauses
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                entities          evidence          chunks
                                     │
                              ┌──────┴──────┐
                              │             │
                         findings    chat_messages
                              │             │
                    finding_evidence   message_citations
                    
              timeline_events    checklist_items    lawyer_questions
              
                            audit_events
```

### 7.2 Table Definitions

| Table | Key Columns | Constraints | Indexes |
|-------|-------------|-------------|---------|
| `users` | `id`, `email_hash`, `display_name`, `created_at`, `deleted_at` | PK; email hash unique when not null | email_hash |
| `documents` | `id`, `owner_id`, `filename`, `mime_type`, `sha256`, `status`, `language`, `document_type`, `object_key`, `expires_at` | FK users; status enum; size check | owner/status, expires_at, sha256 |
| `document_pages` | `id`, `document_id`, `page_number`, `text`, `source`, `width`, `height`, `content_hash` | unique(document_id, page_number) | document/page |
| `sections` | `id`, `document_id`, `number`, `heading`, `page_start`, `page_end`, `parent_id` | FK; page checks | document/number |
| `clauses` | `id`, `document_id`, `section_id`, `number`, `original_text`, `normalized_text`, `page_start`, `page_end`, `bbox_json`, `clause_type`, `confidence` | FK; text not empty | document/type, section |
| `entities` | `id`, `document_id`, `clause_id`, `type`, `surface_form`, `normalized_value`, `confidence`, `page_number`, offsets | FK; confidence 0..1 | document/type, clause |
| `evidence` | `id`, `document_id`, `page_number`, `clause_id`, `quote`, `quote_hash`, `status`, `bbox_json` | FK; verified status requires clause/page | document/clause |
| `findings` | `id`, `document_id`, `category`, `severity`, `title`, `explanation`, `confidence`, `requires_review`, `detector_version` | FK; controlled enums | document/severity |
| `finding_evidence` | `finding_id`, `evidence_id` | composite PK | evidence |
| `timeline_events` | `id`, `document_id`, `event_type`, `label`, `date_value`, `duration_days`, `date_status`, `trace_json` | FK; explicit date rules | document/date |
| `checklist_items` | `id`, `document_id`, `text`, `status`, `reason`, `sort_order` | FK; status enum | document/status |
| `lawyer_questions` | `id`, `document_id`, `question`, `reason`, `sort_order` | FK | document |
| `analysis_runs` | `id`, `document_id`, `version`, `status`, `stage`, `prompt_version`, `model`, timings, `error_code` | unique(document_id, version) | document/status |
| `chunks` | `id`, `document_id`, `clause_id`, `text`, `metadata_json`, `embedding`, `model_version` | FK; vector dimension check | HNSW vector, document |
| `chat_sessions` | `id`, `document_id`, `owner_id`, `created_at`, `expires_at` | FK; owner consistency | document/owner |
| `chat_messages` | `id`, `session_id`, `role`, `content`, `answer_status`, `created_at` | FK; role enum | session/time |
| `message_citations` | `message_id`, `evidence_id` | composite PK | evidence |
| `audit_events` | `id`, `owner_id`, `document_id`, `event_type`, `request_id`, `metadata_json`, `created_at` | no raw content | owner/time, document/time |

### 7.3 Data NOT Persisted

- Raw LLM prompts
- Full retrieved contexts
- API keys
- Unneeded page images
- Model hidden reasoning
- Rejected free-form model output
- Temporary OCR intermediates after normalization
- Unredacted stack traces

---

## 8. API Specification

All endpoints under `/api/v1`. JSON responses use an envelope with `request_id`.

### 8.1 Endpoint Summary

| Method | Path | Purpose | Status |
|--------|------|---------|--------|
| `POST` | `/documents/upload` | Upload and enqueue analysis | 202 |
| `GET` | `/documents/{id}` | Document metadata and processing state | 200/404 |
| `POST` | `/documents/{id}/analyze` | Start/restart analysis | 202/409 |
| `GET` | `/documents/{id}/analysis` | Legal Situation Map (full read model) | 200/202 |
| `GET` | `/documents/{id}/clauses` | Paginated clause list | 200 |
| `GET` | `/documents/{id}/findings` | Findings with evidence IDs | 200 |
| `GET` | `/documents/{id}/timeline` | Timeline events with date status | 200 |
| `POST` | `/documents/{id}/questions` | Generate professional questions | 200/202 |
| `POST` | `/documents/{id}/chat` | Document-grounded Q&A | 200 |
| `POST` | `/compare` | Two-document comparison (Phase 2) | — |
| `GET` | `/health` | Liveness check | 200 |
| `GET` | `/health/ready` | Readiness check (DB, workers) | 200 |

### 8.2 Upload Endpoint

```
POST /api/v1/documents/upload
Content-Type: multipart/form-data
```

**Request:** `file` (required), `language_hint` (optional), `retain_hours` (optional)

**Response 202:**
```json
{
  "request_id": "req_1",
  "document_id": "doc_1",
  "analysis_id": "run_1",
  "status": "QUEUED"
}
```

**Error codes:** 400 (invalid metadata), 413 (size), 415 (type), 422 (malformed file), 429 (rate limit)

**Validations:** extension, magic bytes, size ≤ 20MB, page count ≤ 100, owner, idempotency key

### 8.3 Chat Endpoint

```
POST /api/v1/documents/{id}/chat
```

**Request:**
```json
{
  "session_id": "chat_1",
  "question": "What happens if I terminate early?",
  "allow_external_context": false
}
```

**Response 200:**
```json
{
  "request_id": "req_2",
  "message_id": "msg_1",
  "answer": "The supplied document states ...",
  "answer_status": "SUPPORTED",
  "citations": [
    {
      "evidence_id": "ev_1",
      "page_number": 2,
      "clause_id": "clause_4_1",
      "quote": "..."
    }
  ],
  "limitations": ["The document does not state whether ..."]
}
```

### 8.4 Common Error Schema

```json
{
  "request_id": "req_1",
  "error": {
    "code": "DOCUMENT_NOT_READY",
    "message": "Analysis is still processing. You can view the current extraction status."
  }
}
```

### 8.5 Authorization

Every document query includes `WHERE owner_id = current_user.id`. Evidence, clauses, pages, chat sessions, and analysis runs are reachable only through a document that passes the same ownership check. Unauthorized IDs return 404 (same shape as missing) to prevent enumeration.

---

## 9. Route Structure (Frontend)

```
/                                    Landing page
/upload                              Upload page
/documents/[id]/processing           Processing progress
/documents/[id]/dashboard            Legal Situation Map
/documents/[id]/viewer               Document viewer with highlights
/documents/[id]/clauses              Clause browser
/documents/[id]/findings             Findings detail
/documents/[id]/timeline             Timeline view
/documents/[id]/chat                 Grounded Q&A
/documents/[id]/checklist            Preparation checklist
/compare                             Document comparison (Phase 2)
/privacy                             Privacy policy
```

---

## 10. Deployment Architecture

### 10.1 MVP Deployment

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│   Vercel     │     │  Railway /   │     │   Managed      │
│   (Next.js)  │────>│  Render      │────>│   PostgreSQL   │
│              │     │  (FastAPI)   │     │   + pgvector   │
└─────────────┘     └──────┬───────┘     └────────────────┘
                           │
                    ┌──────┴───────┐
                    │ S3-compatible │
                    │ Object Store  │
                    └──────────────┘
```

### 10.2 Local Development

```yaml
# docker-compose.yml services:
- postgres:15 + pgvector
- minio (S3-compatible)
- redis (optional)
- api (FastAPI, hot-reload)
- web (Next.js, hot-reload)
```

---

## 11. Environment Configuration

```env
APP_ENV=development
APP_NAME=legallens
API_BASE_URL=http://localhost:8000
WEB_BASE_URL=http://localhost:3000
DATABASE_URL=postgresql+psycopg://legallens:legallens@localhost:5432/legallens
REDIS_URL=redis://localhost:6379/0
OBJECT_STORAGE_ENDPOINT=http://localhost:9000
OBJECT_STORAGE_BUCKET=legallens-private
OBJECT_STORAGE_ACCESS_KEY=
OBJECT_STORAGE_SECRET_KEY=
LLM_API_BASE=
LLM_API_KEY=
LLM_MODEL=
LLM_FALLBACK_MODEL=
EMBEDDING_MODEL=
MAX_UPLOAD_SIZE_MB=20
MAX_PDF_PAGES=100
DOCUMENT_TTL_HOURS=24
CHAT_TTL_HOURS=24
OCR_ENABLED=true
EXTERNAL_RAG_ENABLED=false
CORS_ORIGINS=http://localhost:3000
RATE_LIMIT_PER_MINUTE=30
LOG_LEVEL=INFO
SECRET_KEY=
```

Configuration loaded once into a typed settings object. Missing required secrets fail startup in production; development uses explicit warnings.

---

## 12. Repository Structure

```
legallens/
├── apps/
│   ├── web/                          # Next.js frontend
│   │   ├── app/                      # App router pages
│   │   ├── components/               # UI components
│   │   ├── lib/                      # API client, hooks, utils
│   │   └── tests/                    # Frontend tests
│   └── api/                          # FastAPI backend
│       ├── app/
│       │   ├── api/                  # Route handlers
│       │   ├── core/                 # Config, security, middleware
│       │   ├── db/                   # Database session, connection
│       │   ├── models/               # SQLAlchemy models
│       │   ├── repositories/         # Data access layer
│       │   ├── services/             # Business logic
│       │   │   ├── parsers/          # PDF, DOCX, OCR adapters
│       │   │   └── detectors/        # Finding detectors
│       │   └── main.py               # App entry point
│       └── tests/                    # API tests
├── packages/
│   ├── schemas/                      # Shared Pydantic & TS types
│   ├── prompts/                      # Versioned prompt templates
│   └── shared/                       # Shared utilities
├── data/
│   ├── sample-documents/             # Demo fixtures
│   └── evaluation/                   # Golden test documents
├── tests/
│   ├── integration/                  # Cross-component tests
│   ├── security/                     # Security test suite
│   └── fixtures/                     # Test data
├── scripts/                          # Utility scripts
├── docs/                             # This documentation
├── docker/                           # Dockerfiles
├── alembic/                          # Database migrations
├── .github/workflows/                # CI/CD
├── docker-compose.yml
├── Makefile
├── README.md
├── .env.example
└── pyproject.toml
```
