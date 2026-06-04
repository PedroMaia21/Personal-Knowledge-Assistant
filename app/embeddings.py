from ollama import embeddings

MODEL = "nomic-embed-text"

def generate_embeddings(text: str):
    response = embeddings(
        model = MODEL, 
        prompt = text    
    )
    
    return response["embedding"]