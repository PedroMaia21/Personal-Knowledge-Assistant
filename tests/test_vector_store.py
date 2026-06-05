from app.chunking import chunk_text
from app.embeddings import generate_embeddings
from app.vector_store import store_chunks

text = """
Artificial Intelligence is transforming many industries.

Machine Learning enables systems to learn patterns.

Vector databases store embeddings efficiently.
"""

chunks = chunk_text(text)

embeddings = generate_embeddings(chunks)

store_chunks(chunks, embeddings, "test_document")

print("Chunks, embeddings, and metadata stored successfully in the vector database.")