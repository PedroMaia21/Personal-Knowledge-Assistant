import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.ingestion.loader import load_folder
from src.ingestion.chunking import ChunkerV1
from src.models.embedding import generate_embedding
from src.vectorstore.chroma_store import store_chunks, count_documents

chunker = ChunkerV1()

def run_ingestion():
    print("🔄 Crawling for raw documents...")
    docs = load_folder("./data/raw")

    for doc in docs:
        path = doc["path"]
        print(f"  Processing: {path}")

        # chunk_document() returns [{"text": str, "metadata": dict}, ...]
        chunks = chunker.chunk_document(doc["content"], source=path)

        # Embed the text of each chunk
        vectors = [generate_embedding(chunk["text"]) for chunk in chunks]

        # store_chunks() expects the full chunk dicts + parallel embeddings list
        store_chunks(chunks=chunks, embeddings=vectors)

        print(f"    → {len(chunks)} chunks stored")

    print(f"\n✅ Ingestion complete. Total vectors in store: {count_documents()}")

if __name__ == "__main__":
    run_ingestion()