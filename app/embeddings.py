from ollama import embeddings

MODEL = "nomic-embed-text"

def generate_embedding(text):
    response = embeddings(
        model = MODEL, 
        prompt = text    
    )
    
    return response["embedding"]

def generate_embeddings(chunks):
    results = []

    for chunk in chunks:
        vector = generate_embedding(chunk)
        
        results.append(
            {
                "text": chunk,
                "embedding": vector
            }    
        )
    
    return results