# LegalLens — UI/UX Specification

**Version:** 1.0.0  
**Status:** Implementation-Ready  
**Last Updated:** 2026-09-23

---

## 1. Design Philosophy

### 1.1 Core Principles

| Principle | Implementation |
|-----------|---------------|
| **Trust through transparency** | Every AI-generated output links to source evidence |
| **Clarity over cleverness** | Plain language, no jargon, no unexplained scores |
| **Evidence first** | Findings always show "what the document says" before "what LegalLens generated" |
| **Safety is visible** | Disclaimers present at upload, results, and chat — not hidden in footnotes |
| **Accessibility is mandatory** | WCAG 2.2 AA compliance, keyboard-navigable, screen-reader friendly |

### 1.2 Visual Language

- **Professional and calm** — not alarmist. Legal documents are stressful; the interface should reduce anxiety.
- **No red as generic "legal danger" signal** — use text labels and icons with sufficient contrast
- **Three-layer visual distinction:**
  - 🔵 **Document Facts** — what the document says (primary, confident)
  - 🟣 **LegalLens Generated** — AI explanations & analysis (secondary, labeled)
  - 🟠 **External Context** — attributed external info (tertiary, clearly separated)

---

## 2. Design System

### 2.1 Color Palette

```css
:root {
  /* Primary — Trust & Authority */
  --color-primary-50:  #EEF2FF;
  --color-primary-100: #E0E7FF;
  --color-primary-200: #C7D2FE;
  --color-primary-500: #6366F1;
  --color-primary-600: #4F46E5;
  --color-primary-700: #4338CA;
  --color-primary-900: #312E81;

  /* Neutral — Text & Backgrounds */
  --color-neutral-50:  #F8FAFC;
  --color-neutral-100: #F1F5F9;
  --color-neutral-200: #E2E8F0;
  --color-neutral-300: #CBD5E1;
  --color-neutral-400: #94A3B8;
  --color-neutral-500: #64748B;
  --color-neutral-600: #475569;
  --color-neutral-700: #334155;
  --color-neutral-800: #1E293B;
  --color-neutral-900: #0F172A;

  /* Semantic — Severity (NOT red/green) */
  --color-attention:   #F59E0B;  /* Amber — needs attention */
  --color-important:   #8B5CF6;  /* Purple — important finding */
  --color-review:      #3B82F6;  /* Blue — needs review */
  --color-missing:     #6B7280;  /* Gray — information missing */
  --color-success:     #10B981;  /* Emerald — verified/complete */
  --color-error:       #EF4444;  /* Red — system errors only */

  /* Evidence Layers */
  --color-document-fact: #1E40AF;     /* Deep blue */
  --color-ai-generated:  #7C3AED;     /* Purple */
  --color-external:      #D97706;     /* Amber */

  /* Surfaces */
  --surface-base:      #FFFFFF;
  --surface-raised:    #F8FAFC;
  --surface-overlay:   rgba(15, 23, 42, 0.6);

  /* Dark Mode */
  --dark-surface-base:   #0F172A;
  --dark-surface-raised: #1E293B;
  --dark-text-primary:   #F1F5F9;
  --dark-text-secondary: #94A3B8;
}
```

### 2.2 Typography

```css
/* Font Stack */
--font-sans: 'Inter', 'system-ui', '-apple-system', 'Segoe UI', sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;

/* Scale */
--text-xs:   0.75rem;   /* 12px — Labels, captions */
--text-sm:   0.875rem;  /* 14px — Secondary text */
--text-base: 1rem;      /* 16px — Body text */
--text-lg:   1.125rem;  /* 18px — Lead text */
--text-xl:   1.25rem;   /* 20px — Section headers */
--text-2xl:  1.5rem;    /* 24px — Page headers */
--text-3xl:  1.875rem;  /* 30px — Hero text */
--text-4xl:  2.25rem;   /* 36px — Landing hero */

/* Weights */
--font-normal:   400;
--font-medium:   500;
--font-semibold: 600;
--font-bold:     700;

/* Line Heights */
--leading-tight:  1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.625;
```

