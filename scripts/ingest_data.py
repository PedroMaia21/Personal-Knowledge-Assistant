"""
scripts/ingest_data.py — Bulk ingestion / live vector-store rebuild for PKA-AI.

Usage (from the repository root):
    python -m scripts.ingest_data            # refuses if the collection is non-empty
    python -m scripts.ingest_data --reset    # DESTRUCTIVE: empties the collection first

Loads every supported file under data/raw/, chunks it with ChunkerV1,
embeds each chunk through EmbeddingClient and stores it through ChromaClient
in the configured collection (CHROMA_COLLECTION_NAME at CHROMA_DB_PATH).
"""

import argparse
import sys

from src.core.chroma_client import ChromaClient
from src.core.embedding_client import EmbeddingClient
from src.ingestion.chunking import ChunkerV1
from src.ingestion.loader import load_folder
from src.vectorstore.chroma_store import count_documents, store_chunks

RAW_DATA_PATH = "./data/raw"


def run_ingestion(reset: bool = False) -> int:
    chroma_client = ChromaClient()
    embedding_client = EmbeddingClient()
    chunker = ChunkerV1()
    collection_name = chroma_client.collection_name

    existing = count_documents(chroma_client=chroma_client)
    if existing and not reset:
        print(
            f"❌ Collection '{collection_name}' at {chroma_client.db_path} already "
            f"holds {existing} vectors. Refusing to ingest, to avoid duplicating "
            f"or partially overwriting them.\n"
            f"   Re-run with --reset to delete ONLY this collection and rebuild "
            f"it from {RAW_DATA_PATH}."
        )
        return 1

    if reset:
        print(f"⚠️  --reset: deleting collection '{collection_name}' ({existing} vectors)")
        chroma_client.reset_collection()

    print("🔄 Crawling for raw documents...")
    docs = load_folder(RAW_DATA_PATH)

    total_chunks = 0
    for doc in docs:
        path = doc["path"]
        print(f"  Processing: {path}")

        # chunk_document() returns [{"text": str, "metadata": dict}, ...]
        chunks = chunker.chunk_document(doc["content"], source=path)

        # One generate() call per chunk keeps chunks and vectors aligned:
        # a failure raises instead of being skipped (as generate_many() does).
        vectors = [embedding_client.generate(chunk["text"]) for chunk in chunks]

        store_chunks(chunks=chunks, embeddings=vectors, chroma_client=chroma_client)
        total_chunks += len(chunks)

        print(f"    → {len(chunks)} chunks stored")

    print(
        f"\n✅ Ingestion complete. {len(docs)} documents, {total_chunks} chunks. "
        f"Total vectors in store: {count_documents(chroma_client=chroma_client)}"
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and recreate the knowledge-base collection before ingesting "
             "(destructive; other collections are untouched).",
    )
    args = parser.parse_args()
    sys.exit(run_ingestion(reset=args.reset))


if __name__ == "__main__":
    main()
