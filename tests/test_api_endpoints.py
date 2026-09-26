"""
LegalLens — Unit and Integration Tests for API Endpoints & Security Controls.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI TestClient fixture with mocked database session."""
    mock_session = AsyncMock()
    app.dependency_overrides[get_db_session] = lambda: mock_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check_endpoint(client: TestClient):
    """Health check endpoint should return 200 OK and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert "version" in data
    assert "request_id" in data


def test_security_headers_present(client: TestClient):
    """Responses must contain OWASP defense-in-depth HTTP security headers."""
    response = client.get("/health")
    headers = response.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "default-src 'self'" in headers.get("Content-Security-Policy", "")
    assert "X-Request-ID" in headers


def test_consistent_404_no_enumeration(client: TestClient):
    """404 responses must follow uniform structure to prevent resource enumeration."""
    response = client.get("/api/v1/invalid_non_existent_route")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "request_id" in data


def test_upload_reject_disallowed_extension(client: TestClient):
    """Uploading executable or unsupported file extension should return 415."""
    file_content = b"echo 'malicious script'"
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("malware.sh", file_content, "application/x-sh")},
    )
    assert response.status_code == 415
    assert "Accepted types" in response.text or "Unsupported" in response.text


def test_upload_reject_empty_file(client: TestClient):
    """Uploading an empty file should return 422 Unprocessable Entity."""
    empty_pdf = b""
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("empty.pdf", empty_pdf, "application/pdf")},
    )
    assert response.status_code == 422
    assert "empty" in response.text.lower()


def test_upload_reject_spoofed_pdf_magic_bytes(client: TestClient):
    """Uploading a file named .pdf with non-PDF magic bytes should return 422."""
    fake_pdf = b"NOT_A_REAL_PDF_HEADER"
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("fake.pdf", fake_pdf, "application/pdf")},
    )
    assert response.status_code == 422
    assert "PDF format" in response.text or "magic" in response.text.lower()