### 2.3 Spacing & Layout

```css
/* Spacing Scale (4px base) */
--space-1:  0.25rem;   /* 4px */
--space-2:  0.5rem;    /* 8px */
--space-3:  0.75rem;   /* 12px */
--space-4:  1rem;      /* 16px */
--space-5:  1.25rem;   /* 20px */
--space-6:  1.5rem;    /* 24px */
--space-8:  2rem;      /* 32px */
--space-10: 2.5rem;    /* 40px */
--space-12: 3rem;      /* 48px */
--space-16: 4rem;      /* 64px */

/* Border Radius */
--radius-sm:  0.375rem;
--radius-md:  0.5rem;
--radius-lg:  0.75rem;
--radius-xl:  1rem;
--radius-full: 9999px;

/* Shadows */
--shadow-sm:  0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md:  0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg:  0 10px 15px -3px rgba(0, 0, 0, 0.1);
--shadow-xl:  0 20px 25px -5px rgba(0, 0, 0, 0.1);

/* Breakpoints */
--bp-sm:  640px;
--bp-md:  768px;
--bp-lg:  1024px;
--bp-xl:  1280px;
--bp-2xl: 1536px;

/* Container */
--container-max: 1280px;
--container-padding: var(--space-4);
```

### 2.4 Animation & Motion

```css
/* Transitions */
--transition-fast:   150ms ease;
--transition-base:   200ms ease;
--transition-slow:   300ms ease;
--transition-spring: 500ms cubic-bezier(0.34, 1.56, 0.64, 1);

/* Reduced Motion */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 3. Component Library

### 3.1 Core Components

| Component | Purpose | Key Props |
|-----------|---------|-----------|
| `Card` | Container for findings, facts, Q&A answers | `variant: 'default' \| 'finding' \| 'evidence'`, `severity?` |
| `Badge` | Status labels, severity indicators, source types | `variant`, `color`, `size` |
| `Tabs` | Section navigation (dashboard, viewer) | `items`, `activeTab`, `onChange` |
| `Button` | Actions | `variant: 'primary' \| 'secondary' \| 'ghost'`, `size`, `loading` |
| `Alert` | Disclaimers, warnings, system messages | `type: 'info' \| 'warning' \| 'disclaimer'` |
| `Skeleton` | Loading states | `variant: 'text' \| 'card' \| 'table'` |

### 3.2 Domain Components

| Component | Purpose | Key Props |
|-----------|---------|-----------|
| `EvidenceLink` | Clickable citation that navigates to source | `evidenceId`, `quote`, `pageNumber`, `clauseId` |
| `DocumentViewer` | Render pages with evidence highlights | `documentId`, `currentPage`, `highlights` |
| `FindingCard` | Single finding with severity, explanation, evidence | `finding`, `onEvidenceClick` |
| `TimelineView` | Visual timeline with date status labels | `events`, `onEventClick` |
| `ClauseCard` | Clause text with type badge and evidence | `clause`, `entities` |
| `ChatMessage` | Q&A message with citations and limitations | `message`, `role`, `citations` |
| `ChecklistItem` | Preparation task with reason and evidence | `item`, `onToggle` |
| `Disclaimer` | Legal information disclaimer | `variant: 'banner' \| 'inline' \| 'modal'` |
| `ProcessingStage` | Named stage with status and timing | `stage`, `status`, `elapsed` |
| `SeverityBadge` | Transparent severity label (text + icon) | `severity`, `showLabel` |
| `SourceTypeBadge` | Document fact / Generated / External label | `sourceType` |
| `PageNavigator` | Page-level navigation in document viewer | `pageCount`, `currentPage` |

### 3.3 Component Guidelines

- **Semantic HTML first** — use `<button>`, `<nav>`, `<main>`, `<article>`, `<section>`, never clickable `<div>`
- **Visible focus rings** on all interactive elements
- **Loading, error, partial, and empty states** for every data-driven component
- **Keyboard operable** — all interactions accessible via keyboard
- **ARIA labels** — only where semantic HTML is insufficient
- **aria-live regions** — for processing status updates

---

## 4. Page Specifications

### 4.1 Landing Page (`/`)

**Purpose:** Communicate the problem, positioning, evidence-linking, and call to action.

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  Logo    [Try LegalLens]                         │
├─────────────────────────────────────────────────┤
│                                                  │
│  "Understand your legal documents               │
│   with evidence-linked AI"                      │
│                                                  │
│  [Upload a Document →]                          │
│                                                  │
│  • Not an AI lawyer — an information tool       │
│  • Every finding links to source evidence       │
│  • Your documents are processed privately       │
│                                                  │
├─────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │Understand│  │ Protect  │  │   Act    │      │
│  │          │  │          │  │          │      │
│  │ Extract  │  │ Detect   │  │ Prepare  │      │
│  │ facts    │  │ risks    │  │ actions  │      │
│  └──────────┘  └──────────┘  └──────────┘      │
├─────────────────────────────────────────────────┤
│  How it works: Upload → Analyze → Act           │
│  Evidence example: [interactive demo]           │
├─────────────────────────────────────────────────┤
│  Privacy • Accepted formats • Disclaimer        │
└─────────────────────────────────────────────────┘
```

