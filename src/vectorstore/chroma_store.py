import chromadb
from typing import Any, Dict, List
from src.config.config import CHROMA_DB_PATH, CHROMA_COLLECTION_NAME

client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

collection = client.get_or_create_collection(
    name=CHROMA_COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)


def store_chunks(
    chunks: List[Dict[str, Any]],
    embeddings: List[List[float]],
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
                "chunker_version":  str,   ← set by the chunker
            }
        }

    The caller is responsible for ensuring len(chunks) == len(embeddings).
    """
    if not chunks:
        return

    ids: List[str] = []
    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []

    for i, chunk in enumerate(chunks):
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


def count_documents() -> int:
    return collection.count()