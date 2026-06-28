import json
import logging
from pathlib import Path
from src.retrieval.search import semantic_search_reranked

logging.basicConfig(level=logging.INFO)

def run_evaluation():
    eval_file = Path("data/evaluation/eval_queries.json")
    if not eval_file.exists():
        print(f"❌ Evaluation file not found at {eval_file}. Skipping baseline metrics.")
        return

    with open(eval_file, "r", encoding="utf-8") as f:
        eval_queries = json.load(f)
        
    correct = 0
    total = len(eval_queries)

    print(f"\n🔍 Evaluating retrieval accuracy across {total} cases...")
    for test_case in eval_queries:
        query = test_case["query"]
        expected = test_case["expected_chunk_id"]

        chunks = semantic_search_reranked(query, top_k=3)
        
        if chunks:
            # Check if expected chunk is within top result position
            if chunks[0].get("id") == expected:
                correct += 1

    accuracy = (correct / total * 100) if total > 0 else 0
    print(f"📊 Accuracy Metric: {accuracy:.2f}% ({correct}/{total} hits)\n")

if __name__ == "__main__":
    run_evaluation()