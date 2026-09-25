"""
LegalLens API — Document SQLAlchemy Models.

Models for the core document structures (Documents, Pages, Sections).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import BigInteger, Float, String, text
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, generate_prefixed_uuid
from packages.schemas.enums import DocumentStatus, DocumentType, TextSource


class Document(Base, TimestampMixin):
    """A legal document uploaded by a user."""
    
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: generate_prefixed_uuid("doc"),
    )
    owner_id: Mapped[str] = mapped_column(String, index=True)
    filename: Mapped[str] = mapped_column(String)
    mime_type: Mapped[str] = mapped_column(String)
    sha256: Mapped[str] = mapped_column(String, index=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    
    # ENUM types for PostgreSQL
    status: Mapped[str] = mapped_column(
        ENUM(DocumentStatus, name="document_status_enum", create_type=False),
        nullable=False,
        default=DocumentStatus.QUEUED,
        index=True,
    )
    document_type: Mapped[str | None] = mapped_column(
        ENUM(DocumentType, name="document_type_enum", create_type=False),
        nullable=True,
    )
    
    language: Mapped[str] = mapped_column(String, default="en")
    page_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    
    # Storage reference
    storage_path: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Optional references
    analysis_id: Mapped[str | None] = mapped_column(String, nullable=True)
    deleted_at: Mapped[Any | None] = mapped_column(
        JSONB, nullable=True
    )  # JSONB for soft delete if needed, or just standard timestamp


class Page(Base, TimestampMixin):
    """A page within a document."""
    
    __tablename__ = "pages"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: generate_prefixed_uuid("pg"),
    )
    document_id: Mapped[str] = mapped_column(String, index=True)
    page_number: Mapped[int] = mapped_column(BigInteger, index=True)
    
    text: Mapped[str] = mapped_column(String)
    text_source: Mapped[str] = mapped_column(
        ENUM(TextSource, name="text_source_enum", create_type=False),
        default=TextSource.NATIVE_TEXT,
    )
    ocr_quality: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    width: Mapped[float | None] = mapped_column(Float, nullable=True)
    height: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Store blocks as JSONB for spatial rendering
    blocks: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    content_hash: Mapped[str] = mapped_column(String)


class Section(Base, TimestampMixin):
    """A logical section within a document."""
    
    __tablename__ = "sections"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: generate_prefixed_uuid("sec"),
    )
    document_id: Mapped[str] = mapped_column(String, index=True)
    parent_section_id: Mapped[str | None] = mapped_column(String, nullable=True)
    
    number: Mapped[str | None] = mapped_column(String, nullable=True)
    heading: Mapped[str | None] = mapped_column(String, nullable=True)
    
    page_start: Mapped[int] = mapped_column(BigInteger)
    page_end: Mapped[int] = mapped_column(BigInteger)
