"""
LegalLens API — Chat Repository.

Data access layer for chat sessions, messages, and claims.
"""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatMessage, ChatSession, Claim, Evidence


class ChatRepository:
    """Repository for Chat and Evidence entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_session(self, chat_session: ChatSession) -> ChatSession:
        """Create a new chat session."""
        self.session.add(chat_session)
        await self.session.commit()
        await self.session.refresh(chat_session)
        return chat_session

    async def get_session(self, session_id: str) -> ChatSession | None:
        """Get a chat session by ID."""
        result = await self.session.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def save_message(self, message: ChatMessage) -> ChatMessage:
        """Save a new chat message."""
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_messages(self, session_id: str) -> Sequence[ChatMessage]:
        """Get all messages for a session."""
        result = await self.session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        )
        return result.scalars().all()

    async def save_claims(self, claims: list[Claim]) -> None:
        """Bulk save claims."""
        self.session.add_all(claims)
        await self.session.commit()

    async def save_evidence(self, evidence_list: list[Evidence]) -> None:
        """Bulk save evidence."""
        self.session.add_all(evidence_list)
        await self.session.commit()

    async def get_claims_for_message(self, message_id: str) -> Sequence[Claim]:
        """Get claims associated with a specific message."""
        result = await self.session.execute(
            select(Claim).where(Claim.message_id == message_id)
        )
        return result.scalars().all()
