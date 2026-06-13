import chromadb
from typing import List

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="knowledge_base",
    metadata={"hnsw:space": "cosine"},
)


def store_chunks(chunks: List[str], embeddings: List[List[float]], source: str):
    """Saves vectorized text strings with custom context tracking metadata."""
    if not chunks:
        return

    ids = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        safe_source = source.replace("/", "_").replace("\\", "_")
        ids.append(f"{safe_source}_ch{i}")

        metadatas.append({
            "source": source,
            "chunk_index": i,
            "chunk_length": len(chunk),
        })

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def count_documents() -> int:
    return collection.count()