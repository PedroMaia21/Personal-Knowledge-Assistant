import pytest
from models.embedding import generate_embeddings, generate_embedding

def test_generate_single_embedding():
    vector = generate_embedding("Test payload text.")
    assert isinstance(vector, list)
    assert len(vector) > 0
    assert isinstance(vector[0], float)

def test_generate_multiple_embeddings():
    chunks = ["Portugal is in Europe.", "Berlin is in Germany."]
    results = generate_embeddings(chunks)
    
    assert len(results) == 2
    assert results[0]["text"] == chunks[0]
    assert "embedding" in results[0]