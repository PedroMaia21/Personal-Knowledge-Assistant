import json

def log_retrieval(query: str, chunks: list):    
    retrieval_log = {
        "query": query,
        "results": []
    }

    for rank, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source") if metadata else "Unknown"

        retrieval_log["results"].append({
            "rank": rank,
            "distance": chunk.get("distance"),
            "similarity": chunk.get("similarity_score"),
            "source": source,
            "chunk_text": chunk.get("text"),
            "chunk_id": chunk.get("id")
        })

    print(
        json.dumps(
            retrieval_log,
            indent=2
        )
    )

    return