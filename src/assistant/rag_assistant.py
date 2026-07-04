# src/assistant/rag_assistant.py
"""
rag_assistant.py — RAG pipeline orchestrator for PKA-AI.

Wires retrieval → context building → prompt → LLM generation into
one injectable, testable class. Now also wires in short-term
conversation memory.

Pipeline:
    question
        ↓  retriever.retrieve()
    top-k chunks
        ↓  prompt_builder.build(chunks, question, history)  ← memory injected here
    prompt string
        ↓  llm_client.generate()
    answer string + sources
        ↓  memory.add(question, answer)

Dependencies are injected via __init__, so each component — including
memory — can be swapped or mocked independently in tests.

Conversation memory and retrieved chunks remain separate concerns:
memory only ever stores/returns {"question", "answer"} pairs and knows
nothing about chunks, sources, or embeddings.
"""

import logging

from src.assistant.memory import ConversationMemory

logger = logging.getLogger(__name__)


class RAGAssistant:
    """
    End-to-end RAG assistant with short-term conversation memory.

    Args:
        retriever      — Any object with a .retrieve(question, k) method.
                         Expected to return a list of chunk dicts:
                         [{"text": str, "metadata": dict, ...}, ...]

        prompt_builder — Any object with a .build(chunks, question, history)
                         method. Expected to return a prompt string.
                         Receives raw chunk dicts (not pre-joined text) so it
                         can embed source labels via format_context_block(),
                         and raw history pairs via format_conversation_block().

        llm_client     — Any object with a .generate(prompt) method.
                         Expected to return an answer string.

        memory         — Optional ConversationMemory instance. Defaults to a
                         fresh one (empty history) if not provided. Inject
                         a shared instance to persist history across
                         multiple RAGAssistant calls within the same session.
    """

    def __init__(self, retriever, prompt_builder, llm_client, memory: ConversationMemory | None = None):
        self.retriever = retriever
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client
        self.memory = memory if memory is not None else ConversationMemory()

    # ── Public API ────────────────────────────────────────────────────────────

    def ask(self, question: str, k: int = 5) -> dict:
        """
        Run the full RAG pipeline for a single question, using and then
        updating conversation memory.

        Args:
            question : Natural-language question from the user.
            k        : Number of chunks to retrieve (default 5).

        Returns:
            A dict with:
                answer  : str   — the LLM-generated answer
                chunks  : list  — raw retrieved chunk dicts (for attribution)
                prompt  : str   — the exact prompt sent to the LLM (for debugging)
                sources : list  — deduplicated [{file, chunk_index}] for display
        """
        # Step 1 — Retrieve relevant chunks (retrieval is unaffected by memory)
        logger.info(f"[RAGAssistant] Retrieving top-{k} chunks...")
        chunks = self.retriever.retrieve(question, k=k)

        logger.debug("QUESTION\n%s", question)
        logger.debug("CHUNKS\n%s", chunks)

        # Step 2 — Build prompt (chunks + prior turns, kept as separate sections)
        logger.info("[RAGAssistant] Building prompt...")
        history = self.memory.get_history()
        prompt = self.prompt_builder.build(chunks=chunks, question=question, history=history)

        logger.debug("HISTORY\n%s", history)
        logger.debug("PROMPT\n%s", prompt)

        # Step 3 — Generate answer
        logger.info("[RAGAssistant] Calling LLM...")
        answer = self.llm_client.generate(prompt)

        logger.debug("ANSWER\n%s", answer)

        # Step 4 — Update conversation memory for the next turn
        self.memory.add(question, answer)

        # Step 5 — Assemble source list for display
        sources = _extract_sources(chunks)

        return {
            "answer": answer,
            "chunks": chunks,
            "prompt": prompt,
            "sources": sources,
        }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_sources(chunks: list) -> list:
    """
    Builds a deduplicated, ordered list of source references from retrieved chunks.

    Each entry has the shape:
        {"file": str, "chunk_index": int | str}

    Order reflects retrieval rank (rank 1 source appears first).
    Deduplication is by (file, chunk_index) pair.

    Args:
        chunks : List of chunk dicts as returned by the retriever.

    Returns:
        List of source dicts, deduplicated and ordered by first appearance.
    """
    seen: set = set()
    sources: list = []

    for chunk in chunks:
        metadata = chunk.get("metadata") or {}
        file = metadata.get("source", "unknown")
        chunk_index = metadata.get("chunk_index", "?")
        key = (file, chunk_index)

        if key not in seen:
            seen.add(key)
            sources.append({"file": file, "chunk_index": chunk_index})

    return sources