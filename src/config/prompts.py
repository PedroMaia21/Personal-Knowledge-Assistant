# src/config/prompts.py
"""
prompts.py — Prompt construction for PKA-AI.

Responsibility: build the final string handed to the LLM.
No retrieval. No LLM calls. Pure string assembly.

Keeping this isolated means the prompt can be iterated, tested,
and version-controlled without touching retrieval or generation logic.

Section order in the final prompt:

    Conversation History   (optional — only if prior turns exist)
    Relevant Context       (retrieved chunks)
    Current Question

Conversation history and retrieved context are kept as two distinct
blocks, built by two distinct functions, and never merged into a
single list. This preserves the separation of concerns between
"what was said" and "what was retrieved".
"""

# ── Constants ─────────────────────────────────────────────────────────────────

CONVERSATION_HEADER = "Conversation History:"
CONTEXT_HEADER = "Relevant Context:"
QUESTION_HEADER = "Current Question:"
ANSWER_HEADER = "Answer:"

NO_CONTEXT_REPLY = "I don't know based on the provided context."

SYSTEM_PROMPT = """\
You are a helpful personal knowledge assistant.

Rules:
- Answer using ONLY the information provided in the context below.
- Do NOT use outside knowledge or assumptions.
- If the answer cannot be found in the context, respond with exactly:
  "{no_context_reply}"
- Use the conversation history only to resolve references (e.g. "it",
  "that", "the previous answer") — never as a source of facts that
  aren't also in the retrieved context.
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


# ── Conversation Formatting ────────────────────────────────────────────────────

def format_conversation_block(history: list[dict] | None) -> str:
    """
    Renders prior question/answer pairs into a single conversation string.

    Each history entry is expected to have the shape produced by
    ConversationMemory.add():
        {"question": str, "answer": str}

    Returns "" (empty string) when there is no history, so callers can
    skip the whole section instead of printing an empty header.

    Example output:
        User: What is RAG?
        Assistant: Retrieval Augmented Generation combines...

        User: How is it different from fine-tuning?
        Assistant: Unlike fine-tuning, RAG doesn't change model weights...
    """
    if not history:
        return ""

    lines = []
    for turn in history:
        lines.append(f"User: {turn.get('question', '').strip()}")
        lines.append(f"Assistant: {turn.get('answer', '').strip()}")
        lines.append("")

    return "\n".join(lines).strip()


# ── Prompt Builder ────────────────────────────────────────────────────────────

def build_rag_prompt(
    question: str,
    chunks: list[dict],
    history: list[dict] | None = None,
) -> str:
    """
    Assembles the full user-turn prompt from a question, retrieved chunks,
    and (optionally) prior conversation turns.

    Args:
        question : The user's natural-language question.
        chunks   : Top-k chunk dicts returned by semantic_search().
        history  : Prior exchanges from ConversationMemory.get_history(),
                   or None / [] for a single-turn call. Backward compatible —
                   existing callers that don't pass `history` behave exactly
                   as before, minus the reordered section headers.

    Returns:
        A complete prompt string ready to pass to generate_chat_response().

    The system prompt (SYSTEM_PROMPT) is kept separate — it is passed as the
    system role in llm.generate_chat_response(), not embedded here.
    This preserves the system/user role separation expected by chat models.

    Conversation history is never merged into the `chunks` list or the
    context block — it is rendered as its own section so retrieval
    provenance stays unambiguous.
    """
    context_block = format_context_block(chunks)
    conversation_block = format_conversation_block(history)

    sections = []

    if conversation_block:
        sections.append(f"{CONVERSATION_HEADER}\n{conversation_block}")

    sections.append(f"{CONTEXT_HEADER}\n{context_block}")
    sections.append(f"{QUESTION_HEADER}\n{question.strip()}")
    sections.append(ANSWER_HEADER)

    return "\n\n".join(sections)