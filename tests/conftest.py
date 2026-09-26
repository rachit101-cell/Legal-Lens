"""
LegalLens — Pytest Global Configuration & Shared Fixtures.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Ensure repository root and apps/api are in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
API_ROOT = REPO_ROOT / "apps" / "api"

for p in (str(REPO_ROOT), str(API_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture
def sample_nda_text() -> str:
    """Load the golden set sample NDA text."""
    nda_path = REPO_ROOT / "tests" / "golden_set" / "sample_nda.txt"
    if nda_path.exists():
        return nda_path.read_text(encoding="utf-8")
    return (
        "NON-DISCLOSURE AGREEMENT\n\n"
        "This Non-Disclosure Agreement is entered into on October 1, 2026, by and between ACME Corp and Beta LLC.\n\n"
        "1. Definition of Confidential Information\n"
        "Confidential Information means any proprietary information provided by the Disclosing Party.\n\n"
        "2. Term\n"
        "Obligations shall expire three (3) years from disclosure.\n\n"
        "3. Governing Law\n"
        "Governed by the laws of the State of Delaware.\n\n"
        "4. Liability\n"
        "The maximum liability under this agreement shall not exceed $2,000,000.\n"
    )


@pytest.fixture
def mock_clause():
    """Create a mock clause object for unit tests."""
    clause = MagicMock()
    clause.id = "clause_1"
    clause.document_id = "doc_123"
    clause.analysis_id = "analysis_123"
    clause.text = "The maximum liability under this agreement shall not exceed $2,000,000."
    clause.original_text = clause.text
    clause.clause_type = "LIABILITY_INDEMNITY"
    clause.page_number = 1
    return clause
