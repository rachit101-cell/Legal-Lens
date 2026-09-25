# LegalLens — Implementation Plan

**Version:** 1.0.0  
**Status:** Implementation-Ready  
**Last Updated:** 2026-09-23

---

## 1. Development Phases

| Phase | Objective | Tasks | Acceptance Criteria | Complexity |
|-------|-----------|-------|---------------------|------------|
| 0 | Foundation | Monorepo, settings, schemas, DB, Docker, CI, design tokens | App boots; migrations and shared types pass | Medium |
| 1 | Document Engine | Upload, validation, PDF/DOCX, OCR adapter, canonical model | Fixture pages and clauses preserve source locations | High |
| 2 | Legal Intelligence | Taxonomy, entities, dates, obligations | Golden extraction reaches target precision | Medium |
| 3 | Analysis Engine | Findings, conflicts, missing information | Every finding has evidence and detector version | Medium |
| 4 | RAG | Chunks, embeddings, pgvector, hybrid retrieval | Retrieval recall target passes | Medium |
| 5 | LLM Layer | Prompts, model adapter, structured output, fallback | Schema validity and safety tests pass | High |
| 6 | Evidence Layer | Claim validator, page viewer anchors | Citation clicks reach highlighted source | High |
| 7 | Frontend | All MVP pages, dashboard, chat, checklist | Complete demo path works on mobile and keyboard | High |
| 8 | Security | Upload hardening, ownership, injection defense, TTL | Security suite passes | Medium |
| 9 | Testing | Golden set, integration, AI metrics, accessibility | Gates are reported in CI | Medium |
| 10 | Deployment | Managed services, secrets, migrations, health checks | Public demo is repeatable | Medium |
| 11 | Demo Polish | Seed data, loading states, pitch, recovery controls | 3-minute demo works twice consecutively | Medium |

---

## 2. Task Backlog (Dependency Order)

### TASK FND-001: Establish Typed Monorepo & Infrastructure

**Objective:** Create repository, Python/TypeScript toolchains, Docker Compose, configuration, CI skeleton.

**Files to Create:**
| File | Purpose |
|------|---------|
| `README.md` | Project documentation, setup instructions |
| `.env.example` | Environment variable template |
| `pyproject.toml` | Python project configuration (Ruff, Pytest, dependencies) |
| `apps/api/app/core/config.py` | Typed environment configuration with `get_settings()` |
| `apps/api/app/main.py` | FastAPI app creation with `create_app()` |
| `apps/api/requirements.txt` | Python dependencies |
| `docker-compose.yml` | PostgreSQL+pgvector, MinIO, optional Redis |
| `docker/Dockerfile.api` | API container |
| `docker/Dockerfile.web` | Web container |
| `apps/web/package.json` | Next.js project configuration |
| `apps/web/tsconfig.json` | TypeScript strict mode config |
| `apps/web/next.config.js` | Next.js configuration |
| `.github/workflows/ci.yml` | CI pipeline skeleton |
| `Makefile` | Common development commands |

**Dependencies:** None  
**Done when:** `docker compose up` boots; `GET /api/v1/health` returns `{status, version, request_id}`.

---

### TASK FND-002: Define Canonical Schemas & Database Migrations

**Objective:** Implement shared Pydantic/TypeScript schemas and all core database tables.

**Files to Create:**
| File | Purpose |
|------|---------|
| `packages/schemas/enums.py` | Status enums, source types, severity levels |
| `packages/schemas/documents.py` | Document, Page, Section, Clause models |
| `packages/schemas/entities.py` | Entity extraction models |
| `packages/schemas/evidence.py` | Evidence and Claim models |
| `packages/schemas/findings.py` | Finding and detector models |
| `packages/schemas/timeline.py` | Timeline event models |
| `packages/schemas/analysis.py` | Analysis run and result models |
| `packages/schemas/chat.py` | Chat session and message models |
| `packages/schemas/api.py` | API request/response envelope models |
| `apps/api/app/models/base.py` | SQLAlchemy base, mixins |
| `apps/api/app/models/document.py` | Document, Page, Section SQLAlchemy models |
| `apps/api/app/models/analysis.py` | Analysis, Finding, Timeline SQLAlchemy models |
| `apps/api/app/models/chat.py` | Chat, Message SQLAlchemy models |
| `apps/api/app/db/session.py` | Database session management |
| `alembic/env.py` | Alembic environment |
| `alembic/versions/001_initial.py` | Initial migration (all 14+ tables) |

