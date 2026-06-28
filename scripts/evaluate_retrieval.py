"""
scripts/evaluate_retrieval.py — Retrieval benchmark for PKA-AI.

Usage:
    python scripts/evaluate_retrieval.py

Reads data/evaluation/eval_queries.json, runs each query through
semantic_search_reranked(), and prints a full accuracy report.

Matching strategy
-----------------
Queries are matched against `expected_source` (a filename substring)
rather than an exact chunk ID.  Chunk IDs change whenever documents are
re-ingested; source filenames are stable.  A hit is recorded when the
expected filename appears anywhere in the source path of a returned chunk.

Two accuracy metrics are reported:
    Accuracy @1   — correct source ranked #1
    Hit Rate @k   — correct source anywhere in top-k results
"""

import json
import logging
from datetime import date
from pathlib import Path

from src.retrieval.search import semantic_search_reranked
from src.config.config import DEFAULT_TOP_K

logging.basicConfig(level=logging.WARNING)   # suppress Ollama/ChromaDB noise during eval

QUERIES_PATH = Path("data/evaluation/eval_queries.json")
RESULTS_PATH = Path("data/evaluation/eval_results.json")
TOP_K        = DEFAULT_TOP_K


# ── Helpers ───────────────────────────────────────────────────────────────────

def source_of(chunk: dict) -> str:
    return chunk.get("metadata", {}).get("source", "")


def correct_at_1(chunks: list[dict], expected: str) -> bool:
    """True if the top-ranked chunk comes from the expected source."""
    return bool(chunks) and expected in source_of(chunks[0])


def hit_in_topk(chunks: list[dict], expected: str) -> bool:
    """True if the expected source appears anywhere in top-k results."""
    return any(expected in source_of(c) for c in chunks)


# ── Runner ────────────────────────────────────────────────────────────────────

def run_evaluation() -> None:
    if not QUERIES_PATH.exists():
        print(f"❌ Query file not found: {QUERIES_PATH}")
        return

    with open(QUERIES_PATH, encoding="utf-8") as f:
        queries = json.load(f)

    total   = len(queries)
    results = []

    print(f"\n🔍 Evaluating {total} queries (top_k={TOP_K}) …\n")

    for item in queries:
        qid      = item["id"]
        query    = item["query"]
        expected = item["expected_source"]

        chunks = semantic_search_reranked(query, top_k=TOP_K)

        at1   = correct_at_1(chunks, expected)
        in_k  = hit_in_topk(chunks, expected)
        top1  = source_of(chunks[0]) if chunks else "—"
        dist  = chunks[0].get("distance") if chunks else None

        status = "✅" if at1 else ("⚠️ " if in_k else "❌")
        print(f"  {status} [{qid}] {query}")
        if not at1:
            print(f"        expected: {expected}")
            print(f"        got:      {top1}")

        results.append({
            "id":              qid,
            "query":           query,
            "expected_source": expected,
            "actual_top1":     top1,
            "correct_at_1":    at1,
            "hit_in_topk":     in_k,
            "top1_distance":   round(dist, 4) if dist is not None else None,
            "notes":           item.get("notes", ""),
        })

    _print_report(results, total)
    _save_results(results)


# ── Report ────────────────────────────────────────────────────────────────────

def _print_report(results: list[dict], total: int) -> None:
    at1_count  = sum(1 for r in results if r["correct_at_1"])
    hitk_count = sum(1 for r in results if r["hit_in_topk"])
    misses     = [r for r in results if not r["hit_in_topk"]]
    wrong_rank = [r for r in results if r["hit_in_topk"] and not r["correct_at_1"]]

    print()
    print("═" * 56)
    print(f"  PKA-AI Retrieval Evaluation  —  {date.today()}")
    print("═" * 56)
    print(f"  Queries        : {total}")
    print(f"  Top-k          : {TOP_K}")
    print()
    print(f"  Accuracy @1    : {at1_count}/{total}  ({at1_count/total*100:.0f}%)")
    print(f"  Hit Rate @{TOP_K}   : {hitk_count}/{total}  ({hitk_count/total*100:.0f}%)")
    print(f"  Wrong rank     : {len(wrong_rank)}")
    print(f"  Complete miss  : {len(misses)}")

    if misses or wrong_rank:
        print()
        print("  ── Failure Analysis ─────────────────────────────────")
        for r in misses:
            print(f"\n  ❌ [{r['id']}] {r['query']}")
            print(f"       expected : {r['expected_source']}")
            print(f"       got      : {r['actual_top1']}")
            if r["notes"]:
                print(f"       notes    : {r['notes']}")
        for r in wrong_rank:
            print(f"\n  ⚠️  [{r['id']}] {r['query']}")
            print(f"       expected @1 : {r['expected_source']}")
            print(f"       got @1      : {r['actual_top1']}")
            print(f"       (correct source found in top-{TOP_K}, not at rank #1)")

    print()
    print("═" * 56)


def _save_results(results: list[dict]) -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {"date": str(date.today()), "top_k": TOP_K, "results": results},
            f, indent=2,
        )
    print(f"\n  Results saved → {RESULTS_PATH}\n")


if __name__ == "__main__":
    run_evaluation()