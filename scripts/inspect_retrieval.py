from app.search import semantic_search
from app.retrieval.logging import log_retrieval

query = input("Query: ")

k = int(input("Top k: "))

results = semantic_search(query, k)

log_retrieval(query, results)