**Key elements:**
- Hero with gradient background (primary-500 → primary-700)
- Animated evidence-link demonstration
- Three-column mode cards with micro-animations
- Glassmorphism card effects on hover
- Privacy-forward messaging above the fold

### 4.2 Upload Page (`/upload`)

**Purpose:** Privacy-forward file upload with clear constraints.

```
┌─────────────────────────────────────────────────┐
│  ← Back      Upload a Document                   │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐  │
│  │                                           │  │
│  │     📄  Drop your file here               │  │
│  │         or click to browse                │  │
│  │                                           │  │
│  │     PDF or DOCX • Max 20 MB              │  │
│  │                                           │  │
│  └─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘  │
│                                                  │
│  ⚠️  Do not upload material you are not          │
│      authorized to share                         │
│                                                  │
│  🔒 Your document is processed privately and     │
│     automatically deleted after 24 hours         │
│                                                  │
│  ℹ️  LegalLens is an information tool, not       │
│     a legal advisor. AI can make mistakes.       │
│                                                  │
│  [Analyze Document →]                            │
└─────────────────────────────────────────────────┘
```

**Interactions:**
- Drag-and-drop zone with visual feedback
- Client-side validation (size, extension) before upload
- Progress bar during upload
- Clear error messages for rejected files
- Disclaimer always visible

### 4.3 Processing Page (`/documents/[id]/processing`)

**Purpose:** Show named stages with real progress — not a vague spinner.

```
┌─────────────────────────────────────────────────┐
│  Analyzing: notice.pdf                           │
├─────────────────────────────────────────────────┤
│                                                  │
│  ✅ Validating file               0.3s          │
│  ✅ Extracting pages              1.2s          │
│  ✅ Identifying clauses           2.1s          │
│  🔄 Checking dates and amounts    ...           │
│  ○  Building evidence index                      │
│  ○  Generating explanations                      │
│  ○  Verifying citations                          │
│                                                  │
│  ─────────────────────────── 57%                │
│                                                  │
│  ℹ️  You can view partial results while          │
│     analysis continues                           │
│                                                  │
│  [View Partial Results]                          │
└─────────────────────────────────────────────────┘
```

**Behaviors:**
- Stages animate in sequentially
- Completed stages show ✅ + elapsed time
- Active stage shows spinner + "..."
- Failed stage shows ⚠️ + error name + "Retry" option
- Poll via SSE or status endpoint
- `aria-live` announcements for stage changes
- Auto-redirect to dashboard on completion

