"""
prompts.py — Prompt construction for PKA-AI.

Responsibility: build the final string handed to the LLM.
No retrieval. No LLM calls. Pure string assembly.

Keeping this isolated means the prompt can be iterated, tested,
and version-controlled without touching retrieval or generation logic.
"""

# ── Constants ─────────────────────────────────────────────────────────────────

CONTEXT_HEADER = "Context:"
QUESTION_HEADER = "Question:"
ANSWER_HEADER = "Answer:"

NO_CONTEXT_REPLY = "I don't know based on the provided context."

SYSTEM_PROMPT = """\
You are a helpful personal knowledge assistant.

Rules:
- Answer using ONLY the information provided in the context below.
- Do NOT use outside knowledge or assumptions.
- If the answer cannot be found in the context, respond with exactly:
  "{no_context_reply}"
- Be concise and direct. Cite the source when it helps the user.
""".format(no_context_reply=NO_CONTEXT_REPLY)


# ── Context Formatting ────────────────────────────────────────────────────────

def format_context_block(chunks: list[dict]) -> str:
    """
    Renders a list of retrieved chunk dicts into a single context string.

    Each chunk dict is expected to have:
        text     : str   — the raw chunk content
        metadata : dict  — at minimum {"source": str, "chunk_index": int}

    Chunks are numbered so the LLM (and the user, in logs) can reference them.

    Example output:
        [1] Source: notes.md (chunk 3)
        ---
        ...chunk text...

        [2] Source: review.md (chunk 0)
        ---
        ...chunk text...
    """
    if not chunks:
        return "(No context retrieved.)"

    lines = []
    for i, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source", "unknown")
        chunk_index = metadata.get("chunk_index", "?")

        lines.append(f"[{i}] Source: {source} (chunk {chunk_index})")
        lines.append("---")
        lines.append(chunk.get("text", "").strip())
        lines.append("")          # blank line between chunks

    return "\n".join(lines).strip()


# ── Prompt Builder ────────────────────────────────────────────────────────────

def build_rag_prompt(question: str, chunks: list[dict]) -> str:
    """
    Assembles the full user-turn prompt from a question and retrieved chunks.

    Args:
        question : The user's natural-language question.
        chunks   : Top-k chunk dicts returned by semantic_search().

    Returns:
        A complete prompt string ready to pass to generate_chat_response().

    The system prompt (SYSTEM_PROMPT) is kept separate — it is passed as the
    system role in llm.generate_chat_response(), not embedded here.
    This preserves the system/user role separation expected by chat models.
    """
    context_block = format_context_block(chunks)

    return (
        f"{CONTEXT_HEADER}\n"
        f"{context_block}\n\n"
        f"{QUESTION_HEADER}\n"
        f"{question.strip()}\n\n"
        f"{ANSWER_HEADER}"
    )