**Dependencies:** FND-001  
**Done when:** All later services import domain types. Invalid AI output cannot pass schema validation.

---

### TASK DOC-001: Implement Secure Upload & Quarantine

**Objective:** Accept PDF/DOCX with streaming validation and private storage.

**Files to Create:**
| File | Purpose |
|------|---------|
| `apps/api/app/api/documents.py` | Upload endpoint and document routes |
| `apps/api/app/services/upload_service.py` | `validate_upload()`, `create_document()` |
| `apps/api/app/services/storage.py` | `put_private()`, `get_private()`, `delete()` |
| `apps/api/app/repositories/document_repo.py` | Document data access layer |
| `tests/security/test_uploads.py` | Upload security tests |

**Validations:** Extension, MIME, magic bytes, size ≤ 20MB, SHA-256, page estimate, idempotency key.

**Dependencies:** FND-002  
**Done when:** A valid fixture returns a private document record. Invalid inputs are rejected.

---

### TASK DOC-002: Build PDF, DOCX & OCR Adapters

**Objective:** Produce page text, layout blocks, and metadata for all supported files.

**Files to Create:**
| File | Purpose |
|------|---------|
| `apps/api/app/services/document_engine.py` | `process_document()` orchestrator |
| `apps/api/app/services/parsers/pdf_parser.py` | `extract_pdf()` via PyMuPDF |
| `apps/api/app/services/parsers/docx_parser.py` | `extract_docx()` via python-docx |
| `apps/api/app/services/parsers/ocr_parser.py` | `ocr_page()` via Tesseract adapter |
| `data/sample-documents/demo-notice.pdf` | Synthetic demo document |
| `tests/unit/test_parsers.py` | Parser unit tests |

**Interface:** `extract(file_path) -> CanonicalDocumentDraft`

**Dependencies:** DOC-001, FND-002  
**Done when:** Demo notice produces readable pages and source locations.

---

### TASK INT-001: Segment Clauses & Extract Entities

**Objective:** Build canonical sections, clauses, entities, and taxonomy labels.

**Files to Create:**
| File | Purpose |
|------|---------|
| `apps/api/app/services/clause_segmenter.py` | `segment_clauses()` — headings, numbering, hierarchy |
| `apps/api/app/services/entity_extractor.py` | `extract_entities()` — dates, money, durations, parties |
| `apps/api/app/services/taxonomy.py` | Clause taxonomy classification rules |
| `apps/api/app/repositories/clause_repo.py` | Clause data access layer |
| `apps/api/app/repositories/entity_repo.py` | Entity data access layer |
| `tests/unit/test_intelligence.py` | Segmentation and extraction tests |

**Dependencies:** DOC-002  
**Done when:** Golden extraction snapshot is stable. No entity/clause returned without source page.

---

### TASK ANA-001: Implement Timeline & Transparent Findings

**Objective:** Generate timeline events and attention findings with evidence.

**Files to Create:**
| File | Purpose |
|------|---------|
| `apps/api/app/services/timeline_engine.py` | `build_timeline()` — date parsing, arithmetic |
| `apps/api/app/services/finding_engine.py` | `run_findings()` — detector orchestration |
| `apps/api/app/services/detectors/financial.py` | Financial detectors |
| `apps/api/app/services/detectors/commitment.py` | Commitment detectors |
| `apps/api/app/services/detectors/liability.py` | Liability detectors |
| `apps/api/app/services/detectors/termination.py` | Termination detectors |
| `apps/api/app/services/detectors/consistency.py` | Consistency detectors |
| `apps/api/app/repositories/finding_repo.py` | Finding data access layer |
| `apps/api/app/repositories/timeline_repo.py` | Timeline data access layer |
| `tests/unit/test_timeline.py` | Timeline tests |
| `tests/unit/test_findings.py` | Finding detector tests |

**Dependencies:** INT-001  
**Done when:** Demo dashboard renders useful results without an LLM.

---

### TASK RET-001: Add Document Retrieval with pgvector