### 4.4 Dashboard Page (`/documents/[id]/dashboard`)

**Purpose:** The Legal Situation Map — first viewport contains the most important information.

```
┌─────────────────────────────────────────────────┐
│  Legal Situation Map         [Ask LegalLens 💬]  │
├─────────────────────────────────────────────────┤
│                                                  │
│  📄 Legal Notice • 3 pages • en                 │
│  Between: ABC Properties (landlord)              │
│       and: John Smith (tenant)                   │
│  Date: September 15, 2026                        │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │ "A payment demand for ₹75,000 with a    │    │
│  │  15-day response deadline and a 30-day  │    │
│  │  termination notice provision."          │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
├──── Attention Items ────────────────────────────┤
│                                                  │
│  ┌──────────────────────────────────────┐       │
│  │ ⚠️ IMPORTANT                          │       │
│  │ 15-day response deadline              │       │
│  │ "...respond within fifteen days..."   │       │
│  │ Page 2 • Clause 3.1  [View Source →]  │       │
│  │                                       │       │
│  │ Why: Deadline creates a time-bound    │       │
│  │ obligation requiring prompt action    │       │
│  │                                       │       │
│  │ ⚪ Cannot determine: Whether this     │       │
│  │ deadline has legal consequences if    │       │
│  │ missed                                │       │
│  └──────────────────────────────────────┘       │
│                                                  │
│  ┌──────────────────────────────────────┐       │
│  │ 🔍 NEEDS REVIEW                       │       │
│  │ 30-day termination notice period      │       │
│  │ Page 2 • Clause 4.1  [View Source →]  │       │
│  └──────────────────────────────────────┘       │
│                                                  │
├──── Timeline ───────────────────────────────────┤
│                                                  │
│  ●─────●─────●─────○                            │
│  Sep 15  Sep 30  Oct 15                          │
│  Notice  Response  Notice                        │
│  Date    Deadline  Period                        │
│  EXPLICIT DERIVED  DERIVED                       │
│                                                  │
├──── Obligations ────────────────────────────────┤
│  • Pay ₹75,000 (Page 1)                         │
│  • Respond within 15 days (Page 2)               │
│                                                  │
├──── Missing Information ────────────────────────┤
│  • Referenced lease agreement not provided        │
│  • Payment receipt history not available          │
│                                                  │
├──── Prepare ────────────────────────────────────┤
│  [📋 Preparation Checklist]                      │
│  [❓ Questions for a Legal Professional]         │
│                                                  │
├─────────────────────────────────────────────────┤
│  ℹ️  This analysis is based on the supplied      │
│  document. AI can make mistakes. Consult a       │
│  qualified legal professional for advice.        │
└─────────────────────────────────────────────────┘
```

**First Viewport MUST contain:**
1. Document type, parties, duration, key dates
2. One-sentence situation snapshot
3. Important items with transparent severity labels
4. Timeline preview
5. Obligations and missing information
6. "Ask LegalLens" and "Prepare for a professional" actions

### 4.5 Document Viewer (`/documents/[id]/viewer`)

**Purpose:** View original document pages with evidence highlights.

**Desktop — Two-Pane Layout:**
```
┌─────────────────────┬──────────────────────────┐
│  Document Viewer     │  Evidence Panel           │
├─────────────────────┤                            │
│                      │  Clause 4.1: Termination  │
│  ┌───────────────┐  │  ─────────────────────     │
│  │               │  │  "The tenant may           │
│  │   Page 2      │  │   terminate by giving      │
│  │               │  │   thirty days' written     │
│  │  ┌─────────┐  │  │   notice."                │
│  │  │HIGHLIGHT│  │  │                            │
│  │  │ clause  │  │  │  Type: TERMINATION         │
│  │  │ 4.1     │  │  │  Confidence: 94%           │
│  │  └─────────┘  │  │                            │
│  │               │  │  Related Findings:         │
│  │               │  │  • 30-day notice period    │
│  └───────────────┘  │  • Asymmetric termination  │
│                      │                            │
│  ◀ Page 1  Page 2  Page 3 ▶                      │
│  [Zoom +] [Zoom -] [Fit]  │                     │
└─────────────────────┴──────────────────────────┘
```

