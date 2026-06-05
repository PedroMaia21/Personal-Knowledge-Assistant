from app.search import semantic_search

query = "How do vector databases store data?"

results  = semantic_search(query, top_k=3)
print("RAW RESULTS:")
print(results)

for r in results:
    print("\n---")
    print(r["text"])
    print("Distance:", r["distance"])