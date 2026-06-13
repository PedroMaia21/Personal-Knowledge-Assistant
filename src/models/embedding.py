import logging
from typing import List, Dict, Any
import ollama

logger = logging.getLogger(__name__)

MODEL = "nomic-embed-text"

def generate_embedding(text: str) -> List[float]:
    """Generates a standalone vector representation for a single text chunk."""
    response = ollama.embeddings(
        model = MODEL, 
        prompt = text    
    )
    
    return response["embedding"]

def generate_embeddings(chunks: List[str]) -> List[Dict[str, Any]]:
    """Batches incoming text strings through the Ollama embedding client."""
    results = []

    for i, chunk in enumerate(chunks):
        try:
            vector = generate_embedding(chunk)
            
            results.append({
                "text": chunk,
                "embedding": vector
            })
        except Exception as e:
            logger.error(f"Error generation vector on chunk {i}: {e}")
    
    return results