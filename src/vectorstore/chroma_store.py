# src/vectorstore/chroma_store.py
from typing import Any, Dict, List

from src.core.chroma_client import ChromaClient

# Fallback used only when a caller doesn't inject its own ChromaClient —
# keeps store_chunks()/count_documents() callable standalone (REPL, tests)
# without forcing every caller to construct and pass one.
_default_chroma_client = ChromaClient()


def store_chunks(
    chunks: List[Dict[str, Any]],
    embeddings: List[List[float]],
    chroma_client: ChromaClient | None = None,
) -> None:
    """
    Persists vectorised chunk dicts (as produced by ChunkerV1) to ChromaDB.

    Each element of *chunks* must have the shape:
        {
            "text":     str,
            "metadata": {
                "source":           str,
                "chunk_index":      int,
                "chunk_length":     int,
                "chunker_version":  str,
            }
        }

    Args:
        chroma_client: Injected ChromaClient. Falls back to a shared
                       module-level default if not provided — no module
                       should construct PersistentClient(...) directly.

    The caller is responsible for ensuring len(chunks) == len(embeddings).
    """
    if not chunks:
        return

    client_to_use = chroma_client or _default_chroma_client
    collection = client_to_use.get_collection()

    ids: List[str] = []
    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []

    for chunk in chunks:
        metadata = chunk["metadata"]
        source = metadata["source"]
        safe_source = source.replace("/", "_").replace("\\", "_")

        ids.append(f"{safe_source}_ch{metadata['chunk_index']}")
        documents.append(chunk["text"])
        metadatas.append(metadata)

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def count_documents(chroma_client: ChromaClient | None = None) -> int:
    client_to_use = chroma_client or _default_chroma_client
    return client_to_use.get_collection().count()