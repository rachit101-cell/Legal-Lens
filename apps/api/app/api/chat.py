"""
LegalLens API — Chat Endpoints.

Handle Q&A with documents, applying retrieval and evidence verification.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.base import generate_prefixed_uuid
from app.models.chat import ChatMessage, ChatSession, Claim, Evidence
from app.repositories.chat_repo import ChatRepository
from app.services.ai.generation import generation_pipeline
from app.services.evidence.verification_engine import verification_engine
from app.services.retrieval.retrieval_engine import RetrievalEngine
from packages.schemas.domain import ChatMessageRequest, ChatMessageResponse
from packages.schemas.enums import MessageRole, SupportStatus, VerificationStatus

logger = structlog.get_logger()
router = APIRouter(prefix="/chat", tags=["chat"])


from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    document_id: str
    owner_id: str = "demo_user"


class CreateSessionResponse(BaseModel):
    session_id: str


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_chat_session(
    request: CreateSessionRequest, db: AsyncSession = Depends(get_db_session)
) -> CreateSessionResponse:
    """Create a new chat session for a document."""
    chat_repo = ChatRepository(db)
    session = ChatSession(document_id=request.document_id, owner_id=request.owner_id)
    await chat_repo.create_session(session)
    return CreateSessionResponse(session_id=session.id)


@router.post("/{session_id}/message", response_model=ChatMessageResponse)
async def send_message(
    session_id: str, request: ChatMessageRequest, db: AsyncSession = Depends(get_db_session)
) -> ChatMessageResponse:
    """
    Send a message to a chat session.
    Retrieves context, generates answer, verifies claims, and saves everything.
    """
    chat_repo = ChatRepository(db)

    # 1. Fetch Session
    session = await chat_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # 2. Save User Message
    user_msg = ChatMessage(
        id=generate_prefixed_uuid("msg"),
        session_id=session_id,
        role=MessageRole.USER,
        content=request.message,
    )
    await chat_repo.save_message(user_msg)

    # 3. Retrieve Context
    retrieval_engine = RetrievalEngine(db)
    retrieved_clauses = await retrieval_engine.search(
        document_id=session.document_id,
        query=request.message,
        top_k=5,
    )

    # 4. Generate Answer
    response_schema = await generation_pipeline.generate_answer(
        question=request.message,
        retrieved_clauses=retrieved_clauses,
    )

    # 5. Save AI Message
    ai_msg = ChatMessage(
        id=generate_prefixed_uuid("msg"),
        session_id=session_id,
        role=MessageRole.ASSISTANT,
        content=response_schema.answer,
        answer_status=response_schema.answer_status,
        limitations=response_schema.limitations,
    )
    await chat_repo.save_message(ai_msg)

    # 6. Verify Claims and Create Evidence
    db_claims = []
    db_evidence = []

    # Create a lookup for retrieved clauses by ID
    clause_lookup = {c.id: c for c in retrieved_clauses}

    for citation in response_schema.citations:
        # Resolve clauses for this citation
        cited_clauses = []
        for c_id in citation.source_ids:
            if c_id in clause_lookup:
                cited_clauses.append(clause_lookup[c_id])

        # Run Verification
        support_status, notes = verification_engine.verify_claim(
            claim_text=citation.claim,
            evidence_clauses=cited_clauses,
        )

        # Save Claim
        claim_record = Claim(
            id=generate_prefixed_uuid("clm"),
            message_id=ai_msg.id,
            claim=citation.claim,
            supporting_evidence=citation.source_ids,
            support_status=support_status,
            verification_notes=notes,
        )
        db_claims.append(claim_record)

        # Save Evidence mapping back to the clauses/document
        # (For MVP, we just create generic Evidence items. In full app, we map char_start/bbox)
        for clause in cited_clauses:
            ev = Evidence(
                id=generate_prefixed_uuid("evd"),
                document_id=session.document_id,
                page_number=clause.page_start,
                section_id=clause.section_id,
                clause_id=clause.id,
                quote=clause.original_text,
                quote_hash="TODO_HASH",  # MVP Stub
                verification_status=VerificationStatus.VERIFIED
                if support_status == SupportStatus.SUPPORTED
                else VerificationStatus.REJECTED,
            )
            db_evidence.append(ev)

    await chat_repo.save_claims(db_claims)
    await chat_repo.save_evidence(db_evidence)

    logger.info("chat_message_processed", session_id=session_id, ai_message_id=ai_msg.id)

    return response_schema
