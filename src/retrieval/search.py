# src/retrieval/search.py
from chromadb import PersistentClient

from src.core.embedding_client import EmbeddingClient
from src.utils.helpers import normalize_similarity
from src.utils.reranker import rerank
from src.config.config import DEFAULT_TOP_K, CHROMA_DB_PATH, CHROMA_COLLECTION_NAME

client = PersistentClient(path=CHROMA_DB_PATH)

collection = client.get_or_create_collection(
    name=CHROMA_COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)

# Fallback used only when a caller doesn't inject its own EmbeddingClient.
# Keeps semantic_search() callable standalone (e.g. from a REPL or a test)
# without forcing every caller to construct and pass a client.
_default_embedding_client = EmbeddingClient()


def semantic_search(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    embedding_client: EmbeddingClient | None = None,
):
    """
    Pure vector search. Returns chunks sorted by cosine distance only.
    Use semantic_search_reranked() for the heuristic-boosted version.

    Args:
        embedding_client: Injected EmbeddingClient. Falls back to a shared
                          module-level default if not provided — no module
                          should call `ollama.embeddings()` directly anymore.
    """
    client_to_use = embedding_client or _default_embedding_client

    # 1. Embed the query
    query_embedding = client_to_use.generate(query)

    # 2. Search ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    # 3. Format results
    chunks = []
    for i in range(len(results["documents"][0])):
        distance = results["distances"][0][i]
        chunks.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": distance,
            "similarity_score": normalize_similarity(distance),
        })

    return chunks


def semantic_search_reranked(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    embedding_client: EmbeddingClient | None = None,
):
    """
    Vector search followed by heuristic reranking.

    Retrieves top_k chunks by cosine distance, then re-sorts them using
    three lightweight signals (distance score, size penalty, continuity bonus).

    Each returned chunk contains a "rerank_scores" key with the full breakdown:
        {
            "distance_score":   float,
            "size_bonus":       float,
            "continuity_bonus": float,
            "final_score":      float,
        }

    Use reranker.format_rerank_debug(chunk) to print the breakdown for a chunk.
    """
    chunks = semantic_search(query, top_k=top_k, embedding_client=embedding_client)
    return rerank(chunks)