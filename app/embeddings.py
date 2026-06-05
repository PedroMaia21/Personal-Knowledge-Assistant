from ollama import embeddings
from chromadb import PersistentClient

MODEL = "nomic-embed-text"

def generate_embedding(text):
    response = embeddings(
        model = MODEL, 
        prompt = text    
    )
    
    return response["embedding"]

def generate_embeddings(chunks):
    results = []

    total = len(chunks)

    for i, chunk in enumerate(chunks):
        print(f"Generating embedding for chunk {i + 1} of {total}...")

        vector = generate_embedding(chunk)
        
        results.append(
            {
                "text": chunk,
                "embedding": vector
            }    
        )
    
    return results

def get_embedding(text: str):
    import ollama
    response = ollama.embeddings(
        model="nomic-embed-text",
        prompt=text
    )
    return response["embedding"]

client = PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="documents")

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

    return chunks