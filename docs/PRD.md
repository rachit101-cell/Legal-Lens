# LegalLens — Product Requirements Document (PRD)

**Version:** 1.0.0  
**Status:** Implementation-Ready  
**Last Updated:** 2026-09-23

---

## 1. Product Vision

LegalLens is an **AI Legal Document Risk & Action Navigator**. It converts an uploaded legal document into a structured **Legal Situation Map** containing document facts, parties, obligations, dates, attention items, missing information, preparation tasks, and questions for a legal professional.

> **LegalLens is an information tool, not an AI lawyer.**

### Core Differentiator

**Evidence-linked AI**: every material finding or answer points to the source document — page, section, clause, and quoted passage — whenever the evidence is available.

### Design Principle

> **Deterministic where possible, AI where useful, evidence always, uncertainty when necessary, and security by design.**

---

## 2. Product Promise

LegalLens answers five questions without pretending to provide professional advice:

1. **What does the supplied document say?**
2. **What actions, payments, dates, and restrictions does it mention?**
3. **Which clauses deserve attention and why?**
4. **What information is missing or unverifiable?**
5. **What should the user prepare or ask a qualified legal professional?**

### Three-Layer Information Model

| Layer | Description | Example |
|-------|------------|---------|
| **WHAT THE DOCUMENT SAYS** | Direct facts and quotes from the uploaded file | "The tenant shall pay ₹25,000 monthly" |
| **WHAT LEGALLENS GENERATED** | Explanations, classifications, derived timelines, suggestions | "This clause appears to require monthly rent payments" |
| **EXTERNAL LEGAL INFORMATION** | Separately attributed context from approved sources (future) | "Under the Transfer of Property Act..." |

---

## 3. Safety Boundary

LegalLens MUST:
- Use language such as "the document states," "this clause appears to require," and "this point may warrant professional review"
- State that output depends on the supplied document and sources
- State that AI can make mistakes
- State that decisions requiring professional judgment should be reviewed with a qualified legal professional

LegalLens MUST NOT:
- Claim that a user will win
- State that a contract is definitely illegal
- Tell a user they do not need a lawyer
- Assert that the user is legally protected
- Produce unsourced legal conclusions

---

## 4. User Personas

### 4.1 Primary: Non-Lawyer Document Recipient

**Who:** Tenant, employee, small-business owner, customer, or family member who receives a notice or agreement.

**Needs:**
- Plain language explanations
- Visible evidence linking
- Low reading effort
- Mobile support
- No unexplained confidence scores

**Scenario:** Receives a legal notice about rent arrears and needs to understand what it says, what deadlines exist, and what to prepare before contacting a lawyer.

### 4.2 Secondary: Legal-Aid Intake Worker

**Who:** Legal-aid or community-support worker preparing an intake conversation.

**Needs:**
- Source-linked facts
- Missing-document detection
- Exportable checklists
- Clear distinction between document facts and generated suggestions

### 4.3 Tertiary: Hackathon Judge / Evaluator

**Who:** Technical evaluator assessing the product.

**Needs:**
- Understand differentiation without reading source code
- See a situation map, clickable finding, evidence highlight, and cited answer within 3 minutes

---

## 5. User Journeys

### 5.1 First-Time Analysis Journey

```
Landing Page → Upload Page → Processing Screen → Dashboard
     ↓              ↓              ↓                 ↓
  Privacy &      File type     Named stages      Situation Map:
  disclaimer     validation    with progress      • Snapshot
  visible        (client +     (not vague         • Key facts
                 server)       spinner)           • Findings
                                                  • Timeline
                                                  • Q&A
                                                  • Checklist
```

1. User lands on a privacy-forward upload page
2. Sees accepted file types, size limits, retention behavior, legal disclaimer
3. Selects a PDF or DOCX
4. Client performs basic validation; API repeats all validation
5. Processing screen shows named stages (not a vague spinner)
6. Dashboard opens with:
   - One-sentence snapshot
   - Key facts, attention items, timeline
   - Obligations, missing information
   - Professional questions
7. Clicking any item opens the exact page with highlighted evidence

### 5.2 Grounded Q&A Journey

1. User asks a question about the uploaded document
2. System classifies: document-only, document-plus-context, or unsupported
3. Retrieves relevant clauses, assembles bounded context
4. Generates structured answer with citation IDs
5. Validates every citation against stored evidence
6. Returns answer with source quote and uncertainty statement when evidence is incomplete
7. **Never silently substitutes general legal knowledge for document evidence**

### 5.3 Failure Journey

| Failure | User Experience |
|---------|----------------|
| Incomplete extraction | Shows which pages affected; recovered text still inspectable |
| No trustworthy evidence | "Cannot verify this point from the supplied material" |
| External service failure | Existing deterministic facts remain; unavailable section labeled |
| Corrupted PDF | "This file could not be read. Try exporting it again." |
| Poor OCR | Partial extraction with accuracy warning and affected pages |
| LLM failure | Deterministic facts shown; retry control; no fabricated prose |

---

## 6. Core Modes

| Mode | Description | MVP Status |
|------|------------|------------|
| **Understand** | Extract document type, parties, dates, amounts, jurisdiction, duration, clause structure, plain-language explanations | ✅ MVP |
| **Protect** | Detect obligations, deadlines, penalties, termination terms, renewal, liability, indemnity, restrictions, inconsistencies, missing information | ✅ MVP |
| **Act** | Produce situation snapshot, timeline, checklist, professional questions | ✅ MVP |
| **Compare** | Compare two normalized documents, link each change to both source versions | ⏳ Post-MVP |

---

## 7. Feature Matrix