**Objective:** Index clause chunks and retrieve evidence for Q&A.

**Files to Create:**
| File | Purpose |
|------|---------|
| `apps/api/app/services/retrieval_service.py` | `index_document()`, `retrieve()` |
| `apps/api/app/services/embedding_provider.py` | Embedding adapter |
| `apps/api/app/services/chunker.py` | Clause-level chunking with metadata |
| `apps/api/app/repositories/chunk_repo.py` | Chunk data access layer |
| `tests/integration/test_retrieval.py` | Retrieval tests (recall@5) |

**Dependencies:** INT-001, embedding provider  
**Done when:** Q&A can retrieve termination clause from a paraphrased question.

---

### TASK AI-001: Build Model Adapter & Prompt Library

**Objective:** Safe, versioned prompts and schema-validated generation.

**Files to Create:**
| File | Purpose |
|------|---------|
| `apps/api/app/services/ai_engine.py` | `generate_summary()`, `answer_question()`, `generate_checklist()` |
| `apps/api/app/services/model_provider.py` | `generate_structured()` adapter |
| `apps/api/app/services/output_validator.py` | Schema validation and retry logic |
| `packages/prompts/clause_explanation.md` | Clause explanation prompt v1.0 |
| `packages/prompts/document_summary.md` | Document summary prompt v1.0 |
| `packages/prompts/finding_explanation.md` | Finding explanation prompt v1.0 |
| `packages/prompts/qa_answer.md` | Q&A answer prompt v1.0 |
| `packages/prompts/checklist.md` | Checklist generation prompt v1.0 |
| `packages/prompts/professional_questions.md` | Professional questions prompt v1.0 |
| `tests/unit/test_ai_validation.py` | AI output validation tests |

**Dependencies:** FND-002, RET-001  
**Done when:** A mocked model and live model both satisfy the same interface.

---

### TASK EVD-001: Implement Evidence & Claim Verification

**Objective:** Validate every citation and classify claims.

**Files to Create:**
| File | Purpose |
|------|---------|
| `apps/api/app/services/evidence_service.py` | Evidence creation and resolution |
| `apps/api/app/services/claim_verifier.py` | `verify_claims()` |
| `apps/api/app/repositories/evidence_repo.py` | Evidence data access layer |
| `tests/unit/test_evidence.py` | Evidence verification tests |

**Dependencies:** DOC-002, INT-001, AI-001  
**Done when:** Clicking a citation locates the source. Unsupported claims are omitted or marked.

---

### TASK WEB-001: Build Accessible Dashboard & Viewer

**Objective:** Create complete MVP user journey and evidence navigation.

**Files to Create:**
| File | Purpose |
|------|---------|
| `apps/web/app/page.tsx` | Landing page |
| `apps/web/app/upload/page.tsx` | Upload page |
| `apps/web/app/documents/[id]/processing/page.tsx` | Processing progress |
| `apps/web/app/documents/[id]/dashboard/page.tsx` | Legal Situation Map |
| `apps/web/app/documents/[id]/viewer/page.tsx` | Document viewer |
| `apps/web/app/documents/[id]/clauses/page.tsx` | Clause browser |
| `apps/web/app/documents/[id]/findings/page.tsx` | Findings detail |
| `apps/web/app/documents/[id]/timeline/page.tsx` | Timeline view |
| `apps/web/app/documents/[id]/chat/page.tsx` | Grounded Q&A |
| `apps/web/app/documents/[id]/checklist/page.tsx` | Preparation checklist |
| `apps/web/app/privacy/page.tsx` | Privacy policy |
| `apps/web/app/layout.tsx` | Root layout |
| `apps/web/app/globals.css` | Design system tokens and styles |
| `apps/web/components/Card.tsx` | Card component |
| `apps/web/components/Badge.tsx` | Badge component |
| `apps/web/components/Button.tsx` | Button component |
| `apps/web/components/Tabs.tsx` | Tabs component |
| `apps/web/components/Alert.tsx` | Alert/Disclaimer component |
| `apps/web/components/EvidenceLink.tsx` | Evidence navigation component |
| `apps/web/components/DocumentViewer.tsx` | Document viewer component |
| `apps/web/components/FindingCard.tsx` | Finding card component |
| `apps/web/components/TimelineView.tsx` | Timeline component |
| `apps/web/components/ChatMessage.tsx` | Chat message component |
| `apps/web/components/ChecklistItem.tsx` | Checklist item component |
| `apps/web/components/ProcessingStage.tsx` | Processing stage component |
| `apps/web/components/SeverityBadge.tsx` | Severity badge component |
| `apps/web/components/SourceTypeBadge.tsx` | Source type badge component |
| `apps/web/components/Disclaimer.tsx` | Disclaimer component |
| `apps/web/components/Skeleton.tsx` | Loading skeleton component |
| `apps/web/lib/api.ts` | Typed API client |
| `apps/web/lib/hooks.ts` | Custom React hooks |
| `apps/web/lib/types.ts` | TypeScript type definitions |
| `apps/web/lib/constants.ts` | Configuration constants |

