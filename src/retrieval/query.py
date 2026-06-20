"""
query.py — RAG pipeline orchestrator for PKA-AI.

Responsibility: wire retrieval → prompt → generation into one callable.
Each step stays in its own module; this file only coordinates them.

Pipeline:
    question
        ↓  search.semantic_search()
    top-k chunks
        ↓  prompts.build_rag_prompt()
    prompt string
        ↓  llm.generate_chat_response()
    answer string
"""

import logging

from src.retrieval.search import semantic_search
from src.config.prompts import build_rag_prompt, format_context_block, SYSTEM_PROMPT
from src.config.config import DEFAULT_TOP_K
from src.models.llm import generate_chat_response
from src.utils.logging import log_retrieval

logger = logging.getLogger(__name__)


def answer_question(question: str, top_k: int = DEFAULT_TOP_K) -> dict:
    """
    End-to-end RAG query: retrieve → build prompt → generate answer.

    Args:
        question : Natural-language question from the user.
        top_k    : Number of chunks to retrieve (default 5).

    Returns:
        A dict with:
            answer   : str   — the LLM-generated answer
            chunks   : list  — the raw retrieved chunk dicts (for attribution)
            prompt   : str   — the exact prompt sent to the LLM (for debugging)
    """
    # ── Step 1: Retrieve relevant chunks ──────────────────────────────────────
    logger.info(f"Retrieving top-{top_k} chunks for question: {question!r}")
    chunks = semantic_search(question, top_k=top_k)

    # Log retrieval details (chunk IDs, sources, scores) for observability
    log_retrieval(question, chunks)

    # ── Step 2: Build prompt ───────────────────────────────────────────────────
    prompt = build_rag_prompt(question, chunks)
    logger.debug(f"Prompt built ({len(prompt)} chars)")

    # ── Step 3: Generate answer ────────────────────────────────────────────────
    logger.info("Sending prompt to LLM...")
    answer = generate_chat_response(prompt, system_override=SYSTEM_PROMPT)

    return {
        "answer": answer,
        "chunks": chunks,
        "prompt": prompt,
    }