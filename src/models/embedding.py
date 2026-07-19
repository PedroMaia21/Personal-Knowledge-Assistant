# src/models/embedding.py
"""
embedding.py — DEPRECATED.

This module used to own its own Ollama call (`generate_embedding`) and
its own batching loop (`generate_embeddings`), duplicating what
search.py's get_embedding() also did independently. That duplication is
exactly what the shared EmbeddingClient was introduced to eliminate.

Migration:
    OLD:
        from src.models.embedding import generate_embedding, generate_embeddings
        vector = generate_embedding(text)
        results = generate_embeddings(chunks)

    NEW:
        from src.core.embedding_client import EmbeddingClient
        client = EmbeddingClient()
        vector = client.generate(text)
        results = client.generate_many(chunks)

Construct one EmbeddingClient per process (e.g. in app.py) and inject it
into whatever needs embeddings — ingestion and SearchRetriever alike —
rather than importing a module-level function here.
"""

raise ImportError(
    "src.models.embedding.generate_embedding/generate_embeddings have been "
    "removed. Use src.core.embedding_client.EmbeddingClient instead — "
    "see the module docstring for the migration snippet."
)