**Dependencies:** API read endpoints, EVD-001  
**Done when:** Demo flow works without documentation or developer tools. Judge navigates finding to evidence in 2 clicks.

---

### TASK SEC-001: Harden Security, Retention & Audit

**Objective:** Complete ownership controls, CSP, TTL deletion, redacted logs, injection defense.

**Files to Create:**
| File | Purpose |
|------|---------|
| `apps/api/app/core/security.py` | `get_current_user()`, `authorize_document()`, rate limiting |
| `apps/api/app/services/retention.py` | TTL deletion job |
| `apps/api/app/middleware/logging.py` | Redacted structured logging |
| `tests/security/test_ownership.py` | Cross-user access tests |
| `tests/security/test_injection.py` | Prompt injection tests |
| `tests/security/test_csp.py` | CSP and XSS tests |
| `docs/THREAT_MODEL.md` | Threat model document |

**Dependencies:** DOC-001, AI-001, WEB-001  
**Done when:** Security checklist complete. No cross-user read path. No injection tool execution.

---

### TASK QA-001: Golden Evaluation, Deployment & Demo

**Objective:** Measurable quality gates and repeatable 3-minute demo.

**Files to Create:**
| File | Purpose |
|------|---------|
| `data/evaluation/lease.pdf` | Golden lease document |
| `data/evaluation/notice.pdf` | Golden termination notice |
| `data/evaluation/employment.pdf` | Golden employment agreement |
| `data/evaluation/expected/*.json` | Expected extraction results |
| `scripts/run_evaluation.py` | Evaluation runner and metrics |
| `scripts/seed_demo.py` | Demo data seeder |
| `docs/DEMO_SCRIPT.md` | Demo playbook |

**Dependencies:** All MVP tasks  
**Done when:** Demo works twice consecutively. CI evaluation gates pass.

---

## 3. File-by-File Build Plan

| File | Public Functions | Dependencies | Test File |
|------|-----------------|--------------|-----------|
| `app/main.py` | `create_app()` | settings, routers | `test_main.py` |
| `app/core/config.py` | `get_settings()` | pydantic-settings | `test_config.py` |
| `app/core/security.py` | `get_current_user()`, `authorize_document()` | DB, session | `test_security.py` |
| `app/services/upload_service.py` | `validate_upload()`, `create_document()` | storage, repos | `test_uploads.py` |
| `app/services/storage.py` | `put_private()`, `get_private()`, `delete()` | S3 client | `test_storage.py` |
| `app/services/document_engine.py` | `process_document()` | parsers, schemas | `test_document_engine.py` |
| `app/services/parsers/pdf_parser.py` | `extract_pdf()` | PyMuPDF | `test_pdf_parser.py` |
| `app/services/parsers/docx_parser.py` | `extract_docx()` | python-docx | `test_docx_parser.py` |
| `app/services/parsers/ocr_parser.py` | `ocr_page()` | OCR adapter | `test_ocr.py` |
| `app/services/clause_segmenter.py` | `segment_clauses()` | regex, schemas | `test_clause_segmenter.py` |
| `app/services/entity_extractor.py` | `extract_entities()` | regex, dateparser | `test_entities.py` |
| `app/services/timeline_engine.py` | `build_timeline()` | date arithmetic | `test_timeline.py` |
| `app/services/finding_engine.py` | `run_findings()` | detector modules | `test_findings.py` |
| `app/services/retrieval_service.py` | `index_document()`, `retrieve()` | embeddings, pg | `test_retrieval.py` |
| `app/services/ai_engine.py` | `generate_summary()`, `answer_question()` | model provider | `test_ai_engine.py` |
| `app/services/claim_verifier.py` | `verify_claims()` | evidence repo | `test_claims.py` |
| `app/api/documents.py` | endpoint functions | services, deps | `test_document_api.py` |
| `app/api/analysis.py` | endpoint functions | services | `test_analysis_api.py` |
| `app/api/chat.py` | endpoint functions | retrieval, AI, verifier | `test_chat_api.py` |
| `packages/schemas/domain.py` | Pydantic models | pydantic | `test_schemas.py` |
| `apps/web/lib/api.ts` | `upload()`, `getAnalysis()`, `ask()` | fetch, types | `api.test.ts` |
| `apps/web/components/EvidenceLink.tsx` | `EvidenceLink` | router, viewer | component test |
| `apps/web/components/DocumentViewer.tsx` | `DocumentViewer` | evidence API | component test |
| `apps/web/app/documents/[id]/dashboard/page.tsx` | page component | API hooks | route test |

