# src/assistant/memory.py
"""
memory.py — Conversation memory for PKA-AI.

Keeps a short, in-process buffer of recent question/answer pairs so
follow-up questions ("What about it?", "Summarize that") can be
resolved by the LLM using conversational context.

Explicitly NOT:
    - persisted to disk
    - embedded or vectorised
    - summarized
    - mixed with retrieved document chunks

Conversation history and document retrieval are separate concerns —
this module knows nothing about chunks, ChromaDB, or embeddings.
"""

from typing import Dict, List

MAX_HISTORY = 5  # number of Q/A exchanges retained


class ConversationMemory:
    """
    Simple in-memory buffer of the last `max_history` question/answer pairs.

    Not thread-safe. Not persisted. Scoped to a single running session
    (a new process / CLI run starts with empty history).
    """

    def __init__(self, max_history: int = MAX_HISTORY):
        self.max_history = max_history
        self.history: List[Dict[str, str]] = []

    def add(self, question: str, answer: str) -> None:
        """
        Appends a new exchange, evicting the oldest exchange once the
        buffer exceeds `max_history`.
        """
        self.history.append({
            "question": question,
            "answer": answer,
        })

        if len(self.history) > self.max_history:
            self.history.pop(0)

    def get_history(self) -> List[Dict[str, str]]:
        """Returns exchanges oldest-first, ready for prompt formatting."""
        return self.history

    def clear(self) -> None:
        """Empties the history (e.g. a `/reset` command in the CLI)."""
        self.history = []

    def __len__(self) -> int:
        return len(self.history)