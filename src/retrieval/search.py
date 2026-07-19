# src/retrieval/search.py
from src.core.chroma_client import ChromaClient
from src.core.embedding_client import EmbeddingClient
from src.utils.helpers import normalize_similarity
from src.utils.reranker import rerank
from src.config.config import DEFAULT_TOP_K

# Fallbacks used only when a caller doesn't inject its own clients.
_default_embedding_client = EmbeddingClient()
_default_chroma_client = ChromaClient()


def semantic_search(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    embedding_client: EmbeddingClient | None = None,
    chroma_client: ChromaClient | None = None,
):
    """
    Pure vector search. Returns chunks sorted by cosine distance only.
    Use semantic_search_reranked() for the heuristic-boosted version.

    Args:
        embedding_client: Injected EmbeddingClient (falls back to shared default).
        chroma_client:    Injected ChromaClient (falls back to shared default).
                          No module should construct PersistentClient(...)
                          or call get_or_create_collection() directly anymore.
    """
    embed_client = embedding_client or _default_embedding_client
    chroma = chroma_client or _default_chroma_client
    collection = chroma.get_collection()

    # 1. Embed the query
    query_embedding = embed_client.generate(query)

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
    chroma_client: ChromaClient | None = None,
):
    """
    Vector search followed by heuristic reranking. See rerank() for the
    distance_score + size_bonus + continuity_bonus breakdown.
    """
    chunks = semantic_search(
        query,
        top_k=top_k,
        embedding_client=embedding_client,
        chroma_client=chroma_client,
    )
    return rerank(chunks)