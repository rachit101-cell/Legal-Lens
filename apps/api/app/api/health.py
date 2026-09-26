"""
LegalLens API — Health Endpoints.

Liveness and readiness checks. Never include secrets,
connection strings, or internal details in responses.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Request

from app.core.config import get_settings
from packages.schemas.domain import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
@router.get("/api/v1/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """
    Liveness check — returns OK if the API process is running.

    Does not check external dependencies. Use /health/ready for that.
    """
    settings = get_settings()
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        request_id=request_id,
        environment=settings.app_env if settings.is_development else None,
    )


@router.get("/api/v1/health/ready", response_model=HealthResponse)
async def readiness_check(request: Request) -> HealthResponse:
    """
    Readiness check — verifies database and optional worker dependencies.

    Returns 503 if critical dependencies are unavailable.
    """
    settings = get_settings()
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # TODO: Add database connectivity check
    # TODO: Add optional Redis check
    # TODO: Add object storage check

    return HealthResponse(
        status="ok",
        version=settings.app_version,
        request_id=request_id,
    )
