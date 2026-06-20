import pytest
from ingestion.chunking import chunk_text
from models.embedding import generate_embeddings
from vectorstore.chroma_store import store_chunks, count_documents

def test_database_ingestion_flow():
    initial_count = count_documents()
    text = "Artificial Intelligence is transforming industries. Vector databases store embeddings efficiently."
    
    chunks = chunk_text(text, chunk_size=50, overlap=5)
    embeddings = generate_embeddings(chunks)
    
    # Run storage operation
    store_chunks(chunks, embeddings, source="unit_test_doc")
    
    # Validate count increased correctly
    assert count_documents() == initial_count + len(chunks)