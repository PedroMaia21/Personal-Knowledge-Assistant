# src/core/embedding_client.py
"""
embedding_client.py — Shared embedding client for PKA-AI.

Every Ollama embedding request — single text or batch, during ingestion
or during query-time search — goes through this class. No other module
should call `ollama.embeddings(...)` directly.

Owns the model name so it's configured in exactly one place instead of
being repeated as a string literal in embedding.py, search.py, etc.
"""

import logging
from typing import Any, Dict, List, Optional

import ollama

from src.config.config import EMBEDDING_MODEL

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """
    Thin wrapper around the Ollama embeddings endpoint.

    Args:
        model_name: Embedding model to use. Defaults to EMBEDDING_MODEL
                    from config. Override here (not by editing this class)
                    for tests or alternate models — e.g.
                    EmbeddingClient(model_name="mxbai-embed-large").
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name

    def generate(self, text: str) -> List[float]:
        """Generates a single embedding vector for one piece of text."""
        response = ollama.embeddings(
            model=self.model_name,
            prompt=text,
        )
        return response["embedding"]

    def generate_many(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Batches multiple texts through generate().

        A single failed embedding is logged and skipped rather than
        aborting the whole batch — same behaviour as the old
        generate_embeddings() in models/embedding.py.

        Returns:
            List of {"text": str, "embedding": list[float]} dicts.
        """
        results: List[Dict[str, Any]] = []
        for i, text in enumerate(texts):
            try:
                vector = self.generate(text)
                results.append({"text": text, "embedding": vector})
            except Exception as e:
                logger.error(f"Error generating vector on chunk {i}: {e}")
        return results

    def health_check(self) -> bool:
        """
        Confirms the configured embedding model is reachable and responding.

        Returns:
            True if a trivial embedding call succeeds, False otherwise
            (failure is logged, not raised, so callers can use this for
            a startup check without a try/except).
        """
        try:
            self.generate("health check")
            return True
        except Exception as e:
            logger.error(f"EmbeddingClient health check failed ({self.model_name}): {e}")
            return False