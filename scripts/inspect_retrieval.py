from src.retrieval.search import semantic_search_reranked
from src.utils.logging import log_retrieval

query = input("Query: ")

k = int(input("Top k: "))

results = semantic_search_reranked(query, k)

log_retrieval(query, results)