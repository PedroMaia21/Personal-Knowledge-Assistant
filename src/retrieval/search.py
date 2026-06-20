from chromadb import PersistentClient

from src.utils.helpers import normalize_similarity
from src.config.config import DEFAULT_TOP_K, CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL

client = PersistentClient(path=CHROMA_DB_PATH)

collection = client.get_or_create_collection(
    name=CHROMA_COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)


def get_embedding(text: str):
    import ollama
    response = ollama.embeddings(
        model=EMBEDDING_MODEL,
        prompt=text,
    )
    return response["embedding"]


def semantic_search(query: str, top_k: int = DEFAULT_TOP_K):
    # 1. Embed the query
    query_embedding = get_embedding(query)

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