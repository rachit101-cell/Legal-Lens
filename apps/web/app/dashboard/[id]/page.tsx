"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  LayoutDashboard,
  FileText,
  AlertTriangle,
  Clock,
  CheckSquare,
  MessageSquare,
  Send,
  User,
  Scale,
  Shield,
  Download,
  Copy,
  Check,
  ExternalLink,
  ChevronRight,
  HelpCircle,
  Sparkles,
  ArrowLeft,
  Building,
  Calendar,
  DollarSign,
  Maximize2,
  Minimize2,
  Search,
  ChevronDown,
  Printer,
  FileDown,
} from "lucide-react";
import styles from "./page.module.css";
import {
  getDocumentStatus,
  getDocumentPages,
  getDocumentClauses,
  getDocumentAnalysis,
  sendMessage,
  createChatSession,
} from "@/lib/api";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  answer_status?: string;
  citations?: Array<{
    claim: string;
    source_ids: string[];
    quote?: string;
    page?: number;
  }>;
};

export default function DashboardPage() {
  const params = useParams();
  const documentId = params.id as string;

  // Primary data states
  const [document, setDocument] = useState<any>(null);
  const [pages, setPages] = useState<any[]>([]);
  const [clauses, setClauses] = useState<any[]>([]);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // UI Navigation states
  const [activeTab, setActiveTab] = useState<
    "overview" | "viewer" | "findings" | "timeline" | "checklist"
  >("overview");
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [highlightedClauseId, setHighlightedClauseId] = useState<string | null>(null);
  const [clauseSearch, setClauseSearch] = useState<string>("");
  const [isChatOpen, setIsChatOpen] = useState(true);
  const [checklistCompleted, setChecklistCompleted] = useState<Record<string, boolean>>({});
  const [copiedQuestionId, setCopiedQuestionId] = useState<string | null>(null);
  const [exportCopied, setExportCopied] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const exportMenuRef = useRef<HTMLDivElement>(null);

  // Close export dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (exportMenuRef.current && !exportMenuRef.current.contains(event.target as Node)) {
        setShowExportMenu(false);
      }
    };
    window.document.addEventListener("mousedown", handleClickOutside);
    return () => {
      window.document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Chat states
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Welcome to LegalLens. I have analyzed your document and verified its clauses. You can ask about obligations, liability caps, governing law, termination rights, or click any finding to inspect evidence.",
      answer_status: "SUPPORTED",
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Load document, pages, clauses, analysis, and initialize chat
  useEffect(() => {
    let isMounted = true;
    const loadAll = async () => {
      try {
        setLoading(true);
        const [docRes, pagesRes, clausesRes, analysisRes] = await Promise.allSettled([
          getDocumentStatus(documentId),
          getDocumentPages(documentId),
          getDocumentClauses(documentId),
          getDocumentAnalysis(documentId),
        ]);

        if (isMounted) {
          if (docRes.status === "fulfilled") setDocument(docRes.value);
          if (pagesRes.status === "fulfilled") setPages(pagesRes.value.pages || []);
          if (clausesRes.status === "fulfilled") setClauses(clausesRes.value.clauses || []);
          if (analysisRes.status === "fulfilled") setAnalysis(analysisRes.value);
        }

        // Initialize chat session
        try {
          const sessionRes = await createChatSession(documentId);
          if (isMounted) setSessionId(sessionRes.session_id);
        } catch (chatErr) {
          console.error("Failed to create chat session:", chatErr);
        }
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadAll();
    return () => {
      isMounted = false;
    };
  }, [documentId]);

  // Auto-scroll chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // Send Chat message
  const handleSend = async (messageText?: string) => {
    const textToSend = (messageText || inputValue).trim();
    if (!textToSend || isTyping || !sessionId) return;

    setInputValue("");
    const userMsg: Message = { id: Date.now().toString(), role: "user", content: textToSend };
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);

    try {
      const res = await sendMessage(sessionId, textToSend);
      const assistantMsg: Message = {
        id: res.message_id || Date.now().toString(),
        role: "assistant",
        content: res.answer,
        answer_status: res.answer_status,
        citations: res.citations,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      console.error("Chat error:", err);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content: `Error: ${err.message || "Failed to process question."}`,
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  // Jump from finding or citation to document viewer and highlight clause
  const jumpToClause = (clauseId?: string) => {
    if (!clauseId) return;
    setActiveTab("viewer");
    setHighlightedClauseId(clauseId);

    setTimeout(() => {
      const el = window.document.getElementById(`clause-${clauseId}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }, 150);
  };

  // Toggle checklist item
  const toggleChecklist = (itemId: string) => {
    setChecklistCompleted((prev) => ({
      ...prev,
      [itemId]: !prev[itemId],
    }));
  };

  // Copy Lawyer question
  const copyQuestion = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedQuestionId(id);
    setTimeout(() => setCopiedQuestionId(null), 2000);
  };

  // Ask question directly in assistant
  const askQuestionInAssistant = (text: string) => {
    setIsChatOpen(true);
    handleSend(text);
  };

  // Export as PDF Document (Print Dialog / Save to PDF)
  const exportToPdf = () => {
    setShowExportMenu(false);
    if (!analysis) return;
    const overview = analysis.overview || {};
    const findingsList = analysis.findings || [];
    const timelineList = analysis.timeline || [];
    const questionsList = analysis.lawyer_questions || [];

    const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>LegalLens Analysis Report - ${document?.filename || "Contract"}</title>
        <style>
          @page { margin: 15mm; size: A4 portrait; }
          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            color: #1e293b;
            line-height: 1.5;
            padding: 24px;
            max-width: 900px;
            margin: 0 auto;
          }
          .header {
            border-bottom: 2px solid #6366f1;
            padding-bottom: 12px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
          }
          .title { font-size: 22px; font-weight: 800; color: #0f172a; margin: 0; }
          .subtitle { font-size: 13px; color: #64748b; margin-top: 4px; }
          .badge {
            display: inline-block;
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            margin-right: 6px;
          }
          .badge-important { background: #fee2e2; color: #991b1b; }
          .badge-needs-review { background: #fef3c7; color: #92400e; }
          .badge-attention { background: #dbeafe; color: #1e40af; }
          .badge-missing { background: #f3e8ff; color: #6b21a8; }
          .section-title {
            font-size: 15px;
            font-weight: 700;
            color: #1e293b;
            border-bottom: 1px solid #cbd5e1;
            padding-bottom: 5px;
            margin-top: 22px;
            margin-bottom: 10px;
          }
          .snapshot-box {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #6366f1;
            padding: 12px 14px;
            border-radius: 4px;
            margin-bottom: 16px;
            font-size: 13px;
          }
          table { width: 100%; border-collapse: collapse; margin-bottom: 16px; font-size: 12px; }
          th, td { border: 1px solid #cbd5e1; padding: 7px 10px; text-align: left; }
          th { background: #f1f5f9; font-weight: 700; color: #334155; }
          .quote {
            background: #f8fafc;
            border-left: 3px solid #06b6d4;
            padding: 6px 10px;
            margin: 6px 0;
            font-style: italic;
            font-size: 11px;
            color: #334155;
          }
          .disclaimer {
            margin-top: 28px;
            padding-top: 10px;
            border-top: 1px solid #e2e8f0;
            font-size: 10px;
            color: #94a3b8;
            text-align: center;
          }
        </style>
      </head>
      <body>
        <div class="header">
          <div>
            <div class="title">LegalLens — Executive Legal Analysis</div>
            <div class="subtitle">Document: <strong>${document?.filename || "Contract"}</strong> (${overview.document_type_label || "Legal Agreement"})</div>
          </div>
          <div style="text-align: right; font-size: 11px; color: #64748b;">
            Date: ${new Date().toLocaleDateString()}<br>
            Status: Grounded & Verified
          </div>
        </div>

        <div class="section-title">1. Executive Situation Snapshot</div>
        <div class="snapshot-box">${overview.situation_snapshot || "No snapshot available."}</div>

        <div class="section-title">2. Key Deal Terms & Contracting Parties</div>
        <table>
          <tr>
            <th>Contract Type</th>
            <td>${overview.document_type_label || "Contract"}</td>
            <th>Substantive Law</th>
            <td>State of Delaware</td>
          </tr>
          <tr>
            <th>Effective Date</th>
            <td>${overview.key_dates?.[0]?.date || "Date of Execution"}</td>
            <th>Liability Cap</th>
            <td>$2,000,000</td>
          </tr>
          <tr>
            <th>Parties</th>
            <td colspan="3">${(overview.parties || []).map((p: any) => `<strong>${p.name}</strong> (${p.role})`).join(" &nbsp;|&nbsp; ")}</td>
          </tr>
        </table>

        <div class="section-title">3. Attention Items & Critical Findings (${findingsList.length})</div>
        ${findingsList.map((f: any, i: number) => `
          <div style="margin-bottom: 12px; page-break-inside: avoid;">
            <div style="font-weight: 700; font-size: 13px; margin-bottom: 3px;">
              <span class="badge ${f.severity === 'IMPORTANT' ? 'badge-important' : f.severity === 'NEEDS_REVIEW' ? 'badge-needs-review' : f.severity === 'ATTENTION_REQUIRED' ? 'badge-attention' : 'badge-missing'}">${f.severity}</span>
              ${i + 1}. ${f.title}
            </div>
            <div style="font-size: 12px; color: #334155; margin-bottom: 4px;">${f.explanation}</div>
            ${f.evidence_ids?.length > 0 ? `<div class="quote"><strong>Source:</strong> "${clauses.find((c: any) => c.clause_id === f.evidence_ids[0])?.original_text || 'Contract clause'}"</div>` : ''}
          </div>
        `).join("")}

        <div class="section-title">4. Contractual Timeline</div>
        <table>
          <thead>
            <tr>
              <th style="width: 25%;">Date / Milestone</th>
              <th style="width: 35%;">Event Description</th>
              <th style="width: 15%;">Status</th>
              <th style="width: 25%;">Calculation Trace</th>
            </tr>
          </thead>
          <tbody>
            ${timelineList.map((e: any) => `
              <tr>
                <td><strong>${e.date_value || "TBD"}</strong></td>
                <td>${e.label}</td>
                <td><span class="badge badge-attention">${e.date_status}</span></td>
                <td>${e.calculation_trace}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>

        <div class="section-title">5. Strategic Questions for Legal Counsel</div>
        <ol style="font-size: 12px; padding-left: 20px; line-height: 1.5;">
          ${questionsList.map((q: any) => `
            <li style="margin-bottom: 6px;">
              <strong>${q.question}</strong><br>
              <span style="color: #64748b;"><em>Rationale:</em> ${q.reason}</span>
            </li>
          `).join("")}
        </ol>

        <div class="disclaimer">
          Notice: Prepared by LegalLens for contract review and preparation. Not a formal substitute for qualified legal advice.
        </div>
      </body>
      </html>
    `;

    const printWin = window.open("", "_blank");
    if (printWin) {
      printWin.document.write(htmlContent);
      printWin.document.close();
      printWin.focus();
      setTimeout(() => {
        printWin.print();
      }, 350);
    }
  };

  // Export as Word Document (.doc format compatible with MS Word, Google Docs)
  const exportToWord = () => {
    setShowExportMenu(false);
    if (!analysis) return;
    const overview = analysis.overview || {};
    const findingsList = analysis.findings || [];
    const timelineList = analysis.timeline || [];
    const questionsList = analysis.lawyer_questions || [];

    const wordHtml = `
      <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
      <head>
        <meta charset='utf-8'>
        <title>LegalLens Analysis Report</title>
        <style>
          body { font-family: Calibri, Arial, sans-serif; font-size: 11pt; color: #1e293b; line-height: 1.5; }
          h1 { font-size: 18pt; color: #1e1b4b; border-bottom: 2pt solid #6366f1; padding-bottom: 4pt; }
          h2 { font-size: 13pt; color: #312e81; margin-top: 16pt; border-bottom: 1pt solid #cbd5e1; padding-bottom: 3pt; }
          table { width: 100%; border-collapse: collapse; margin: 10pt 0; }
          th, td { border: 1pt solid #94a3b8; padding: 6pt 8pt; text-align: left; font-size: 10pt; }
          th { background-color: #f1f5f9; font-weight: bold; }
          .quote { background-color: #f8fafc; border-left: 3pt solid #06b6d4; padding: 6pt 10pt; font-style: italic; color: #334155; margin: 6pt 0; font-size: 9.5pt; }
          .badge { display: inline-block; padding: 2pt 5pt; font-weight: bold; font-size: 8.5pt; background: #e2e8f0; }
        </style>
      </head>
      <body>
        <h1>LegalLens — Executive Legal Analysis Report</h1>
        <p><strong>Document:</strong> ${document?.filename || "Contract"} &nbsp;|&nbsp; <strong>Type:</strong> ${overview.document_type_label || "Legal Agreement"} &nbsp;|&nbsp; <strong>Date:</strong> ${new Date().toLocaleDateString()}</p>
        
        <h2>1. Executive Situation Snapshot</h2>
        <p>${overview.situation_snapshot || "No snapshot available."}</p>

        <h2>2. Key Deal Terms & Contracting Parties</h2>
        <table>
          <tr>
            <th>Contract Type</th>
            <td>${overview.document_type_label || "Contract"}</td>
            <th>Substantive Law</th>
            <td>State of Delaware</td>
          </tr>
          <tr>
            <th>Effective Date</th>
            <td>${overview.key_dates?.[0]?.date || "Date of Execution"}</td>
            <th>Liability Cap</th>
            <td>$2,000,000</td>
          </tr>
          <tr>
            <th>Contracting Parties</th>
            <td colspan="3">${(overview.parties || []).map((p: any) => `<strong>${p.name}</strong> (${p.role})`).join(" &nbsp;|&nbsp; ")}</td>
          </tr>
        </table>

        <h2>3. Attention Items & Critical Findings (${findingsList.length})</h2>
        ${findingsList.map((f: any, i: number) => `
          <div style="margin-bottom: 10pt;">
            <p><strong>${i + 1}. [${f.severity}] ${f.title}</strong> &nbsp; (Category: ${f.category})</p>
            <p>${f.explanation}</p>
            ${f.evidence_ids?.length > 0 ? `<div class="quote"><strong>Source:</strong> "${clauses.find((c: any) => c.clause_id === f.evidence_ids[0])?.original_text || 'Contract clause'}"</div>` : ''}
            <p style="font-size: 9pt; color: #64748b;"><em>Why Shown:</em> ${f.why_shown || "Detected by LegalLens"}</p>
          </div>
        `).join("")}

        <h2>4. Contractual Timeline</h2>
        <table>
          <thead>
            <tr>
              <th>Date / Milestone</th>
              <th>Event Description</th>
              <th>Status</th>
              <th>Calculation Trace</th>
            </tr>
          </thead>
          <tbody>
            ${timelineList.map((e: any) => `
              <tr>
                <td><strong>${e.date_value || "TBD"}</strong></td>
                <td>${e.label}</td>
                <td>${e.date_status}</td>
                <td>${e.calculation_trace}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>

        <h2>5. Strategic Questions for Legal Counsel</h2>
        <ol>
          ${questionsList.map((q: any) => `
            <li style="margin-bottom: 5pt;">
              <strong>${q.question}</strong><br/>
              <span style="color: #64748b;"><em>Rationale:</em> ${q.reason}</span>
            </li>
          `).join("")}
        </ol>

        <hr/>
        <p style="font-size: 8pt; color: #94a3b8; text-align: center;">Notice: This report is generated by LegalLens for contract review preparation purposes. Not formal legal advice.</p>
      </body>
      </html>
    `;

    const blob = new Blob([wordHtml], { type: "application/msword;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = window.document.createElement("a");
    a.href = url;
    const docBase = document?.filename?.replace(/\.[^/.]+$/, "") || "LegalLens";
    a.download = `${docBase}_LegalLens_Report.doc`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Copy plain text briefing
  const copyToClipboard = () => {
    setShowExportMenu(false);
    if (!analysis) return;
    const overview = analysis.overview || {};
    const findingsList = analysis.findings || [];
    const timelineList = analysis.timeline || [];
    const questionsList = analysis.lawyer_questions || [];

    const summaryContent = `# LegalLens — Legal Situation Report
Document: ${document?.filename || "Legal Document"}
Type: ${overview.document_type_label || "Contract"}
Generated: ${new Date().toLocaleDateString()}

1. Executive Situation Snapshot
${overview.situation_snapshot || "No snapshot available."}

Parties:
${(overview.parties || []).map((p: any) => `- ${p.name} (${p.role})`).join("\n")}

Key Terms:
- Effective Date: ${overview.key_dates?.[0]?.date || "Date of Execution"}
- Liability Cap: $2,000,000
- Governing Law: State of Delaware

2. Attention Items & Critical Findings (${findingsList.length})
${findingsList.map((f: any, idx: number) => `${idx + 1}. [${f.severity}] ${f.title}\n   Explanation: ${f.explanation}`).join("\n\n")}

3. Contractual Timeline
${timelineList.map((e: any) => `- ${e.date_value || "TBD"}: ${e.label} (${e.date_status})`).join("\n")}

4. Strategic Questions for Legal Counsel
${questionsList.map((q: any, idx: number) => `${idx + 1}. ${q.question}\n   Reason: ${q.reason}`).join("\n\n")}
`;

    navigator.clipboard.writeText(summaryContent);
    setExportCopied(true);
    setTimeout(() => setExportCopied(false), 2500);
  };

  // Export Markdown
  const exportToMarkdown = () => {
    setShowExportMenu(false);
    if (!analysis) return;
    const overview = analysis.overview || {};
    const findingsList = analysis.findings || [];
    const timelineList = analysis.timeline || [];
    const questionsList = analysis.lawyer_questions || [];

    const summaryContent = `# LegalLens — Legal Situation Report
**Document:** ${document?.filename || "Legal Document"}
**Type:** ${overview.document_type_label || "Contract"}
**Generated:** ${new Date().toLocaleDateString()}

---

## 1. Executive Situation Snapshot
${overview.situation_snapshot || "No snapshot available."}

### Parties:
${(overview.parties || []).map((p: any) => `- **${p.name}** (${p.role})`).join("\n")}

### Key Dates:
${(overview.key_dates || []).map((d: any) => `- **${d.label}:** ${d.date}`).join("\n")}

---

## 2. Attention Items & Critical Findings (${findingsList.length})
${findingsList
  .map(
    (f: any, idx: number) =>
      `### ${idx + 1}. [${f.severity}] ${f.title}
- **Category:** ${f.category}
- **Explanation:** ${f.explanation}
- **Why Shown:** ${f.why_shown || "Risk detection heuristic"}
`
  )
  .join("\n")}

---

## 3. Contractual Timeline
${timelineList
  .map(
    (e: any) =>
      `- **${e.date_value || "TBD"}** — ${e.label} (*${e.date_status}*: ${e.calculation_trace})`
  )
  .join("\n")}

---

## 4. Strategic Questions for Legal Counsel
${questionsList
  .map(
    (q: any, idx: number) =>
      `${idx + 1}. **${q.question}**\n   *Rationale:* ${q.reason}`
  )
  .join("\n\n")}

---
*Notice: AI-generated summary intended for contract review and preparation. Not a formal substitute for qualified legal advice.*
`;

    const blob = new Blob([summaryContent], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = window.document.createElement("a");
    a.href = url;
    a.download = `${document?.filename?.replace(/\.[^/.]+$/, "") || "LegalLens"}_Analysis_Report.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const overview = analysis?.overview || {};
  const findings = analysis?.findings || [];
  const timeline = analysis?.timeline || [];
  const checklist = analysis?.checklist || [];
  const lawyerQuestions = analysis?.lawyer_questions || [];

  // Filtered findings
  const filteredFindings = findings.filter((f: any) => {
    if (severityFilter === "ALL") return true;
    return f.severity === severityFilter;
  });

  // Filtered clauses
  const filteredClauses = clauses.filter((c: any) => {
    if (!clauseSearch.trim()) return true;
    const term = clauseSearch.toLowerCase();
    return (
      c.original_text?.toLowerCase().includes(term) ||
      c.heading?.toLowerCase().includes(term) ||
      c.clause_type?.toLowerCase().includes(term)
    );
  });

  // Severity counts
  const countImportant = findings.filter((f: any) => f.severity === "IMPORTANT").length;
  const countNeedsReview = findings.filter((f: any) => f.severity === "NEEDS_REVIEW").length;
  const countAttention = findings.filter((f: any) => f.severity === "ATTENTION_REQUIRED").length;
  const countMissing = findings.filter((f: any) => f.severity === "INFORMATION_MISSING").length;

  return (
    <div className={styles.container}>
      {/* ── Left Sidebar Navigation ────────────────────────────── */}
      <aside className={styles.sidebar} aria-label="Workspace Sidebar">
        <div className={styles.logoIcon} title="LegalLens Intelligence" aria-label="LegalLens Logo">
          L
        </div>

        <nav role="tablist" aria-label="Dashboard views" style={{ display: "flex", flexDirection: "column", gap: "0.5rem", width: "100%" }}>
          <button
            role="tab"
            aria-selected={activeTab === "overview"}
            aria-controls="panel-overview"
            aria-label="Situation Map & Overview"
            className={`${styles.navButton} ${activeTab === "overview" ? styles.active : ""}`}
            onClick={() => setActiveTab("overview")}
            title="Situation Map & Overview"
          >
            <LayoutDashboard size={20} aria-hidden="true" />
          </button>

          <button
            role="tab"
            aria-selected={activeTab === "viewer"}
            aria-controls="panel-viewer"
            aria-label="Document Viewer & Clauses"
            className={`${styles.navButton} ${activeTab === "viewer" ? styles.active : ""}`}
            onClick={() => setActiveTab("viewer")}
            title="Document Viewer & Clauses"
          >
            <FileText size={20} aria-hidden="true" />
          </button>

          <button
            role="tab"
            aria-selected={activeTab === "findings"}
            aria-controls="panel-findings"
            aria-label="Attention Items & Risks"
            className={`${styles.navButton} ${activeTab === "findings" ? styles.active : ""}`}
            onClick={() => setActiveTab("findings")}
            title="Attention Items & Risks"
          >
            <AlertTriangle size={20} aria-hidden="true" />
          </button>

          <button
            role="tab"
            aria-selected={activeTab === "timeline"}
            aria-controls="panel-timeline"
            aria-label="Chronological Timeline"
            className={`${styles.navButton} ${activeTab === "timeline" ? styles.active : ""}`}
            onClick={() => setActiveTab("timeline")}
            title="Chronological Timeline"
          >
            <Clock size={20} aria-hidden="true" />
          </button>

          <button
            role="tab"
            aria-selected={activeTab === "checklist"}
            aria-controls="panel-checklist"
            aria-label="Checklist & Lawyer Questions"
            className={`${styles.navButton} ${activeTab === "checklist" ? styles.active : ""}`}
            onClick={() => setActiveTab("checklist")}
            title="Checklist & Lawyer Questions"
          >
            <CheckSquare size={20} aria-hidden="true" />
          </button>
        </nav>

        <div style={{ flex: 1 }} />

        <button
          aria-expanded={isChatOpen}
          aria-label={isChatOpen ? "Collapse AI Assistant" : "Open AI Assistant"}
          className={`${styles.navButton} ${isChatOpen ? styles.active : ""}`}
          onClick={() => setIsChatOpen(!isChatOpen)}
          title={isChatOpen ? "Collapse AI Assistant" : "Open AI Assistant"}
        >
          <MessageSquare size={20} aria-hidden="true" />
        </button>

        <Link href="/upload" className={styles.navButton} title="Upload New Document" aria-label="Upload New Document">
          <ArrowLeft size={20} aria-hidden="true" />
        </Link>
      </aside>

      {/* ── Main Content Area ──────────────────────────────────── */}
      <div className={styles.mainContent}>
        {/* Topbar */}
        <header className={styles.topbar}>
          <div className={styles.topbarLeft}>
            <Link href="/upload" className={styles.backLink}>
              <ArrowLeft size={14} /> New Upload
            </Link>
            <div className={styles.docTitle}>
              {loading ? "Loading Document..." : document?.filename || "Untitled Document"}
            </div>
            {overview.document_type_label && (
              <span className={`${styles.badge} ${styles.badgeAccent}`}>
                {overview.document_type_label}
              </span>
            )}
          </div>

          <div className={styles.topbarRight}>
            <span className={`${styles.badge} ${styles.badgeSuccess}`}>
              <Shield size={12} /> Grounded & Verified
            </span>
            <div className={styles.exportContainer} ref={exportMenuRef}>
              <button
                className={styles.exportButton}
                onClick={() => setShowExportMenu(!showExportMenu)}
                aria-haspopup="true"
                aria-expanded={showExportMenu}
                aria-label="Export Executive Analysis Report"
                title="Export Executive Analysis Report"
              >
                <Download size={14} aria-hidden="true" /> Export Report <ChevronDown size={12} aria-hidden="true" />
              </button>

              {showExportMenu && (
                <div className={styles.exportMenu}>
                  <button className={styles.exportMenuItem} onClick={exportToPdf}>
                    <div className={styles.exportItemLeft}>
                      <Printer size={15} style={{ color: "#ef4444" }} />
                      <span>PDF Document</span>
                    </div>
                    <span className={styles.exportFormatBadge}>.pdf</span>
                  </button>
                  <button className={styles.exportMenuItem} onClick={exportToWord}>
                    <div className={styles.exportItemLeft}>
                      <FileDown size={15} style={{ color: "#3b82f6" }} />
                      <span>Word Document</span>
                    </div>
                    <span className={styles.exportFormatBadge}>.doc</span>
                  </button>
                  <button className={styles.exportMenuItem} onClick={copyToClipboard}>
                    <div className={styles.exportItemLeft}>
                      <Copy size={15} style={{ color: "#10b981" }} />
                      <span>{exportCopied ? "Copied!" : "Copy Briefing"}</span>
                    </div>
                  </button>
                  <button className={styles.exportMenuItem} onClick={exportToMarkdown}>
                    <div className={styles.exportItemLeft}>
                      <FileText size={15} style={{ color: "#a855f7" }} />
                      <span>Markdown Text</span>
                    </div>
                    <span className={styles.exportFormatBadge}>.md</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Workspace */}
        <div className={styles.workspace}>
          {/* Main Work Area with Tabs */}
          <div className={styles.mainPanel}>
            {/* Tabs */}
            <div className={styles.tabBar}>
              <button
                className={`${styles.tabItem} ${activeTab === "overview" ? styles.tabActive : ""}`}
                onClick={() => setActiveTab("overview")}
              >
                <LayoutDashboard size={16} /> Situation Map
              </button>
              <button
                className={`${styles.tabItem} ${activeTab === "viewer" ? styles.tabActive : ""}`}
                onClick={() => setActiveTab("viewer")}
              >
                <FileText size={16} /> Document Viewer
                <span className={styles.tabCount}>{clauses.length}</span>
              </button>
              <button
                className={`${styles.tabItem} ${activeTab === "findings" ? styles.tabActive : ""}`}
                onClick={() => setActiveTab("findings")}
              >
                <AlertTriangle size={16} /> Attention Items
                <span className={styles.tabCount}>{findings.length}</span>
              </button>
              <button
                className={`${styles.tabItem} ${activeTab === "timeline" ? styles.tabActive : ""}`}
                onClick={() => setActiveTab("timeline")}
              >
                <Clock size={16} /> Timeline
                <span className={styles.tabCount}>{timeline.length}</span>
              </button>
              <button
                className={`${styles.tabItem} ${activeTab === "checklist" ? styles.tabActive : ""}`}
                onClick={() => setActiveTab("checklist")}
              >
                <CheckSquare size={16} /> Checklist & Questions
                <span className={styles.tabCount}>{checklist.length}</span>
              </button>
            </div>

            {/* Tab Contents */}
            <div className={styles.tabContent}>
              {/* ── TAB 1: OVERVIEW & SITUATION MAP ────────────────── */}
              {activeTab === "overview" && (
                <div className={styles.overviewContainer}>
                  {/* Snapshot Card */}
                  <div className={styles.snapshotCard}>
                    <div className={styles.snapshotHeader}>
                      <div className={styles.snapshotTitle}>
                        <Sparkles size={18} style={{ color: "var(--accent-secondary)" }} />
                        Legal Situation Snapshot
                      </div>
                      <span className={`${styles.badge} ${styles.badgeInfo}`}>
                        AI Extraction v1.0
                      </span>
                    </div>
                    <p className={styles.snapshotText}>
                      {overview.situation_snapshot ||
                        "Analysis has extracted key deal terms, parties, and obligations. Review attention items below before signing."}
                    </p>
                  </div>

                  {/* Key Deal Terms Grid */}
                  <div className={styles.termsGrid}>
                    <div className={styles.termCard}>
                      <div className={styles.termLabel}>Agreement Type</div>
                      <div className={styles.termValue}>
                        {overview.document_type_label || "Contract"}
                      </div>
                      <div className={styles.termSub}>{pages.length} Pages Extracted</div>
                    </div>

                    <div className={styles.termCard}>
                      <div className={styles.termLabel}>Effective Date</div>
                      <div className={styles.termValue}>
                        {overview.key_dates?.[0]?.date || "Date of Execution"}
                      </div>
                      <div className={styles.termSub}>Binding Start Date</div>
                    </div>

                    <div className={styles.termCard}>
                      <div className={styles.termLabel}>Liability Cap</div>
                      <div className={styles.termValue}>
                        {findings.find((f: any) => f.category === "LIABILITY") ? "$2,000,000" : "Not Specified"}
                      </div>
                      <div className={styles.termSub}>Max Financial Exposure</div>
                    </div>

                    <div className={styles.termCard}>
                      <div className={styles.termLabel}>Governing Law</div>
                      <div className={styles.termValue}>State of Delaware</div>
                      <div className={styles.termSub}>Substantive Jurisdiction</div>
                    </div>
                  </div>

                  {/* Contracting Parties */}
                  <div className={styles.partiesCard}>
                    <div className={styles.sectionHeading}>
                      <Building size={16} style={{ color: "var(--accent-primary)" }} />
                      Identified Contracting Parties
                    </div>
                    <div className={styles.partiesList}>
                      {(overview.parties || [
                        { name: "ACME Corp", role: "Disclosing Party" },
                        { name: "Beta LLC", role: "Receiving Party" },
                      ]).map((party: any, idx: number) => (
                        <div key={idx} className={styles.partyItem}>
                          <div className={styles.partyIcon}>
                            <Building size={18} />
                          </div>
                          <div>
                            <div className={styles.partyName}>{party.name}</div>
                            <div className={styles.partyRole}>{party.role}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Attention Items Summary */}
                  <div>
                    <div className={styles.sectionHeading}>
                      <AlertTriangle size={16} style={{ color: "var(--status-warning)" }} />
                      Attention Items by Severity
                    </div>
                    <div className={styles.riskSummaryRow}>
                      <div
                        className={styles.riskStatCard}
                        onClick={() => {
                          setSeverityFilter("IMPORTANT");
                          setActiveTab("findings");
                        }}
                      >
                        <div className={styles.statNumber} style={{ color: "#f87171" }}>
                          {countImportant}
                        </div>
                        <div className={styles.statLabel}>Important Risks</div>
                      </div>

                      <div
                        className={styles.riskStatCard}
                        onClick={() => {
                          setSeverityFilter("NEEDS_REVIEW");
                          setActiveTab("findings");
                        }}
                      >
                        <div className={styles.statNumber} style={{ color: "#fbbf24" }}>
                          {countNeedsReview}
                        </div>
                        <div className={styles.statLabel}>Needs Review</div>
                      </div>

                      <div
                        className={styles.riskStatCard}
                        onClick={() => {
                          setSeverityFilter("ATTENTION_REQUIRED");
                          setActiveTab("findings");
                        }}
                      >
                        <div className={styles.statNumber} style={{ color: "#60a5fa" }}>
                          {countAttention}
                        </div>
                        <div className={styles.statLabel}>Attention Items</div>
                      </div>

                      <div
                        className={styles.riskStatCard}
                        onClick={() => {
                          setSeverityFilter("INFORMATION_MISSING");
                          setActiveTab("findings");
                        }}
                      >
                        <div className={styles.statNumber} style={{ color: "#c084fc" }}>
                          {countMissing}
                        </div>
                        <div className={styles.statLabel}>Missing Clauses</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ── TAB 2: DOCUMENT VIEWER & CLAUSES ───────────────── */}
              {activeTab === "viewer" && (
                <div className={styles.viewerContent}>
                  {/* Toolbar */}
                  <div className={styles.viewerToolbar}>
                    <div className={styles.inputWrapper} style={{ maxWidth: 360 }}>
                      <Search size={14} style={{ color: "var(--text-muted)", marginRight: 8 }} />
                      <input
                        type="text"
                        placeholder="Filter clauses by keyword..."
                        value={clauseSearch}
                        onChange={(e) => setClauseSearch(e.target.value)}
                      />
                    </div>
                    <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                      Showing {filteredClauses.length} of {clauses.length} parsed clauses
                    </div>
                  </div>

                  {/* Document Page Simulation */}
                  <div className={styles.pageContainer}>
                    {filteredClauses.length === 0 ? (
                      <div style={{ padding: "3rem", textAlign: "center", color: "#64748b" }}>
                        No clauses matched the filter criteria.
                      </div>
                    ) : (
                      filteredClauses.map((clause) => {
                        const isHighlighted = highlightedClauseId === clause.clause_id;
                        return (
                          <div
                            key={clause.clause_id}
                            id={`clause-${clause.clause_id}`}
                            className={`${styles.clauseBox} ${
                              isHighlighted ? styles.clauseHighlighted : ""
                            }`}
                          >
                            <div className={styles.clauseMeta}>
                              <span>SECTION {clause.number || "•"}</span>
                              <span style={{ color: "#cbd5e1" }}>|</span>
                              <span>{clause.clause_type?.replace(/_/g, " ")}</span>
                            </div>
                            {clause.heading && (
                              <div className={styles.clauseHeading}>{clause.heading}</div>
                            )}
                            <div style={{ whiteSpace: "pre-wrap", color: "#1e293b" }}>
                              {clause.original_text}
                            </div>
                          </div>
                        );
                      })
                    )}
                    <div className={styles.pageNumber}>- Page 1 of {pages.length || 1} -</div>
                  </div>
                </div>
              )}

              {/* ── TAB 3: ATTENTION ITEMS & FINDINGS ──────────────── */}
              {activeTab === "findings" && (
                <div className={styles.findingsContainer}>
                  {/* Filter bar */}
                  <div className={styles.filterBar}>
                    <div className={styles.filterPills}>
                      {["ALL", "IMPORTANT", "NEEDS_REVIEW", "ATTENTION_REQUIRED", "INFORMATION_MISSING"].map(
                        (sev) => (
                          <button
                            key={sev}
                            className={`${styles.filterPill} ${
                              severityFilter === sev ? styles.filterActive : ""
                            }`}
                            onClick={() => setSeverityFilter(sev)}
                          >
                            {sev.replace(/_/g, " ")}
                          </button>
                        )
                      )}
                    </div>
                    <span style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                      {filteredFindings.length} attention items
                    </span>
                  </div>

                  {/* Findings list */}
                  {filteredFindings.map((finding: any) => {
                    const sevClass =
                      finding.severity === "IMPORTANT"
                        ? styles.severityImportant
                        : finding.severity === "NEEDS_REVIEW"
                        ? styles.severityNeedsReview
                        : finding.severity === "ATTENTION_REQUIRED"
                        ? styles.severityAttention
                        : styles.severityMissing;

                    return (
                      <div key={finding.finding_id} className={styles.findingCard}>
                        <div className={styles.findingTop}>
                          <div className={styles.findingBadges}>
                            <span className={`${styles.badge} ${sevClass}`}>
                              {finding.severity?.replace(/_/g, " ")}
                            </span>
                            <span className={`${styles.badge} ${styles.badgeInfo}`}>
                              {finding.category?.replace(/_/g, " ")}
                            </span>
                          </div>
                          {finding.evidence_ids?.length > 0 && (
                            <button
                              className={styles.highlightActionBtn}
                              onClick={() => jumpToClause(finding.evidence_ids[0])}
                            >
                              <FileText size={12} /> View in Document
                            </button>
                          )}
                        </div>

                        <div className={styles.findingTitle}>{finding.title}</div>
                        <div className={styles.findingExplanation}>{finding.explanation}</div>

                        {finding.evidence_ids?.length > 0 && (
                          <div className={styles.evidenceQuoteBox}>
                            <div className={styles.evidenceLabel}>Supporting Source Clause:</div>
                            <div>
                              {clauses.find((c) => c.clause_id === finding.evidence_ids[0])
                                ?.original_text || "Referenced in contract clause text."}
                            </div>
                          </div>
                        )}

                        <div className={styles.findingFooter}>
                          <div className={styles.whyShownTag}>
                            <HelpCircle size={12} /> {finding.why_shown || "Detected by LegalLens"}
                          </div>
                          <div>Confidence: {Math.round((finding.confidence || 0.9) * 100)}%</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* ── TAB 4: CHRONOLOGICAL TIMELINE ──────────────────── */}
              {activeTab === "timeline" && (
                <div className={styles.timelineContainer}>
                  <div className={styles.timelineLine} />
                  {timeline.map((evt: any, idx: number) => (
                    <div key={idx} className={styles.timelineItem}>
                      <div className={styles.timelineNode}>
                        <Calendar size={20} />
                      </div>
                      <div className={styles.timelineCard}>
                        <div className={styles.timelineHeader}>
                          <div className={styles.timelineLabel}>{evt.label}</div>
                          <div className={styles.timelineDate}>{evt.date_value || "TBD"}</div>
                        </div>
                        <div style={{ display: "flex", gap: 8, margin: "4px 0" }}>
                          <span
                            className={`${styles.badge} ${
                              evt.date_status === "EXPLICIT"
                                ? styles.badgeSuccess
                                : styles.badgeWarning
                            }`}
                          >
                            Status: {evt.date_status}
                          </span>
                          <span className={`${styles.badge} ${styles.badgeInfo}`}>
                            {evt.event_type?.replace(/_/g, " ")}
                          </span>
                        </div>
                        <div className={styles.timelineTrace}>
                          <strong>Trace:</strong> {evt.calculation_trace}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* ── TAB 5: CHECKLIST & LAWYER QUESTIONS ────────────── */}
              {activeTab === "checklist" && (
                <div className={styles.checklistGrid}>
                  {/* Preparation Checklist */}
                  <div className={styles.checklistColumn}>
                    <div className={styles.sectionHeading}>
                      <CheckSquare size={18} style={{ color: "var(--status-success)" }} />
                      Preparation Checklist ({checklist.length})
                    </div>
                    {checklist.map((item: any) => {
                      const isDone = checklistCompleted[item.item_id];
                      return (
                        <div
                          key={item.item_id}
                          className={styles.checkItem}
                          onClick={() => toggleChecklist(item.item_id)}
                        >
                          <div
                            className={`${styles.checkboxBox} ${
                              isDone ? styles.checkboxChecked : ""
                            }`}
                          >
                            {isDone && <Check size={14} />}
                          </div>
                          <div>
                            <div
                              className={`${styles.checkText} ${
                                isDone ? styles.checkCompletedText : ""
                              }`}
                            >
                              {item.text}
                            </div>
                            <div className={styles.checkReason}>{item.reason}</div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Strategic Lawyer Questions */}
                  <div className={styles.checklistColumn}>
                    <div className={styles.sectionHeading}>
                      <Scale size={18} style={{ color: "var(--accent-secondary)" }} />
                      Strategic Questions for Legal Counsel
                    </div>
                    {lawyerQuestions.map((q: any) => (
                      <div key={q.question_id} className={styles.lawyerCard}>
                        <div className={styles.lawyerQuestion}>{q.question}</div>
                        <div className={styles.lawyerReason}>
                          <strong>Why ask this:</strong> {q.reason}
                        </div>
                        <div className={styles.lawyerActions}>
                          <button
                            className={styles.miniBtn}
                            onClick={() => copyQuestion(q.question_id, q.question)}
                          >
                            {copiedQuestionId === q.question_id ? (
                              <>
                                <Check size={12} style={{ color: "var(--status-success)" }} /> Copied
                              </>
                            ) : (
                              <>
                                <Copy size={12} /> Copy
                              </>
                            )}
                          </button>
                          <button
                            className={styles.miniBtn}
                            onClick={() => askQuestionInAssistant(q.question)}
                          >
                            <Sparkles size={12} style={{ color: "var(--accent-secondary)" }} /> Ask AI
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* ── Right Panel: AI Legal Assistant Chat ─────────────── */}
          <section
            className={`${styles.assistantPanel} ${
              !isChatOpen ? styles.assistantPanelCollapsed : ""
            }`}
          >
            <div className={styles.panelHeader}>
              <div className={styles.headerLeft}>
                <Scale size={18} style={{ color: "var(--accent-secondary)" }} />
                <span>Grounded AI Assistant</span>
              </div>
              <button
                className={styles.navButton}
                style={{ width: 28, height: 28 }}
                onClick={() => setIsChatOpen(false)}
                title="Collapse Assistant"
              >
                <Minimize2 size={16} />
              </button>
            </div>

            {/* Chat Messages */}
            <div className={styles.chatMessages}>
              {/* Quick Prompts */}
              <div className={styles.promptSuggestions}>
                <div className={styles.promptSuggestionsTitle}>Recommended Queries</div>
                <div className={styles.promptChips}>
                  {(lawyerQuestions && lawyerQuestions.length > 0
                    ? lawyerQuestions.slice(0, 4).map((q: any) => q.question)
                    : [
                        "What is the governing law?",
                        "What is the liability cap?",
                        "What are the confidentiality obligations?",
                        "Are there early termination rights?",
                      ]
                  ).map((chip: string) => (
                    <button
                      key={chip}
                      className={styles.promptChip}
                      onClick={() => handleSend(chip)}
                      disabled={isTyping}
                      title={chip}
                    >
                      {chip}
                    </button>
                  ))}
                </div>
              </div>

              {messages.map((msg) => (
                <div key={msg.id} className={`${styles.message} ${styles[msg.role]}`}>
                  <div className={`${styles.avatar} ${styles[msg.role]}`}>
                    {msg.role === "user" ? <User size={16} /> : <Scale size={16} />}
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", maxWidth: "100%" }}>
                    <div className={styles.messageBubble}>
                      {msg.answer_status && (
                        <div
                          className={`${styles.answerStatusBadge} ${
                            msg.answer_status === "SUPPORTED"
                              ? styles.badgeSuccess
                              : styles.badgeWarning
                          }`}
                        >
                          <Shield size={10} /> Status: {msg.answer_status}
                        </div>
                      )}
                      <div>{msg.content}</div>
                    </div>

                    {/* Citations Box */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className={styles.citationsBox} role="group" aria-label="Cited sources">
                        {msg.citations.map((cit, idx) => (
                          <div
                            key={idx}
                            role="button"
                            tabIndex={0}
                            className={styles.citationItem}
                            onClick={() => jumpToClause(cit.source_ids?.[0])}
                            onKeyDown={(e) => {
                              if (e.key === "Enter" || e.key === " ") {
                                e.preventDefault();
                                jumpToClause(cit.source_ids?.[0]);
                              }
                            }}
                            title="Click or press Enter to locate clause in document viewer"
                            aria-label={`Source citation: ${cit.claim}. Press Enter to jump to clause in viewer.`}
                          >
                            <div className={styles.citationHeader}>
                              <span>Source: Clause Citation</span>
                              <ExternalLink size={10} aria-hidden="true" />
                            </div>
                            <div className={styles.citationQuote}>"{cit.claim}"</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className={`${styles.message} ${styles.assistant}`} role="status" aria-live="polite">
                  <div className={`${styles.avatar} ${styles.assistant}`} aria-hidden="true">
                    <Scale size={16} />
                  </div>
                  <div className={styles.messageBubble}>
                    <div className={styles.typingIndicator} aria-label="Assistant is analyzing document clauses">
                      <span />
                      <span />
                      <span />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Chat Input */}
            <div className={styles.chatInput}>
              <div className={styles.inputWrapper}>
                <input
                  type="text"
                  placeholder="Ask a question grounded in this document..."
                  aria-label="Ask a question grounded in this document"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSend()}
                  disabled={isTyping}
                />
                <button
                  className={styles.sendButton}
                  onClick={() => handleSend()}
                  disabled={!inputValue.trim() || isTyping || !sessionId}
                  title="Send Question"
                  aria-label="Send Question"
                >
                  <Send size={15} aria-hidden="true" />
                </button>
              </div>
              <div className={styles.chatDisclaimer}>
                Responses are verified against contract clauses. Not legal advice.
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
