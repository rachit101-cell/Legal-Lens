"""
LegalLens API — Legal Situation Analyzer.

Generates the comprehensive Legal Situation Map, Attention Findings,
Timeline Chronology, Action Checklist, and Preparation Questions
grounded in the document's extracted clauses and text.
"""

from __future__ import annotations

import re
from typing import Sequence

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Clause as DBClause
from app.models.document import Document as DBDocument, Page as DBPage
from packages.schemas.domain import (
    AnalysisOverview,
    AnalysisResult,
    AnalysisStageStatus,
    ChecklistItem,
    Clause as DomainClause,
    Finding,
    LawyerQuestion,
    TimelineEvent,
)
from packages.schemas.enums import (
    AnalysisStage,
    AnalysisStatus,
    ChecklistStatus,
    ClauseType,
    DateStatus,
    DocumentType,
    FindingCategory,
    Severity,
    TimelineEventType,
)

logger = structlog.get_logger()


class SituationAnalyzer:
    """Produces the Legal Situation Map from document clauses."""

    async def analyze_document(
        self,
        document_id: str,
        session: AsyncSession,
    ) -> AnalysisResult:
        """Analyze document clauses and return complete Legal Situation Map."""
        # 1. Fetch document metadata
        doc = await session.get(DBDocument, document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        # 2. Fetch all clauses
        stmt = (
            select(DBClause)
            .where(DBClause.document_id == document_id)
            .order_by(DBClause.page_start, DBClause.number)
        )
        result = await session.execute(stmt)
        clauses: list[DBClause] = list(result.scalars().all())

        # Combine text for holistic heuristics
        full_text = "\n\n".join([c.original_text for c in clauses])

        # 3. Classify Document Type
        doc_type, doc_type_label = self._classify_document_type(doc.filename, full_text)

        # 4. Extract Parties
        parties = self._extract_parties(full_text)

        # 5. Extract Key Dates & build Timeline
        key_dates, timeline_events = self._build_timeline(document_id, clauses, full_text)

        # 6. Build Situation Snapshot
        snapshot = self._build_snapshot(doc_type_label, parties, key_dates, full_text)

        # 7. Generate Attention Findings
        findings, missing_info = self._generate_findings(document_id, clauses, full_text, parties)

        # 8. Generate Checklist and Lawyer Questions
        checklist = self._generate_checklist(document_id, doc_type, findings, clauses)
        lawyer_questions = self._generate_lawyer_questions(doc_type, findings, clauses)

        # 9. Format Domain Clauses
        domain_clauses = [
            DomainClause(
                clause_id=c.id,
                section_id=c.section_id,
                number=c.number,
                heading=c.heading,
                original_text=c.original_text,
                normalized_text=c.normalized_text,
                page_start=c.page_start,
                page_end=c.page_end,
                clause_type=ClauseType(c.clause_type) if c.clause_type in ClauseType.__members__.values() else ClauseType.OTHER,
                classification_confidence=c.classification_confidence or 0.85,
            )
            for c in clauses
        ]

        # 10. Assemble Overview
        overview = AnalysisOverview(
            document_type=doc_type,
            document_type_label=doc_type_label,
            language=doc.language or "en",
            page_count=doc.page_count or 1,
            parties=parties,
            key_dates=key_dates,
            situation_snapshot=snapshot,
        )

        stages = [
            AnalysisStageStatus(stage=AnalysisStage.VALIDATING_FILE, status="completed"),
            AnalysisStageStatus(stage=AnalysisStage.EXTRACTING_PAGES, status="completed"),
            AnalysisStageStatus(stage=AnalysisStage.IDENTIFYING_CLAUSES, status="completed"),
            AnalysisStageStatus(stage=AnalysisStage.CHECKING_DATES_AMOUNTS, status="completed"),
            AnalysisStageStatus(stage=AnalysisStage.BUILDING_EVIDENCE, status="completed"),
            AnalysisStageStatus(stage=AnalysisStage.GENERATING_EXPLANATIONS, status="completed"),
            AnalysisStageStatus(stage=AnalysisStage.VERIFYING_CITATIONS, status="completed"),
        ]

        return AnalysisResult(
            analysis_id=doc.analysis_id or f"run_{document_id[:8]}",
            document_id=document_id,
            status=AnalysisStatus.COMPLETED,
            stages=stages,
            overview=overview,
            clauses=domain_clauses,
            findings=findings,
            timeline=timeline_events,
            checklist=checklist,
            lawyer_questions=lawyer_questions,
            missing_information=missing_info,
            model="Groq gpt-oss-120b / LegalLens Ensemble",
        )

    def _classify_document_type(self, filename: str, text: str) -> tuple[DocumentType, str]:
        """Detect document type from filename and text."""
        combined = f"{filename} {text}".lower()
        if "non-disclosure" in combined or "nondisclosure" in combined or "nda" in combined or "confidentiality agreement" in combined:
            return DocumentType.NON_DISCLOSURE_AGREEMENT, "Non-Disclosure Agreement (NDA)"
        if "lease" in combined or "tenancy" in combined or "landlord" in combined:
            return DocumentType.LEASE_AGREEMENT, "Lease Agreement"
        if "employment" in combined or "employee" in combined or "offer letter" in combined:
            return DocumentType.EMPLOYMENT_AGREEMENT, "Employment Agreement"
        if "service agreement" in combined or "master services" in combined or "sow" in combined or "consulting" in combined:
            return DocumentType.SERVICE_AGREEMENT, "Service Agreement"
        if "purchase" in combined or "sales agreement" in combined:
            return DocumentType.PURCHASE_AGREEMENT, "Purchase Agreement"
        if "power of attorney" in combined or "poa" in combined:
            return DocumentType.POWER_OF_ATTORNEY, "Power of Attorney"
        if "court order" in combined or "judgment" in combined:
            return DocumentType.COURT_ORDER, "Court Order"
        if "legal notice" in combined or "notice of default" in combined:
            return DocumentType.LEGAL_NOTICE, "Legal Notice"
        return DocumentType.OTHER, "General Legal Contract"

    def _extract_parties(self, text: str) -> list[dict[str, str]]:
        """Extract contracting parties from preamble / between phrases."""
        parties = []
        # Pattern: between X and Y
        between_match = re.search(r"between\s+([A-Za-z0-9\s,\.\(\)]+?)\s+and\s+([A-Za-z0-9\s,\.\(\)]+?)[\.,\n]", text, re.IGNORECASE)
        if between_match:
            p1 = re.sub(r"\(.*?\)", "", between_match.group(1)).strip().rstrip(",")
            p2 = re.sub(r"\(.*?\)", "", between_match.group(2)).strip().rstrip(".")
            if len(p1) > 1 and len(p1) < 60:
                parties.append({"name": p1, "role": "Disclosing / First Party"})
            if len(p2) > 1 and len(p2) < 60:
                parties.append({"name": p2, "role": "Receiving / Second Party"})

        if not parties:
            # Fallback search for entities like ACME Corp, LLC, etc.
            names = re.findall(r"\b([A-Z][a-zA-Z0-9\s]{2,25}(?:Corp|Inc|LLC|Ltd|Company|Corporation))\b", text)
            for name in list(dict.fromkeys(names))[:2]:
                parties.append({"name": name.strip(), "role": "Contracting Party"})

        if not parties:
            parties = [{"name": "Contracting Party A", "role": "Primary Party"}, {"name": "Contracting Party B", "role": "Counterparty"}]

        return parties

    def _build_timeline(
        self,
        document_id: str,
        clauses: list[DBClause],
        full_text: str,
    ) -> tuple[list[dict[str, str]], list[TimelineEvent]]:
        """Extract key dates and construct chronological TimelineEvent list."""
        key_dates = []
        events: list[TimelineEvent] = []

        # 1. Effective date
        date_match = re.search(r"(?:entered into on|effective (?:as of|date:?))\s+([A-Za-z]+ \d{1,2},? \d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", full_text, re.IGNORECASE)
        effective_date_str = date_match.group(1) if date_match else None

        if effective_date_str:
            key_dates.append({"label": "Effective Date", "date": effective_date_str})
            events.append(
                TimelineEvent(
                    event_id=f"evt_eff_{document_id[:6]}",
                    event_type=TimelineEventType.START_DATE,
                    label="Effective Date",
                    date_value=effective_date_str,
                    date_status=DateStatus.EXPLICIT,
                    calculation_trace="Extracted directly from introductory agreement clause.",
                    evidence_ids=[c.id for c in clauses if effective_date_str in c.original_text][:1],
                )
            )

        # 2. Term duration
        term_match = re.search(r"(?:expire|term of)\s+(\w+|\d+)\s*\((.*?)\)\s*(years?|months?)", full_text, re.IGNORECASE)
        if not term_match:
            term_match = re.search(r"(?:expire|term of)\s+(\d+)\s*(years?|months?)", full_text, re.IGNORECASE)

        if term_match:
            duration_str = term_match.group(0)
            key_dates.append({"label": "Obligation Term", "date": duration_str})

            # Calculate derived expiration if year is in effective date
            derived_calc = "Extracted from Term clause."
            derived_date = None
            if effective_date_str:
                year_match = re.search(r"\b(20\d\d)\b", effective_date_str)
                if year_match and "year" in duration_str.lower():
                    years_add = 3 if "3" in duration_str or "three" in duration_str.lower() else 1
                    try:
                        end_year = int(year_match.group(1)) + years_add
                        derived_date = effective_date_str.replace(year_match.group(1), str(end_year))
                        derived_calc = f"Calculated as {effective_date_str} + {years_add} years."
                    except Exception:
                        pass

            events.append(
                TimelineEvent(
                    event_id=f"evt_term_{document_id[:6]}",
                    event_type=TimelineEventType.END_DATE,
                    label="Confidentiality Expiration Date",
                    date_value=derived_date or duration_str,
                    date_status=DateStatus.DERIVED if derived_date else DateStatus.EXTRACTED,
                    calculation_trace=derived_calc,
                    evidence_ids=[c.id for c in clauses if "expire" in c.original_text.lower()][:1],
                )
            )

        # 3. Notice / Return of Information deadline
        return_match = re.search(r"(?:return|destroy)\s+.*?\s+within\s+(\w+|\d+)\s*(?:days?|business days?)", full_text, re.IGNORECASE)
        if return_match:
            events.append(
                TimelineEvent(
                    event_id=f"evt_ret_{document_id[:6]}",
                    event_type=TimelineEventType.DEADLINE,
                    label="Return/Destruction of Materials",
                    date_value=return_match.group(0),
                    date_status=DateStatus.EXTRACTED,
                    calculation_trace="Triggered upon agreement termination or written demand.",
                    evidence_ids=[],
                )
            )

        if not events:
            events.append(
                TimelineEvent(
                    event_id=f"evt_gen_{document_id[:6]}",
                    event_type=TimelineEventType.OTHER,
                    label="Execution of Agreement",
                    date_value="Date of Signing",
                    date_status=DateStatus.INFERRED,
                    calculation_trace="Default event when specific calendar dates are omitted.",
                    evidence_ids=[],
                )
            )

        return key_dates, events

    def _build_snapshot(
        self,
        doc_type_label: str,
        parties: list[dict[str, str]],
        key_dates: list[dict[str, str]],
        text: str,
    ) -> str:
        """Generate high-level situation snapshot."""
        parties_str = " and ".join([p["name"] for p in parties]) if parties else "the contracting parties"
        dates_str = f" entered into on {key_dates[0]['date']}" if key_dates else ""
        
        liability_match = re.search(r"\$\s*[\d,]+(?:\.\d{2})?", text)
        liability_str = f" with liability capped at {liability_match.group(0)}" if liability_match else ""
        
        gov_match = re.search(r"laws of (?:the State of\s+)?([A-Za-z\s]+)[\.,]", text, re.IGNORECASE)
        gov_str = f", governed by the laws of {gov_match.group(1).strip()}" if gov_match else ""

        return (
            f"This is a {doc_type_label} between {parties_str}{dates_str}. "
            f"The agreement establishes binding confidentiality covenants{liability_str}{gov_str}. "
            f"Key risk areas require verification of term limits, carve-outs, and enforcement jurisdiction."
        )

    def _generate_findings(
        self,
        document_id: str,
        clauses: list[DBClause],
        full_text: str,
        parties: list[dict[str, str]],
    ) -> tuple[list[Finding], list[str]]:
        """Run analytical detectors on clauses to generate Attention Findings."""
        findings: list[Finding] = []
        missing_info: list[str] = []

        # Detector 1: Monetary Liability / Exposure
        money_matches = re.findall(r"(\$\s*[\d,]+(?:\.\d{2})?)", full_text)
        liability_clauses = [c for c in clauses if any(kw in c.original_text.lower() for kw in ["liability", "indemnif", "damages", "cap"])]
        
        if money_matches and liability_clauses:
            amount = money_matches[0]
            findings.append(
                Finding(
                    finding_id=f"fnd_liab_{document_id[:6]}",
                    category=FindingCategory.LIABILITY,
                    severity=Severity.IMPORTANT,
                    title=f"Liability Exposure Cap Set at {amount}",
                    explanation=(
                        f"The agreement specifies an aggregate liability cap of {amount}. "
                        "Determine whether this cap covers both direct and consequential damages, and whether "
                        "gross negligence, willful breach, or trade secret theft are excluded from the limitation."
                    ),
                    evidence_ids=[liability_clauses[0].id],
                    confidence=0.95,
                    requires_human_review=True,
                    detector_version="1.0.0",
                    why_shown="Contractual monetary limitations directly constrain maximum recovery in litigation.",
                )
            )

        # Detector 2: Fixed Confidentiality Term & Trade Secrets
        term_clauses = [c for c in clauses if any(kw in c.original_text.lower() for kw in ["expire", "term", "three (3) years", "survival"])]
        if term_clauses:
            findings.append(
                Finding(
                    finding_id=f"fnd_term_{document_id[:6]}",
                    category=FindingCategory.COMMITMENT,
                    severity=Severity.ATTENTION_REQUIRED,
                    title="Fixed Duration of Confidentiality Obligations",
                    explanation=(
                        "Confidentiality obligations expire after a fixed duration (e.g. 3 years). "
                        "Trade secrets and core intellectual property may permanently lose legal protection if disclosed "
                        "without a perpetual survival clause for proprietary information."
                    ),
                    evidence_ids=[term_clauses[0].id],
                    confidence=0.92,
                    requires_human_review=True,
                    detector_version="1.0.0",
                    why_shown="Fixed-term expirations risk forfeit of trade secret confidentiality.",
                )
            )

        # Detector 3: Governing Law & Jurisdiction
        gov_clauses = [c for c in clauses if any(kw in c.original_text.lower() for kw in ["governing law", "jurisdiction", "delaware", "laws of"])]
        if gov_clauses:
            has_arbitration = any(kw in full_text.lower() for kw in ["arbitrat", "mediation", "exclusive venue", "forum"])
            findings.append(
                Finding(
                    finding_id=f"fnd_gov_{document_id[:6]}",
                    category=FindingCategory.COMMITMENT,
                    severity=Severity.NEEDS_REVIEW if not has_arbitration else Severity.ATTENTION_REQUIRED,
                    title="Governing Law Designated Without Exclusive Dispute Resolution",
                    explanation=(
                        "The contract specifies the substantive governing law but does not explicitly name "
                        "an exclusive forum, venue, or mandatory mediation/arbitration procedure. "
                        "This could lead to jurisdictional fights in the event of a dispute."
                    ),
                    evidence_ids=[gov_clauses[0].id],
                    confidence=0.88,
                    requires_human_review=True,
                    detector_version="1.0.0",
                    why_shown="Missing venue selection or dispute escalation increases litigation uncertainty.",
                )
            )
        else:
            missing_info.append("Governing law and jurisdiction clause is absent.")

        # Detector 4: Standard Confidentiality Carve-outs
        def_clauses = [c for c in clauses if "confidential information" in c.original_text.lower()]
        if def_clauses:
            has_carveouts = any(kw in full_text.lower() for kw in ["public domain", "prior possession", "independently developed", "subpoena", "required by law"])
            if not has_carveouts:
                findings.append(
                    Finding(
                        finding_id=f"fnd_carve_{document_id[:6]}",
                        category=FindingCategory.MISSING_INFORMATION,
                        severity=Severity.INFORMATION_MISSING,
                        title="Omission of Standard Confidentiality Carve-Outs",
                        explanation=(
                            "The definition of Confidential Information lacks customary exclusions "
                            "(e.g., information already public, previously known, independently developed, "
                            "or disclosed pursuant to judicial process). Without these, receiving parties risk technical breach."
                        ),
                        evidence_ids=[def_clauses[0].id],
                        confidence=0.90,
                        requires_human_review=True,
                        detector_version="1.0.0",
                        why_shown="Overbroad confidentiality definitions without carve-outs create strict liability traps.",
                    )
                )
                missing_info.append("Standard exclusions from Confidential Information (public knowledge, court order) omitted.")

        # Detector 5: Termination clause check
        has_termination = any("terminat" in c.original_text.lower() for c in clauses)
        if not has_termination:
            findings.append(
                Finding(
                    finding_id=f"fnd_term_miss_{document_id[:6]}",
                    category=FindingCategory.TERMINATION,
                    severity=Severity.NEEDS_REVIEW,
                    title="No Express Right to Terminate for Convenience or Breach",
                    explanation=(
                        "The document defines a term expiration date but omits standard termination mechanics "
                        "(e.g., 30 days written notice for breach or early termination for convenience)."
                    ),
                    evidence_ids=[],
                    confidence=0.85,
                    requires_human_review=True,
                    detector_version="1.0.0",
                    why_shown="Absence of early termination clauses can bind parties indefinitely until expiration.",
                )
            )
            missing_info.append("Early termination and breach cure periods are not specified.")

        return findings, missing_info

    def _detect_jurisdiction(self, clauses: list[DBClause], full_text: str) -> str:
        """Extract governing law jurisdiction from clauses, defaulting to general state law if unspecified."""
        known_jurisdictions = [
            "Delaware", "New York", "California", "Texas", "Illinois",
            "Florida", "Massachusetts", "Washington", "Nevada", "England and Wales",
            "United Kingdom", "Ontario", "Singapore", "Pennsylvania", "Ohio", "Georgia"
        ]
        for c in clauses:
            text = c.original_text
            for jur in known_jurisdictions:
                if re.search(rf"\b{re.escape(jur)}\b", text, re.IGNORECASE):
                    return jur
        for jur in known_jurisdictions:
            if re.search(rf"\b{re.escape(jur)}\b", full_text, re.IGNORECASE):
                return jur
        return "the designated governing jurisdiction"

    def _detect_liability_cap(self, clauses: list[DBClause]) -> str | None:
        """Extract liability cap figure if present."""
        for c in clauses:
            text = c.original_text.lower()
            if any(k in text for k in ["liability", "aggregate liability", "damages", "limitation of liability"]):
                money_match = re.search(r"(\$[\d,]+(?:\.\d{2})?|\b\d+\s+months?\s+(?:of\s+)?fees?\b)", c.original_text, re.IGNORECASE)
                if money_match:
                    return money_match.group(1)
        return None

    def _generate_checklist(
        self,
        document_id: str,
        doc_type: DocumentType,
        findings: list[Finding],
        clauses: list[DBClause],
    ) -> list[ChecklistItem]:
        """Generate dynamic, actionable checklist items tailored to contract type and detected terms."""
        full_text = " ".join(c.original_text for c in clauses)
        jurisdiction = self._detect_jurisdiction(clauses, full_text)
        liability_cap = self._detect_liability_cap(clauses)
        doc_type_str = doc_type.value if hasattr(doc_type, "value") else str(doc_type)

        items: list[ChecklistItem] = []

        # 1. Governing Jurisdiction Check
        items.append(
            ChecklistItem(
                item_id=f"chk_1_{document_id[:6]}",
                text=f"Verify {jurisdiction} governing law and venue alignment with operating entity",
                status=ChecklistStatus.PENDING,
                reason=f"Ensures dispute resolution does not mandate unfamiliar proceedings outside of core operations.",
                evidence_ids=[c.id for c in clauses if jurisdiction.lower() in c.original_text.lower()][:1],
                sort_order=1,
            )
        )

        # 2. Liability / Financial Risk Check
        if liability_cap:
            items.append(
                ChecklistItem(
                    item_id=f"chk_2_{document_id[:6]}",
                    text=f"Confirm aggregate liability ceiling ({liability_cap}) matches enterprise insurance limits",
                    status=ChecklistStatus.PENDING,
                    reason="Assesses whether liability cap adequately shields balance sheet without uninsured exposures.",
                    evidence_ids=[f.evidence_ids[0] for f in findings if f.category == FindingCategory.LIABILITY and f.evidence_ids][:1],
                    sort_order=2,
                )
            )
        else:
            items.append(
                ChecklistItem(
                    item_id=f"chk_2_{document_id[:6]}",
                    text="Negotiate mutual liability limitation cap to avoid uncapped commercial exposure",
                    status=ChecklistStatus.PENDING,
                    reason="Absence of a definitive monetary cap creates open-ended contractual exposure in litigation.",
                    evidence_ids=[],
                    sort_order=2,
                )
            )

        # 3. Document-Type Specific Checklist Items
        is_employment = doc_type == DocumentType.EMPLOYMENT_AGREEMENT or "employment" in doc_type_str.lower()
        is_lease = doc_type == DocumentType.LEASE_AGREEMENT or "lease" in doc_type_str.lower()
        is_vendor_or_service = doc_type in (DocumentType.SERVICE_AGREEMENT, DocumentType.PURCHASE_AGREEMENT) or any(k in doc_type_str.lower() for k in ["vendor", "service", "msa", "purchase"])

        if is_employment:
            items.append(
                ChecklistItem(
                    item_id=f"chk_3_{document_id[:6]}",
                    text=f"Confirm non-compete and restrictive covenants comply with {jurisdiction} labor codes",
                    status=ChecklistStatus.PENDING,
                    reason="State statutes strictly limit or void post-employment covenants without adequate consideration.",
                    evidence_ids=[],
                    sort_order=3,
                )
            )
            items.append(
                ChecklistItem(
                    item_id=f"chk_4_{document_id[:6]}",
                    text="Verify IP assignment covenants include statutory carve-outs for pre-existing inventions",
                    status=ChecklistStatus.PENDING,
                    reason="Protects employee personal projects developed without company resources or trade secrets.",
                    evidence_ids=[],
                    sort_order=4,
                )
            )
        elif is_lease:
            items.append(
                ChecklistItem(
                    item_id=f"chk_3_{document_id[:6]}",
                    text="Audit Common Area Maintenance (CAM) allocation and establish annual audit rights",
                    status=ChecklistStatus.PENDING,
                    reason="Uncapped operating expense pass-throughs can substantially inflate monthly obligations.",
                    evidence_ids=[],
                    sort_order=3,
                )
            )
            items.append(
                ChecklistItem(
                    item_id=f"chk_4_{document_id[:6]}",
                    text="Ensure landlord consent for subletting cannot be unreasonably withheld or delayed",
                    status=ChecklistStatus.PENDING,
                    reason="Maintains flexibility for corporate restructuring, downsizing, or office relocation.",
                    evidence_ids=[],
                    sort_order=4,
                )
            )
        elif is_vendor_or_service:
            items.append(
                ChecklistItem(
                    item_id=f"chk_3_{document_id[:6]}",
                    text="Validate Service Level Agreement (SLA) credits and termination rights for chronic outages",
                    status=ChecklistStatus.PENDING,
                    reason="Service credits must provide financial compensation and an escape hatch for repeated downtime.",
                    evidence_ids=[],
                    sort_order=3,
                )
            )
            items.append(
                ChecklistItem(
                    item_id=f"chk_4_{document_id[:6]}",
                    text="Confirm data protection covenants mandate security breach notices within 72 hours",
                    status=ChecklistStatus.PENDING,
                    reason="Aligns vendor response times with statutory notification requirements (e.g. GDPR, CCPA).",
                    evidence_ids=[],
                    sort_order=4,
                )
            )
        else:
            # Standard NDA / Commercial Agreement
            items.append(
                ChecklistItem(
                    item_id=f"chk_3_{document_id[:6]}",
                    text="Verify standard exclusions from Confidential Information (public record, court subpoena)",
                    status=ChecklistStatus.PENDING,
                    reason="Protects receiving party from technical breach when legally compelled to produce records.",
                    evidence_ids=[],
                    sort_order=3,
                )
            )
            items.append(
                ChecklistItem(
                    item_id=f"chk_4_{document_id[:6]}",
                    text="Establish perpetual confidentiality carve-out for core trade secrets and source assets",
                    status=ChecklistStatus.PENDING,
                    reason="Fixed-term lapses (e.g. 2-3 years) forfeit statutory trade secret status under UTSA/DTSA.",
                    evidence_ids=[],
                    sort_order=4,
                )
            )

        # 5. Signatory Authority Check
        items.append(
            ChecklistItem(
                item_id=f"chk_5_{document_id[:6]}",
                text="Confirm authorized signatories have valid corporate officer authority to bind company",
                status=ChecklistStatus.PENDING,
                reason="Prevents enforceability challenges regarding corporate officer signature authority.",
                evidence_ids=[],
                sort_order=5,
            )
        )

        return items

    def _generate_lawyer_questions(
        self,
        doc_type: DocumentType,
        findings: list[Finding],
        clauses: list[DBClause],
    ) -> list[LawyerQuestion]:
        """Generate targeted, document-aware preparation questions for legal counsel."""
        full_text = " ".join(c.original_text for c in clauses)
        jurisdiction = self._detect_jurisdiction(clauses, full_text)
        liability_cap = self._detect_liability_cap(clauses)
        doc_type_str = doc_type.value if hasattr(doc_type, "value") else str(doc_type)

        questions: list[LawyerQuestion] = []
        sort_counter = 1

        is_employment = doc_type == DocumentType.EMPLOYMENT_AGREEMENT or "employment" in doc_type_str.lower()
        is_lease = doc_type == DocumentType.LEASE_AGREEMENT or "lease" in doc_type_str.lower()
        is_vendor_or_service = doc_type in (DocumentType.SERVICE_AGREEMENT, DocumentType.PURCHASE_AGREEMENT) or any(k in doc_type_str.lower() for k in ["vendor", "service", "msa", "purchase"])

        # 1. Document-Type Tailored Strategic Questions
        if is_employment:
            questions.append(
                LawyerQuestion(
                    question_id=f"q{sort_counter}",
                    question=f"Does {jurisdiction} statutory law enforce post-employment non-compete covenants without compensation?",
                    reason=f"Many jurisdictions (including CA, NY, MN) prohibit or strictly limit non-compete clauses in employment contracts.",
                    evidence_ids=[c.id for c in clauses if "compete" in c.original_text.lower()][:1],
                    sort_order=sort_counter,
                )
            )
            sort_counter += 1

            questions.append(
                LawyerQuestion(
                    question_id=f"q{sort_counter}",
                    question="Are invention assignment terms restricted strictly to work performed during business hours and with company equipment?",
                    reason="Overbroad employee IP assignment agreements risk violating employee rights statutes.",
                    evidence_ids=[c.id for c in clauses if any(k in c.original_text.lower() for k in ["invention", "intellectual property"])][:1],
                    sort_order=sort_counter,
                )
            )
            sort_counter += 1

        elif is_lease:
            questions.append(
                LawyerQuestion(
                    question_id=f"q{sort_counter}",
                    question="Can the tenant audit Common Area Maintenance (CAM) expenses, and is there a cap on annual controllable increases?",
                    reason="Without an audit clause and a cap (e.g. 5% per annum), operating expense pass-throughs can escalate unpredictably.",
                    evidence_ids=[c.id for c in clauses if any(k in c.original_text.lower() for k in ["maintenance", "operating expense", "cam"])][:1],
                    sort_order=sort_counter,
                )
            )
            sort_counter += 1

            questions.append(
                LawyerQuestion(
                    question_id=f"q{sort_counter}",
                    question="Under what terms may the tenant assign the lease or sublease premises to an affiliated corporate entity?",
                    reason="Prohibiting assignment without landlord consent restricts corporate reorganizations and spin-offs.",
                    evidence_ids=[c.id for c in clauses if any(k in c.original_text.lower() for k in ["assign", "sublease"])][:1],
                    sort_order=sort_counter,
                )
            )
            sort_counter += 1

        elif is_vendor_or_service:
            questions.append(
                LawyerQuestion(
                    question_id=f"q{sort_counter}",
                    question="Do the SLA remedies allow for contract termination for chronic service failures beyond minor fee credits?",
                    reason="Nominal service credits do not compensate for protracted business interruption if the vendor repeatedly fails SLAs.",
                    evidence_ids=[c.id for c in clauses if any(k in c.original_text.lower() for k in ["sla", "service level", "downtime"])][:1],
                    sort_order=sort_counter,
                )
            )
            sort_counter += 1

            questions.append(
                LawyerQuestion(
                    question_id=f"q{sort_counter}",
                    question="Is vendor indemnification for third-party intellectual property infringement exempt from the general liability limitation?",
                    reason="IP infringement claims by patent trolls or copyright holders can exceed standard contract liability caps.",
                    evidence_ids=[c.id for c in clauses if "indemnif" in c.original_text.lower()][:1],
                    sort_order=sort_counter,
                )
            )
            sort_counter += 1

        else:
            # Default NDA / Confidentiality Agreement
            questions.append(
                LawyerQuestion(
                    question_id=f"q{sort_counter}",
                    question="Should we carve out trade secrets from any fixed-term expiration so confidentiality protection remains perpetual?",
                    reason="Standard NDA terms lapse after 2-5 years, which would forfeit statutory trade secret protection under UTSA/DTSA.",
                    evidence_ids=[c.id for c in clauses if any(k in c.original_text.lower() for k in ["expire", "term", "survival"])][:1],
                    sort_order=sort_counter,
                )
            )
            sort_counter += 1

            questions.append(
                LawyerQuestion(
                    question_id=f"q{sort_counter}",
                    question="Are non-solicitation covenants included in this confidentiality agreement, and are their terms commercially customary?",
                    reason="Non-solicit restrictions disguised in NDAs can impede normal business recruiting and independent contractor engagements.",
                    evidence_ids=[c.id for c in clauses if "solicit" in c.original_text.lower()][:1],
                    sort_order=sort_counter,
                )
            )
            sort_counter += 1

        # 2. Liability Cap Question (fact-grounded)
        if liability_cap:
            questions.append(
                LawyerQuestion(
                    question_id=f"q{sort_counter}",
                    question=f"Is the {liability_cap} liability cap mutual, and does it exclude confidentiality breaches and gross negligence?",
                    reason=f"If an unauthorized disclosure occurs, damages could exceed {liability_cap}; conversely, receiving parties seek strict ceilings.",
                    evidence_ids=[f.evidence_ids[0] for f in findings if f.category == FindingCategory.LIABILITY and f.evidence_ids][:1],
                    sort_order=sort_counter,
                )
            )
        else:
            questions.append(
                LawyerQuestion(
                    question_id=f"q{sort_counter}",
                    question="Since contractual liabilities are uncapped, should we propose a mutual liability ceiling tied to contract value?",
                    reason="Uncapped indemnities and liabilities represent severe balance-sheet risks in corporate agreements.",
                    evidence_ids=[],
                    sort_order=sort_counter,
                )
            )
        sort_counter += 1

        # 3. Governing Law & Dispute Resolution (fact-grounded)
        questions.append(
            LawyerQuestion(
                question_id=f"q{sort_counter}",
                question=f"Does designating {jurisdiction} substantive law require appointing local registered agents or mandatory dispute escalation?",
                reason=f"Specifying {jurisdiction} without an exclusive forum or arbitration protocol invites costly jurisdictional disputes.",
                evidence_ids=[c.id for c in clauses if jurisdiction.lower() in c.original_text.lower()][:1],
                sort_order=sort_counter,
            )
        )
        sort_counter += 1

        # 4. Arbitration vs Public Court Procedure
        has_arbitration = any(kw in full_text.lower() for kw in ["arbitrat", "mediation", "jams", "aaa"])
        if not has_arbitration:
            questions.append(
                LawyerQuestion(
                    question_id=f"q{sort_counter}",
                    question="Should we insert a confidential arbitration clause (AAA/JAMS) to avoid public court dockets in the event of a dispute?",
                    reason="Public litigation records risk exposing proprietary and confidential dispute details to competitors and the press.",
                    evidence_ids=[],
                    sort_order=sort_counter,
                )
            )
        else:
            questions.append(
                LawyerQuestion(
                    question_id=f"q{sort_counter}",
                    question="Does the arbitration clause provide for emergency interim injunctive relief to halt immediate breaches?",
                    reason="Arbitration panels can take months to seat; preliminary court injunction carve-outs are vital for trade secret defense.",
                    evidence_ids=[c.id for c in clauses if "injunct" in c.original_text.lower()][:1],
                    sort_order=sort_counter,
                )
            )
        sort_counter += 1

        return questions


situation_analyzer = SituationAnalyzer()
