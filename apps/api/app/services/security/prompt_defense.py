"""
LegalLens API — Prompt Injection Defense.

Scans incoming user inputs for common prompt injection patterns before
they reach the LLM.
"""

from __future__ import annotations

import re

import structlog

logger = structlog.get_logger()

# Common patterns used to jailbreak or inject prompts
INJECTION_PATTERNS = [
    r"(?i)ignore\s+all\s+previous\s+instructions",
    r"(?i)system\s+override",
    r"(?i)you\s+are\s+now",
    r"(?i)forget\s+that\s+you\s+are",
    r"(?i)disregard\s+the\s+above",
    r"(?i)print\s+your\s+instructions",
]


class PromptDefense:
    """Service to defend against prompt injection."""

    def __init__(self) -> None:
        self.compiled_patterns = [re.compile(p) for p in INJECTION_PATTERNS]

    def is_safe(self, user_input: str) -> bool:
        """
        Check if the user input contains known injection patterns.
        """
        for pattern in self.compiled_patterns:
            if pattern.search(user_input):
                logger.warning("prompt_injection_detected", matched_pattern=pattern.pattern)
                return False
        return True


prompt_defense = PromptDefense()