**Mobile — Stacked Layout:**
```
┌─────────────────────────────┐
│  Document Viewer    ◀ ▶      │
├─────────────────────────────┤
│  ┌───────────────────────┐  │
│  │      Page 2           │  │
│  │  ┌─────────────────┐  │  │
│  │  │   HIGHLIGHTED    │  │  │
│  │  │   CLAUSE 4.1     │  │  │
│  │  └─────────────────┘  │  │
│  └───────────────────────┘  │
├─────────────────────────────┤
│  ▼ Evidence Details          │
│  "The tenant may terminate   │
│   by giving thirty days'..." │
│  [View Finding →]            │
└─────────────────────────────┘
```

### 4.6 Chat Page (`/documents/[id]/chat`)

```
┌─────────────────────────────────────────────────┐
│  Ask LegalLens about this document               │
├─────────────────────────────────────────────────┤
│                                                  │
│  ℹ️ Answers are based only on your uploaded      │
│  document. LegalLens may make mistakes.          │
│                                                  │
│  ┌──────────────────────────────────────┐       │
│  │ 🧑 What happens if I terminate early?│       │
│  └──────────────────────────────────────┘       │
│                                                  │
│  ┌──────────────────────────────────────┐       │
│  │ 🤖 Based on the document:            │       │
│  │                                       │       │
│  │ 🔵 DOCUMENT SAYS:                     │       │
│  │ "The tenant may terminate by giving   │       │
│  │  thirty days' written notice."        │       │
│  │  📌 Page 2, Clause 4.1               │       │
│  │                                       │       │
│  │ 🟣 LEGALLENS ANALYSIS:                │       │
│  │ This clause appears to allow early    │       │
│  │ termination with a 30-day written     │       │
│  │ notice period.                        │       │
│  │                                       │       │
│  │ ⚪ LIMITATION:                         │       │
│  │ The referenced lease agreement was    │       │
│  │ not provided. Additional termination  │       │
│  │ conditions may exist in that document.│       │
│  │                                       │       │
│  │ 📎 Evidence: [View Source →]           │       │
│  └──────────────────────────────────────┘       │
│                                                  │
│  ┌──────────────────────────────────────┐       │
│  │ Ask about this document...     [Send] │       │
│  └──────────────────────────────────────┘       │
│                                                  │
│  Suggested: "What are my payment obligations?"   │
│             "When is the response deadline?"     │
└─────────────────────────────────────────────────┘
```

### 4.7 Checklist Page (`/documents/[id]/checklist`)

```
┌─────────────────────────────────────────────────┐
│  Preparation Checklist                           │
├─────────────────────────────────────────────────┤
│                                                  │
│  ☐ Gather payment records for ₹75,000 demand    │
│    Reason: Document references unpaid rent       │
│    📎 Page 1, Clause 2.1                         │
│                                                  │
│  ☐ Note the 15-day response deadline             │
│    Reason: Time-bound obligation                 │
│    📎 Page 2, Clause 3.1                         │
│                                                  │
│  ☐ Locate referenced lease agreement             │
│    Reason: Document references terms not         │
│    included in this notice                       │
│    📎 Page 3                                     │
│                                                  │
│  ☐ Review 30-day termination notice provision    │
│    Reason: Affects your exit options             │
│    📎 Page 2, Clause 4.1                         │
│                                                  │
├──── Questions for a Legal Professional ─────────┤
│                                                  │
│  1. "Does the 15-day deadline in this notice     │
│      have specific legal consequences if         │
│      missed?"                                    │
│     Reason: The notice implies urgency but does  │
│     not specify consequences.                    │
│                                                  │
│  2. "Are there additional termination            │
│      conditions in the referenced lease that     │
│      affect this notice?"                        │
│     Reason: The lease was not provided for       │
│     analysis.                                    │
│                                                  │
│  [Export as PDF]  [Copy to Clipboard]             │
└─────────────────────────────────────────────────┘
```

