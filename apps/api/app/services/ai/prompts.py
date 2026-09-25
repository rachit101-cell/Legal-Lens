"""
LegalLens API — Prompt Library.

Versioned prompts for LLM interactions.
"""

from __future__ import annotations

# We use simple dictionaries or classes to version our prompts.
# This makes it easy to track prompt regressions.

PROMPTS = {
    "chat_qa_v1": {
        "system": """You are an expert legal assistant. 
Your primary job is to answer questions about a provided legal document based ONLY on the provided context.
You must be precise, professional, and deterministic. Do not hallucinate.

Rules:
1. Base your answer strictly on the provided context clauses.
2. If the context does not contain the answer, explicitly state that you cannot answer based on the provided document.
3. You must provide citations for every claim you make, referencing the specific clause_id from the context.
4. Structure your output exactly according to the provided schema.
""",
        "user_template": """
Context from document:
{context}

User Question:
{question}
"""
    }
}

def get_prompt(prompt_id: str) -> dict[str, str]:
    """Retrieve a prompt template by ID."""
    if prompt_id not in PROMPTS:
        raise ValueError(f"Prompt ID {prompt_id} not found.")
    return PROMPTS[prompt_id]
