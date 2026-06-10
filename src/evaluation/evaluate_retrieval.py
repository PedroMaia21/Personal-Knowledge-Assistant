import json
from app.search import semantic_search

with open("data/eval_queries.json", "r", encoding="utf-8") as f:
    eval_queries = json.load(f)
    
record_result = {}
record_result["correct"] = 0
record_result["total"] = 0

for test_case in eval_queries:
    query = test_case["query"]
    expected = test_case["expected_chunk_id"]

    chunks = semantic_search(query)

    top_chunk = chunks[0]

    success = (top_chunk.get("id") == expected)

    record_result["total"] += 1

    if success:
        record_result["correct"] += 1 

if record_result["total"] != 0:
    accuracy = record_result["correct"]/record_result["total"]
else:
    accuracy = 0

print(f"Accuracy: {accuracy * 100}%")