### 4.8 Timeline Page (`/documents/[id]/timeline`)

```
┌─────────────────────────────────────────────────┐
│  Document Timeline                               │
├─────────────────────────────────────────────────┤
│                                                  │
│  ●═══════════●═══════════●═══════════○          │
│  │            │            │            │        │
│  Sep 15      Sep 30       Oct 15       Oct 15   │
│                                                  │
│  ┌────────┐  ┌────────┐   ┌────────┐            │
│  │Notice  │  │Response│   │Notice  │            │
│  │Date    │  │Deadline│   │Period  │            │
│  │        │  │        │   │Ends    │            │
│  │EXPLICIT│  │DERIVED │   │DERIVED │            │
│  │📎 Pg 1 │  │📎 Pg 2 │   │📎 Pg 2 │            │
│  └────────┘  └────────┘   └────────┘            │
│                                                  │
│  📊 Calculation: Sep 15 + 15 days = Sep 30      │
│  📊 Calculation: Sep 15 + 30 days = Oct 15      │
│                                                  │
│  ⚪ Note: "Within 30 days of receipt" — the      │
│  exact receipt date is not stated in the         │
│  document. Dates shown use the notice date       │
│  as the assumed starting point.                  │
└─────────────────────────────────────────────────┘
```

---

## 5. Finding Card Anatomy

Every finding card MUST include four sections:

```
┌──────────────────────────────────────────────┐
│  ⚠️ SEVERITY_LABEL                            │
│  Finding Title                               │
├──────────────────────────────────────────────┤
│                                              │
│  WHY THIS IS SHOWN:                          │
│  Explanation of why this clause deserves      │
│  attention, in plain language.               │
│                                              │
│  EVIDENCE:                                   │
│  "Exact quote from the document..."          │
│  📌 Page X, Clause Y.Z   [View Source →]     │
│                                              │
│  WHAT LEGALLENS CANNOT DETERMINE:            │
│  What aspects cannot be verified from this   │
│  document alone.                             │
│                                              │
│  [View on Original Page →]                   │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 6. Responsive Strategy

| Breakpoint | Layout |
|------------|--------|
| Mobile (< 768px) | Single column, stacked viewer, collapsible sections |
| Tablet (768–1024px) | Two-column dashboard, side-by-side viewer |
| Desktop (> 1024px) | Full two-pane viewer, expanded dashboard |

### Key Responsive Behaviors

- **Dashboard:** Cards stack vertically on mobile; 2-column grid on tablet+
- **Document Viewer:** Stacked (page above, evidence below) on mobile; side-by-side on desktop
- **Timeline:** Vertical on mobile; horizontal on desktop
- **Chat:** Full-width on all sizes; input fixed at bottom on mobile
- **Navigation:** Bottom nav on mobile; sidebar on desktop

---

## 7. Accessibility Specification (WCAG 2.2 AA)

### 7.1 Mandatory Requirements

| Requirement | Implementation |
|-------------|---------------|
| Semantic headings | h1 per page, proper hierarchy |
| Landmarks | `<nav>`, `<main>`, `<aside>`, `<footer>` |
| Buttons not divs | All interactive elements are `<button>` or `<a>` |
| Visible focus | 2px outline, offset, high contrast ring |
| Skip link | "Skip to main content" as first focusable element |
| Keyboard tabs | Tab, Shift+Tab, Enter, Space, Arrow keys |
| `aria-live` | Processing status announcements |
| Text + icon | Severity uses text label + icon, never color alone |
| High contrast | 4.5:1 minimum contrast ratio |
| Scalable text | Renders correctly at 200% zoom |
| Reduced motion | Respects `prefers-reduced-motion` |
| Screen reader | All images have alt text; decorative images hidden |

### 7.2 Keyboard Navigation Flow

```
Skip Link → Navigation → Main Content → Evidence Links → Side Panel
     ↕           ↕            ↕              ↕              ↕
   Enter      Tab/Arrow     Tab/Enter      Tab/Enter     Tab/Arrow
