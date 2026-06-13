import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

from ingestion.loader import load_folder
from ingestion.chunking import chunk_text
from models.embedding import generate_embedding
from vectorstore.chroma_store import store_chunks, count_documents

def run_ingestion():
    print("🔄 Crawling for raw documents...")
    docs = load_folder("./data")
    
    for doc in docs:
        print(f"Processing structural elements for: {doc['path']}")
        chunks = chunk_text(doc['content'])
        
        # Build embeddings matching raw chunks array indexes cleanly 
        vectors = [generate_embedding(c) for c in chunks]
        
        # Commit safely into ChromaDb instances
        store_chunks(chunks=chunks, embeddings=vectors, source=doc['path'])
        
    print(f"✅ Operations complete. Vector store document count: {count_documents()}")

if __name__ == "__main__":
    run_ingestion()