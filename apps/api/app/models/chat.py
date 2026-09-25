"""
LegalLens API — Chat and Evidence SQLAlchemy Models.

Models for user chat sessions, messages, evidence, and claims.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import BigInteger, Float, String, text
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, generate_prefixed_uuid
from packages.schemas.enums import (
    AnswerStatus,
    MessageRole,
    SourceType,
    SupportStatus,
    VerificationStatus,
)


class Evidence(Base, TimestampMixin):
    """A piece of evidence from the source document."""
    
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: generate_prefixed_uuid("evd"),
    )
    document_id: Mapped[str] = mapped_column(String, index=True)
    page_number: Mapped[int] = mapped_column(BigInteger)
    
    section_id: Mapped[str | None] = mapped_column(String, nullable=True)
    clause_id: Mapped[str | None] = mapped_column(String, nullable=True)
    
    quote: Mapped[str] = mapped_column(String)
    quote_hash: Mapped[str] = mapped_column(String, index=True)
    
    char_start: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    char_end: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    bbox: Mapped[list[float] | None] = mapped_column(JSONB, nullable=True)
    
    source_type: Mapped[str] = mapped_column(
        ENUM(SourceType, name="source_type_enum", create_type=False),
        default=SourceType.USER_DOCUMENT,
    )
    verification_status: Mapped[str] = mapped_column(
        ENUM(VerificationStatus, name="verification_status_enum", create_type=False),
        default=VerificationStatus.PENDING,
    )


class Claim(Base, TimestampMixin):
    """A claim with supporting evidence and verification status."""
    
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: generate_prefixed_uuid("clm"),
    )
    analysis_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    message_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    
    claim: Mapped[str] = mapped_column(String)
    supporting_evidence: Mapped[list[str]] = mapped_column(JSONB, default=list)
    
    support_status: Mapped[str] = mapped_column(
        ENUM(SupportStatus, name="support_status_enum", create_type=False),
        nullable=False,
    )
    verification_notes: Mapped[str | None] = mapped_column(String, nullable=True)


class ChatSession(Base, TimestampMixin):
    """A chat session for a document."""
    
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: generate_prefixed_uuid("ses"),
    )
    document_id: Mapped[str] = mapped_column(String, index=True)
    owner_id: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)


class ChatMessage(Base, TimestampMixin):
    """A single message within a chat session."""
    
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: generate_prefixed_uuid("msg"),
    )
    session_id: Mapped[str] = mapped_column(String, index=True)
    
    role: Mapped[str] = mapped_column(
        ENUM(MessageRole, name="message_role_enum", create_type=False),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(String)
    
    answer_status: Mapped[str | None] = mapped_column(
        ENUM(AnswerStatus, name="answer_status_enum", create_type=False),
        nullable=True,
    )
    
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    limitations: Mapped[list[str]] = mapped_column(JSONB, default=list)