```

**Evidence navigation:** From finding card → Tab to "View Source" → Enter opens viewer → Focus moves to highlighted clause → Escape returns to finding.

---

## 8. Interaction Patterns

### 8.1 Evidence Click Path

```
User clicks evidence link → Viewer opens at page → Scrolls to clause
    → Overlays bounding box (if coordinates available)
    → OR highlights matched text + shows quote in side panel
    → User can navigate to next/previous evidence
```

### 8.2 Processing Updates

```
API polling (or SSE) → Stage completion → 
    ✅ icon + elapsed time animates in → 
    Next stage starts → 
    aria-live announces: "Stage 4 of 7 complete: Checking dates and amounts"
```

### 8.3 Q&A Interaction

```
User types question → Send button enabled → 
    Loading state with typing indicator → 
    Answer streams in with citations → 
    Citations are clickable evidence links → 
    Limitations shown after answer → 
    Suggested follow-ups appear
```

### 8.4 Error States

```
┌──────────────────────────────────────────────┐
│  ⚠️ AI explanation unavailable                │
│                                              │
│  The explanation could not be generated.     │
│  Source facts and evidence remain available.  │
│                                              │
│  [Retry] [View Source Facts Only]            │
└──────────────────────────────────────────────┘
```

---

## 9. 3-Minute Demo Flow

### Timing

| Time | Action | What's Visible |
|------|--------|---------------|
| 0:00–0:20 | Problem statement | Landing page with value proposition |
| 0:20–0:45 | Positioning | "Not an AI lawyer — evidence-linked information tool" |
| 0:45–1:35 | Live upload | Upload → processing stages → dashboard with findings |
| 1:35–2:15 | Grounded Q&A | "What happens if I terminate early?" → cited answer + limitation |
| 2:15–2:40 | Action layer | Timeline → missing info → checklist → professional questions |
| 2:40–3:00 | Differentiation | Source labels, injection defense, privacy, evaluation metrics |

### Key Demo Interactions

1. Upload synthetic notice → show privacy boundary
2. Show processing stages with actual timing
3. Open Situation Map → point out parties, deadline, payment
4. Click "30-day termination notice" finding
5. Show original page with clause highlighted and exact quote
6. Open timeline → distinguish explicit vs derived dates
7. Ask "What happens if I terminate early?"
8. Show grounded answer with citation and missing-lease limitation
9. Open preparation checklist and professional questions
10. Show prompt-injection test or privacy panel

### Fallback Path

If model provider is unavailable:
- Deterministic findings remain visible
- Prevalidated cached analysis available
- Message: "AI explanation unavailable; source facts remain available"
- Reset-demo control: deletes synthetic document and reloads from fixture

---

## 10. Dark Mode

Support system-preference dark mode with manual toggle.

| Element | Light Mode | Dark Mode |
|---------|-----------|-----------|
| Background | `#FFFFFF` | `#0F172A` |
| Surface | `#F8FAFC` | `#1E293B` |
| Text primary | `#0F172A` | `#F1F5F9` |
| Text secondary | `#475569` | `#94A3B8` |
| Border | `#E2E8F0` | `#334155` |
| Cards | White + shadow | Raised surface + subtle border |
| Evidence highlight | Yellow overlay 20% | Yellow overlay 15% |

---

## 11. Loading States

Every data-driven view has explicit loading, error, partial, and empty states:

| State | Pattern |
|-------|---------|
| **Loading** | Skeleton UI matching the layout shape |
| **Error** | Error card with retry action and fallback suggestion |
| **Partial** | Available data shown; unavailable sections labeled with progress |
| **Empty** | Helpful message explaining what's expected (never blank) |
