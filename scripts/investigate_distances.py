"""
Investigation script: distance distribution analysis across diverse queries.

Run from project root:
    python scripts/investigate_distances.py

Results are printed to stdout AND written to data/evaluation/distance_findings.md
"""

import sys
import json
import statistics
from pathlib import Path

# Allow imports from src/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from retrieval.search import semantic_search

# ------------------------------------------------------------------
# 25 diverse queries covering different relevance levels:
# - Some should match well (topic present in your notes)
# - Some should be vague / off-topic (stress-tests lower bound)
# ------------------------------------------------------------------
QUERIES = [
    # Likely relevant (adjust to your actual document content)
    "machine learning",
    "productivity systems",
    "weekly review",
    "action items",
    "project planning",
    "goals and priorities",
    "time management",
    "decision making",
    "knowledge management",
    "note taking strategies",
    # Moderately relevant
    "software development",
    "personal growth",
    "learning strategies",
    "task prioritization",
    "focus and deep work",
    "automation",
    "AI tools",
    "retrospective review",
    "blocker identification",
    "habit building",
    # Likely off-topic (should yield high distances / low similarity)
    "quantum physics equations",
    "French cuisine recipes",
    "stock market prediction",
    "climate change policy",
    "ancient Roman history",
]

TOP_K = 3  # Use top-1 for best result, average over top-k


def run_investigation():
    all_best = []
    all_worst = []
    all_avg = []
    query_summaries = []

    print(f"\n{'='*60}")
    print("DISTANCE INVESTIGATION — PKA-AI")
    print(f"{'='*60}\n")

    for query in QUERIES:
        try:
            results = semantic_search(query, top_k=TOP_K)
        except Exception as e:
            print(f"[SKIP] '{query}' — error: {e}")
            continue

        if not results:
            print(f"[SKIP] '{query}' — no results returned")
            continue

        distances = [r["distance"] for r in results]
        best = min(distances)
        worst = max(distances)
        avg = statistics.mean(distances)

        all_best.append(best)
        all_worst.append(worst)
        all_avg.append(avg)

        query_summaries.append({
            "query": query,
            "best_distance": round(best, 4),
            "worst_distance": round(worst, 4),
            "avg_distance": round(avg, 4),
        })

        print(f"Query : {query!r}")
        print(f"  best={best:.4f}  worst={worst:.4f}  avg={avg:.4f}")
        print()

    if not all_best:
        print("No results collected — is the vector store populated?")
        return

    # ------------------------------------------------------------------
    # Aggregate stats
    # ------------------------------------------------------------------
    overall_best = min(all_best)
    overall_worst = max(all_worst)
    overall_avg = statistics.mean(all_avg)
    overall_median = statistics.median(all_avg)

    print(f"\n{'='*60}")
    print("AGGREGATE RESULTS")
    print(f"{'='*60}")
    print(f"  best result distance  : {overall_best:.4f}")
    print(f"  worst result distance : {overall_worst:.4f}")
    print(f"  average distance      : {overall_avg:.4f}")
    print(f"  median distance       : {overall_median:.4f}")
    print()

    # ------------------------------------------------------------------
    # Write findings note
    # ------------------------------------------------------------------
    findings_path = Path("data/evaluation/distance_findings.md")
    findings_path.parent.mkdir(parents=True, exist_ok=True)

    with findings_path.open("w", encoding="utf-8") as f:
        f.write("# Distance Investigation Findings\n\n")
        f.write("## Summary\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| Best (lowest) distance | `{overall_best:.4f}` |\n")
        f.write(f"| Worst (highest) distance | `{overall_worst:.4f}` |\n")
        f.write(f"| Average distance | `{overall_avg:.4f}` |\n")
        f.write(f"| Median distance | `{overall_median:.4f}` |\n\n")
        f.write("## Interpretation\n\n")
        f.write(
            "> Fill these in after reviewing the per-query table below.\n\n"
            "- **Excellent retrieval (0.90+ similarity):** distance ≈ `___`\n"
            "- **Good retrieval (0.80–0.90):** distance ≈ `___`\n"
            "- **Acceptable (0.70–0.80):** distance ≈ `___`\n"
            "- **Suspicious (<0.70):** distance > `___`\n\n"
        )
        f.write("## Per-Query Results\n\n")
        f.write("| Query | Best distance | Worst distance | Avg distance |\n")
        f.write("|-------|--------------|----------------|-------------|\n")
        for s in query_summaries:
            f.write(
                f"| {s['query']} | {s['best_distance']} "
                f"| {s['worst_distance']} | {s['avg_distance']} |\n"
            )
        f.write("\n## Raw JSON\n\n```json\n")
        f.write(json.dumps(query_summaries, indent=2))
        f.write("\n```\n")

    print(f"Findings written to: {findings_path}")


if __name__ == "__main__":
    run_investigation()