| Feature | MVP | Phase 2 | Future | Judge Impact |
|---------|-----|---------|--------|-------------|
| PDF upload and validation | ✅ | Hardened malware scanning | Bulk upload | High |
| DOCX extraction | ✅ | Tables and tracked changes | More office formats | Medium |
| Scanned PDF OCR | ✅ (bounded) | Layout-aware OCR | Handwriting | High |
| Canonical pages, sections, clauses | ✅ | Improved segmentation | Learned segmentation | High |
| Parties, dates, amounts, durations | ✅ | Better multilingual | Domain models | High |
| Clause taxonomy | ✅ | Active learning | Custom taxonomies | High |
| Deterministic findings | ✅ | More jurisdictions | Configurable packs | High |
| Evidence-linked explanation | ✅ | Exportable report | Collaborative review | **Very High** |
| Timeline | ✅ | Calendar export | Reminder integration | High |
| Document-grounded Q&A | ✅ | Conversation memory | Multi-document Q&A | **Very High** |
| Preparation checklist | ✅ | Editable task tracking | Handoff workflows | High |
| Compare documents | ❌ | ✅ | Batch redlining | Medium |
| External legal RAG | ❌ | ✅ | Jurisdiction-aware corpus | Medium |
| Hindi output | ❌ | Optional | Additional languages | Medium |
| User accounts | Minimal session | Full authentication | Organization workspaces | Medium |

---

## 8. MVP Scope

### 8.1 Build Now

- Single-document pipeline
- Private document ownership
- Page-level evidence
- Curated clause taxonomy (9 categories)
- Deterministic date and amount extraction
- Rules-based attention detectors
- One structured LLM explanation pass
- Document-only Q&A
- Responsive accessible interface
- Structured logs
- Small golden evaluation set

### 8.2 Mock or Simplify

- Deterministic local demo identity or one-time session token (not full social login)
- Managed object store or local encrypted dev storage
- Single worker process or in-process background task
- Curated sample document with deterministic fallback fixtures

### 8.3 Postpone

- Broad external legal research
- Automated legal advice
- Cross-jurisdiction conclusions
- Contract redlining
- Full collaboration
- Lawyer marketplace handoff
- Handwriting OCR
- Model fine-tuning
- Organization-level policy management

---

## 9. Judge-Facing Success Criteria

| Criterion | Concrete Proof in Product |
|-----------|--------------------------|
| **Code quality** | Typed shared schemas, modular services, deterministic tests, clear dependency boundaries, reproducible local setup |
| **Problem alignment** | Upload-to-situation-map flow with plain-language explanation, obligations, deadlines, findings, Q&A, and preparation outputs |
| **Security** | File validation, private ownership checks, prompt-injection isolation, redacted logs, deletion controls, visible privacy messaging |
| **Efficiency** | Parse once, batch extraction, selective retrieval, cached analysis, bounded model calls, displayed processing stages |
| **Testing** | Unit tests, end-to-end pipeline tests, golden-document evaluation, security tests, accessibility checks |

---

## 10. Demo Scenario

Use a **synthetic three-page tenant notice**:

- **Page 1:** Identifies tenant and landlord, states payment is requested
- **Page 2:** Contains 15-day response deadline and 30-day notice clause
- **Page 3:** Refers to a lease that was NOT uploaded, contains conditional termination

The demo must demonstrate:
1. Upload with privacy boundary visible
2. Processing stages with actual timing
3. Legal Situation Map with document type, parties, deadline, payment obligation
4. Click "30-day termination notice" → highlighted evidence on original page
5. Timeline distinguishing explicit deadline from derived notice window
6. Grounded Q&A: "What happens if I terminate early?" → cited answer with limitation about missing lease
7. Preparation checklist and professional questions
8. Security visibility (prompt-injection test or privacy panel)

---

## 11. MVP Completion Criteria

The MVP is complete when:

1. ✅ A new developer can run documented local setup from a clean checkout
2. ✅ A user can upload a valid PDF or DOCX and receive visible processing progress
3. ✅ System preserves pages, sections, clauses, entities, and source locations
4. ✅ Deterministic extraction handles key dates, durations, amounts, notice periods
5. ✅ Findings use transparent categories with reasons and evidence
6. ✅ Timeline events distinguish explicit, extracted, derived, and inferred values
7. ✅ Q&A retrieves from user document and validates answer citations
8. ✅ Unsupported or unverified claims are clearly labeled or omitted
9. ✅ Viewer navigates from finding to original page and highlight
10. ✅ Dashboard includes obligations, missing information, checklist, professional questions
11. ✅ UI distinguishes document facts from generated output
12. ✅ Ownership checks prevent cross-user access
13. ✅ Prompt injection does not trigger tools, prompt disclosure, or data exfiltration
14. ✅ Files, logs, secrets, and retention satisfy security checklist
15. ✅ Unit, integration, AI evaluation, security, and accessibility tests run in CI
16. ✅ Demo works twice consecutively with provider-failure fallback
17. ✅ Public demo uses synthetic data with information-only disclaimer

---

## 12. MVP Cut Line (Priority Order)

If time is lost, preserve this order:

1. Secure upload
2. Native PDF extraction
3. Canonical pages and clauses
4. Dates and amounts
5. 2–3 high-value detectors
6. Evidence viewer
7. One grounded Q&A path
8. Timeline
9. Checklist
10. Disclaimer
11. Polished demo

**Cut before cutting evidence validation or ownership checks:**
- External legal RAG
- Broad taxonomy coverage
- Full authentication
- Comparison
- Multilingual UI
- Advanced NER
- Nonessential visualizations

> **The MVP is not complete if it only produces a summary. It must show where important output came from and what the system cannot verify.**
