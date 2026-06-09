from chromadb import PersistentClient
import json

def get_embedding(text: str):
    import ollama
    response = ollama.embeddings(
        model="nomic-embed-text",
        prompt=text
    )
    return response["embedding"]

client = PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="knowledge_base")

def semantic_search(query: str, top_k: int = 5):
    # 1. Embed the query
    query_embedding = get_embedding(query)

    # 2. Search ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    # 3 Format results
    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })

    print(results.keys())
    log_retrieval(query, results)

    return chunks

def log_retrieval(query: str, results: dict):
    ids = results.get("ids", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    
    retrieval_log = {
        "query": query,
        "results": []
    }

    for rank, (chunk_id, metadata, distance) in enumerate(zip(ids, metadatas, distances), start=1):
        retrieval_log["results"].append({
            "rank": rank,
            "chunk_id": chunk_id,
            "distance": distance,
            "source": metadata.get("source") if metadata else "Unknown"
        })

    print(
        json.dumps(
            retrieval_log,
            indent=2
        )
    )

    return