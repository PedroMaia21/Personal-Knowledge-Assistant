from app.embeddings import generate_embeddings


chunks = [
    "Portugal is in Europe.",
    "Berlin is in Germany."
]

results = generate_embeddings(chunks)

print(len(results))  # Should print 2

for item in results:
    print(f"Embedding length: {len(item['embedding'])}")