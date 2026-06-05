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

def get_embeddings(text: str):
    import ollama
    response = ollama.embeddings(
        model="nomic-embed-text",
        prompt=text
    )
    return response["embedding"]