---

## 4. API Build Order

Implement APIs in this order:

1. **Health** — `GET /health`, `GET /health/ready`
2. **Upload** — `POST /documents/upload`
3. **Document status** — `GET /documents/{id}`
4. **Analysis trigger** — `POST /documents/{id}/analyze`
5. **Analysis status** — `GET /documents/{id}/analysis` (polling)
6. **Clauses** — `GET /documents/{id}/clauses`
7. **Findings** — `GET /documents/{id}/findings`
8. **Timeline** — `GET /documents/{id}/timeline`
9. **Analysis aggregate** — `GET /documents/{id}/analysis` (full read model)
10. **Chat** — `POST /documents/{id}/chat`
11. **Questions** — `POST /documents/{id}/questions`
12. **Compare** — `POST /compare` (Phase 2)

For every route:
1. Define request/response Pydantic models
2. Add authorization dependency
3. Add repository query
4. Add service call
5. Add error mapping
6. Add route test

---

## 5. Coding Standards

### 5.1 Python

- Python 3.11 with strict typing
- Small pure functions for parsing and detection
- Dependency injection for storage, model, and clock providers
- Repository classes for database access
- `snake_case` for modules and functions
- `PascalCase` for classes and Pydantic models
- Explicit return types everywhere
- Domain-specific exceptions → stable API error codes
- Structured logging with `request_id` and `analysis_id`
- Async I/O at API boundary; CPU-heavy parsing in bounded thread pool
- Docstrings on public service interfaces
- Format with Ruff; type check with Pyright/MyPy

### 5.2 TypeScript

- TypeScript strict mode
- Discriminated unions for statuses and source types
- `camelCase` for variables/functions; `PascalCase` for components/types
- No `any` for API data
- Network access only in typed client modules
- Components focused on rendering and interaction
- Semantic HTML before ARIA
- Test loading, error, partial, and empty states
- Format with Prettier; lint with ESLint

### 5.3 General

- Version API paths under `/api/v1`
- Breaking schema changes must be explicit
- Prompts, JSON schemas, detector versions, extraction versions in source control
- Prefer immutable analysis versions over in-place mutation
- Migrations for all database changes
- Tests required for every new detector, prompt, parser, and API route

---

## 6. Testing Strategy

### 6.1 Test Categories

| Category | Scope | Tools |
|----------|-------|-------|
| **Unit** | Parsers, entities, timeline, detectors, schemas | Pytest, fixtures, golden snapshots |
| **Integration** | Upload → parse → analyze → retrieve → verify | Pytest, test PostgreSQL |
| **Security** | Malformed files, MIME spoofing, injection, ownership | Pytest, custom fixtures |
| **Accessibility** | All pages, keyboard nav, screen reader | axe-core, manual keyboard pass |
| **AI Evaluation** | Golden documents, citation accuracy, claim rates | Custom evaluation runner |
| **Frontend** | Components, routes, responsive, interactions | Vitest, Playwright |

### 6.2 Unit Test Coverage

