"""
LegalLens API — Generation Pipeline.

Orchestrates prompts, context, and the model adapter.
"""

from __future__ import annotations

import structlog

from app.models.analysis import Clause
from app.services.ai.adapter import model_adapter
from app.services.ai.prompts import get_prompt
from packages.schemas.domain import ChatMessageResponse, Citation

logger = structlog.get_logger()


class GenerationPipeline:
    """Pipeline for generating answers to legal queries."""

    async def generate_answer(
        self,
        question: str,
        retrieved_clauses: list[Clause],
        prompt_id: str = "chat_qa_v1",
    ) -> ChatMessageResponse:
        """
        Generate a ChatMessageResponse using retrieved context.
        """
        prompt_data = get_prompt(prompt_id)
        system_prompt = prompt_data["system"]
        
        # Format context
        context_parts = []
        for i, clause in enumerate(retrieved_clauses):
            context_parts.append(
                f"--- Clause {i+1} ---\n"
                f"ID: {clause.id}\n"
                f"Text: {clause.original_text}\n"
            )
        context_str = "\n".join(context_parts)
        
        user_prompt = prompt_data["user_template"].format(
            context=context_str,
            question=question
        )
        
        logger.info("generation_pipeline_started", question=question, context_chunks=len(retrieved_clauses))
        
        # Call the adapter expecting the canonical ChatMessageResponse schema
        response = await model_adapter.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=ChatMessageResponse,
            temperature=0.0,
        )
        
        logger.info("generation_pipeline_completed", answer_status=response.answer_status)
        
        return response

generation_pipeline = GenerationPipeline()
