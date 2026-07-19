# src/core/chroma_client.py
"""
chroma_client.py — Shared ChromaDB client for PKA-AI.

Every PersistentClient construction and every get_or_create_collection()
call goes through this class. No other module should know the DB path,
the collection name, or the hnsw:space metadata setting — those are
configuration owned here, in exactly one place.
"""

import logging

import chromadb
from chromadb.api.models.Collection import Collection

from src.config.config import CHROMA_DB_PATH, CHROMA_COLLECTION_NAME

logger = logging.getLogger(__name__)


class ChromaClient:
    """
    Thin wrapper around a persistent ChromaDB collection.

    Args:
        db_path:         Path to the on-disk ChromaDB store. Defaults to
                          CHROMA_DB_PATH from config.
        collection_name:  Name of the collection to use/create. Defaults
                          to CHROMA_COLLECTION_NAME from config.
    """

    def __init__(
        self,
        db_path: str = CHROMA_DB_PATH,
        collection_name: str = CHROMA_COLLECTION_NAME,
    ):
        self.db_path = db_path
        self.collection_name = collection_name
        self._client = chromadb.PersistentClient(path=self.db_path)
        self._collection = self._get_or_create()

    def _get_or_create(self) -> Collection:
        return self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def get_collection(self) -> Collection:
        """Returns the shared collection instance."""
        return self._collection

    def reset_collection(self) -> Collection:
        """
        Deletes and recreates the collection (e.g. before a full
        re-ingestion, or between test runs). Returns the new, empty
        collection and updates the instance's internal reference.
        """
        self._client.delete_collection(self.collection_name)
        self._collection = self._get_or_create()
        logger.info(f"Collection '{self.collection_name}' reset.")
        return self._collection

    def health_check(self) -> bool:
        """
        Confirms the collection is reachable via a trivial count() call.

        Returns:
            True if the call succeeds, False otherwise (failure logged,
            not raised — same convention as EmbeddingClient.health_check()).
        """
        try:
            self._collection.count()
            return True
        except Exception as e:
            logger.error(f"ChromaClient health check failed ({self.db_path}): {e}")
            return False