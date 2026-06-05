import chromadb

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(name="knowledge_base")

def store_chunks(chunks, embeddings, source):
    ids = []
    metadatas = []

    clean_embeddings = [
        item["embedding"] 
        for item in embeddings
    ]

    for i, chunk in enumerate(chunks):
        ids.append(f"{source}_{i}")

        metadatas.append(
            {
                "source": source,
                "chunk_index": i,
            }
        )

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=clean_embeddings,
        metadatas=metadatas
    )

def count_documents():
    return collection.count()