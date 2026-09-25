"""
LegalLens API — Model Adapter.

Abstracts the LLM API calls and enforces structured Pydantic output.
"""

from __future__ import annotations

from typing import Any, Type, TypeVar

import structlog
from pydantic import BaseModel

import openai
from app.core.config import get_settings

logger = structlog.get_logger()

from fastapi.concurrency import run_in_threadpool
import requests

T = TypeVar("T", bound=BaseModel)

class ModelAdapter:
    """Adapter for interacting with the generative AI model."""

    def __init__(self, model_name: str | None = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.llm_model
        self.api_base = settings.llm_api_base
        self.api_key = settings.llm_api_key

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float = 0.0,
    ) -> T:
        logger.info(
            "llm_generation_started",
            model=self.model_name,
            target_schema=response_model.__name__,
        )
        
        schema_json = response_model.model_json_schema()
        system_prompt = f"{system_prompt}\n\nYou MUST respond in valid JSON format adhering exactly to this JSON schema:\n{schema_json}"
        
        try:
            def _call_api():
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": temperature,
                }
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                if not response.ok:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                return response.json()
            
            completion = await run_in_threadpool(_call_api)
            
            content = completion["choices"][0]["message"]["content"]
            return response_model.model_validate_json(content)
            
        except Exception as e:
            logger.error("llm_generation_failed", error=str(e))
            raise

model_adapter = ModelAdapter()
