"""
LegalLens API — Embedding Service.

Generates dense vector embeddings for clauses and queries.
"""

from __future__ import annotations

import structlog

# In production, we'd use OpenAI, Cohere, or a local SentenceTransformer model.
# from sentence_transformers import SentenceTransformer
# import openai

logger = structlog.get_logger()

class EmbeddingService:
    """Service to generate dense vector embeddings."""

    def __init__(self) -> None:
        # e.g., self.model = SentenceTransformer("all-MiniLM-L6-v2")
        pass

    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.
        For MVP stub, returns a fake zero-vector of size 1536 (OpenAI size).
        """
        # return self.model.encode(text).tolist()
        return [0.0] * 1536

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.
        """
        return [self.embed_text(t) for t in texts]

# Singleton
embedding_service = EmbeddingService()