- Native PDF and DOCX extraction
- Low-density OCR fallback
- Page coordinate preservation
- Heading detection and clause segmentation
- Date parsing (Indian and international formats)
- Money normalization with `Decimal` (including ₹)
- Duration arithmetic
- Recurring obligations
- Taxonomy rules for all 9 categories
- Conflict detection
- Evidence quote matching (exact and normalized)
- Prompt schema validation
- Error mapping

### 6.3 Integration Test Scenarios

- Full pipeline: upload → parse → analyze → index → retrieve → generate → verify → persist → read
- Model returns invalid JSON → retry → success
- Citation points to wrong page → rejection
- Ownership check failure → 404
- Partial analysis → deterministic facts available

### 6.4 Security Test Scenarios

- Oversized files, malformed PDFs, mismatched MIME
- Decompression bombs
- Embedded scripts in DOCX
- XSS strings in clause text
- SQL-like search input
- Prompt-injection passages
- Unauthorized document IDs
- Duplicate idempotency keys
- Rate-limit abuse
- Expired documents

### 6.5 MVP Evaluation Gates

| Gate | Target |
|------|--------|
| Zero unauthorized document reads | 0 |
| 100% citation IDs resolve | 100% |
| Unsupported claim rate | < 2% |
| Citation accuracy | > 95% |
| No critical accessibility violation | 0 |
| Schema validity rate | > 99% |

---

## 7. CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
jobs:
  lint-format:
    - Ruff (Python)
    - ESLint + Prettier (TypeScript)
  
  type-check:
    - Pyright/MyPy (Python)
    - tsc --noEmit (TypeScript)
  
  unit-tests:
    - pytest (API unit tests)
    - vitest (frontend unit tests)
  
  integration-tests:
    services: [postgres]
    - pytest (integration suite)
  
  security-tests:
    - pytest (security suite)
    - dependency scan
  
  accessibility-tests:
    - axe-core smoke tests
  
  schema-check:
    - OpenAPI ↔ shared schemas consistency
  
  migration-check:
    - alembic upgrade + downgrade
```

---

## 8. Observability

### 8.1 Structured Logging

Every log entry includes:
- `request_id`
- `analysis_id` (when applicable)
- `document_id_hash` (NOT the actual ID)
- `stage`
- `duration_ms`
- `status`
- `model` (when applicable)
- `token_count`
- `error_code`

### 8.2 What NOT to Log

- Raw document text or quotes
- Email addresses or phone numbers
- File contents or prompts
- API keys or secrets
- Stack traces with document data

### 8.3 Counters to Track

- Upload rejections (by reason)
- OCR fallback invocations
- Schema retry count
- Citation rejections
- Model timeouts
- Q&A unsupported answer rate

---

## 9. Security Checklist

- [ ] File size, extension, MIME, magic-byte, page-count validation server-side
- [ ] Files quarantined before parsing; temporary files deleted
- [ ] Embedded document instructions treated as untrusted text
- [ ] Model has no shell, network, storage, or arbitrary tool access
- [ ] All generated output schema-validated and citation-verified
- [ ] Every query enforces ownership (`WHERE owner_id = current_user.id`)
- [ ] Unauthorized IDs return same 404 shape as nonexistent IDs
- [ ] Browser output escapes document text; restrictive CSP
- [ ] API requests have size, timeout, and rate limits
- [ ] Object storage private; accessed through authorized proxy or signed URLs
- [ ] Logs exclude raw legal text, quotes, prompts, secrets, personal data
- [ ] Document and chat TTL deletion implemented and tested
- [ ] Secrets from environment or secret manager only
- [ ] Synthetic documents in public demonstration
- [ ] Dependency, container, and static security scans in CI
- [ ] UI displays information-only disclaimer at upload, result, and chat stages

---

## 10. Performance Targets

| Stage | Target (10-page native PDF, warm) |
|-------|----------------------------------|
| Upload acknowledgment | < 2s |
| Native extraction | < 5s |
| Deterministic analysis | < 10s |
| Complete AI analysis | < 45s |
| Q&A response | < 8s |
| Dashboard read (cached) | < 1s |

**Principles:**
- Parse each file once
- Batch entity extraction per page
- Embed clauses in batches
- Retrieve only on demand (Q&A, explanation)
- Cache by document hash + extraction version + prompt version + model
- Limit concurrent model calls; use timeouts
- Show actual stage timings (never promise fixed latency)
