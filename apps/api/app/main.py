"""
LegalLens API — FastAPI Application Entry Point.

Creates the FastAPI app with middleware, routers, exception handlers,
CORS configuration, and health endpoints.
"""

from __future__ import annotations

import os
import sys
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

# Add the root workspace directory so 'packages' can be found
root_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Fix for psycopg on Windows with asyncio — must happen before any async imports
if sys.platform == "win32":
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # Force UTF-8 for standard output to prevent 'charmap' encoding errors in logging
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle."""
    settings = get_settings()
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )
    yield
    logger.info("application_shutting_down")


def _add_cors_headers(response: JSONResponse, request: Request) -> JSONResponse:
    """Manually add CORS headers to error responses."""
    settings = get_settings()
    origin = request.headers.get("origin", "")
    if origin in settings.cors_origins:
        response.headers["access-control-allow-origin"] = origin
        response.headers["access-control-allow-credentials"] = "true"
        response.headers["vary"] = "Origin"
    return response


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="LegalLens API",
        description="AI Legal Document Risk & Action Navigator",
        version=settings.app_version,
        docs_url="/api/docs" if settings.is_development else None,
        redoc_url="/api/redoc" if settings.is_development else None,
        openapi_url="/api/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # ── Request ID Middleware ────────────────────────────────
    @app.middleware("http")
    async def add_request_id(request: Request, call_next: object) -> Response:
        """Add a unique request ID to every request/response."""
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)  # type: ignore[misc]
        response.headers["X-Request-ID"] = request_id
        return response  # type: ignore[return-value]

    # ── Security Headers Middleware (OWASP Defense-in-Depth) ─
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next: object) -> Response:
        """Enforce strict browser defense-in-depth security headers."""
        response = await call_next(request)  # type: ignore[misc]
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
        if not settings.is_development:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response  # type: ignore[return-value]

    # ── Rate Limiting Middleware ─────────────────────────────
    # In-memory sliding window rate limiter per client IP
    import time
    from collections import defaultdict

    ip_request_timestamps: dict[str, list[float]] = defaultdict(list)

    @app.middleware("http")
    async def rate_limiting_middleware(request: Request, call_next: object) -> Response:
        """Protect API from abuse and denial of service."""
        # Skip health check endpoints from rate limiting
        if request.url.path in ("/health", "/api/v1/health"):
            return await call_next(request)  # type: ignore[misc]

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60.0

        # Purge older requests outside the 60s window
        timestamps = [t for t in ip_request_timestamps[client_ip] if t > window_start]
        timestamps.append(now)
        ip_request_timestamps[client_ip] = timestamps

        # Enforce rate limit (allowing a generous burst threshold for tests/dev, e.g. max(120, settings.rate_limit_per_minute * 4))
        max_allowed = max(120, settings.rate_limit_per_minute * 4)
        if len(timestamps) > max_allowed:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.warning("rate_limit_exceeded", client_ip=client_ip, request_id=request_id)
            err_resp = JSONResponse(
                status_code=429,
                content={
                    "request_id": request_id,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please slow down.",
                    },
                },
                headers={"Retry-After": "60"},
            )
            return _add_cors_headers(err_resp, request)

        return await call_next(request)  # type: ignore[misc]

    # ── Exception Handlers ──────────────────────────────────
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: object) -> JSONResponse:
        """Return consistent 404 response (prevents enumeration)."""
        request_id = getattr(request.state, "request_id", "unknown")
        response = JSONResponse(
            status_code=404,
            content={
                "request_id": request_id,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "The requested resource was not found.",
                },
            },
        )
        return _add_cors_headers(response, request)

    @app.exception_handler(Exception)
    async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Return safe 500 response without internal stack trace leakage."""
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(
            "unhandled_error",
            request_id=request_id,
            path=request.url.path,
            error=str(exc),
        )
        safe_message = (
            f"An unexpected error occurred: {exc!s}"
            if settings.is_development
            else "An internal server error occurred. Please try again later or contact support."
        )
        response = JSONResponse(
            status_code=500,
            content={
                "request_id": request_id,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": safe_message,
                },
            },
        )
        return _add_cors_headers(response, request)

    # ── Register Routers ────────────────────────────────────
    from app.api.analysis import router as analysis_router
    from app.api.chat import router as chat_router
    from app.api.documents import router as documents_router
    from app.api.health import router as health_router

    app.include_router(health_router)
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(analysis_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")

    return app


# Create the application instance
app = create_app()
