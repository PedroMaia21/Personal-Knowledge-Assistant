"""
scripts/rescore_distance_only.py — Distance-only Accuracy@1 from existing eval results.

Usage:
    python3 -m scripts.rescore_distance_only \
        --out data/evaluation/distance_only_acc1.json

Re-scores the stored per-chunker results (eval_results_v1_isolated.json and
eval_results_v2_isolated.json) WITHOUT re-running retrieval.

Why this is possible
--------------------
semantic_search_reranked() = rerank(semantic_search(query, top_k=5)).
rerank() only re-sorts the 5 chunks ChromaDB returned; it never adds or
drops candidates. Each stored "retrieved" entry keeps its raw cosine
"distance", so sorting those 5 entries by ascending distance reproduces
the pure-vector ranking of semantic_search().

Metric definition (unchanged from scripts/evaluate_retrieval.py)
----------------------------------------------------------------
correct_at_1: the expected_source string is a substring of the rank-1
chunk's source path. Only the ordering differs here: rank 1 is the
smallest-distance chunk instead of the highest reranker final_score.

Safety
------
Pure stdlib: reads JSON, writes one new JSON file. Never imports src.*,
so ChromaDB (./chroma_db) is never opened. Refuses to overwrite any input.
"""

import argparse
import itertools
import json
import sys
from pathlib import Path

EVAL_DIR      = Path("data/evaluation")
QUERIES_PATH  = EVAL_DIR / "eval_queries.json"
INPUTS        = {
    "v1": EVAL_DIR / "eval_results_v1_isolated.json",
    "v2": EVAL_DIR / "eval_results_v2_isolated.json",
}
PROTECTED     = [QUERIES_PATH, EVAL_DIR / "eval_results.json", *INPUTS.values()]

# Reranker constants (src/utils/reranker.py) — used only to validate that the
# stored "distance" is the raw value the reranker scored, never to rank.
SIZE_PENALTY     = -0.10
CONTINUITY_BONUS = 0.15
ROUND_TOL        = 2e-4   # distance and final_score are stored rounded to 4 dp


def matches(source: str, expected: str) -> bool:
    """Same rule as evaluate_retrieval.correct_at_1 / hit_in_topk."""
    return expected in source


def first_rank(entries: list[dict], expected: str) -> int | None:
    for pos, e in enumerate(entries, start=1):
        if matches(e["source"], expected):
            return pos
    return None


def distance_order(retrieved: list[dict]) -> list[dict]:
    # Stable sort: equal (rounded) distances keep reranked order; ties are
    # reported separately so no outcome silently depends on tie-breaking.
    return sorted(retrieved, key=lambda e: e["distance"])


# ── Validation ────────────────────────────────────────────────────────────────

def _allowed_bonuses(top_k: int) -> list[float]:
    return [s + CONTINUITY_BONUS * n
            for s, n in itertools.product((0.0, SIZE_PENALTY), range(top_k))]


def validate(version: str, payload: dict, queries: list[dict]) -> list[str]:
    errors: list[str] = []
    res = payload["results"]
    k = payload["top_k"]
    bonuses = _allowed_bonuses(k)

    if [(q["id"], q["query"], q["expected_source"]) for q in queries] != \
       [(r["id"], r["query"], r["expected_source"]) for r in res]:
        errors.append(f"{version}: query set differs from {QUERIES_PATH}")

    for r in res:
        ret = r["retrieved"]
        tag = f"{version}/{r['id']}"
        if len(ret) != k:
            errors.append(f"{tag}: {len(ret)} retrieved, expected {k}")
        if [e["rank"] for e in ret] != list(range(1, len(ret) + 1)):
            errors.append(f"{tag}: ranks not 1..{len(ret)}")
        if ret and ret[0]["source"] != r["actual_top1"]:
            errors.append(f"{tag}: retrieved[0] != actual_top1")
        if ret and ret[0]["distance"] != r["top1_distance"]:
            errors.append(f"{tag}: retrieved[0].distance != top1_distance")
        if (bool(ret) and matches(ret[0]["source"], r["expected_source"])) != r["correct_at_1"]:
            errors.append(f"{tag}: stored correct_at_1 not reproducible")
        if any(matches(e["source"], r["expected_source"]) for e in ret) != r["hit_in_topk"]:
            errors.append(f"{tag}: stored hit_in_topk not reproducible")
        scores = [e["final_score"] for e in ret]
        if any(a < b for a, b in zip(scores, scores[1:])):
            errors.append(f"{tag}: final_score not non-increasing (not reranked order?)")
        for e in ret:
            resid = e["final_score"] - 1.0 / (1.0 + e["distance"])
            if min(abs(resid - b) for b in bonuses) > ROUND_TOL:
                errors.append(f"{tag} rank {e['rank']}: final_score - 1/(1+d) = "
                              f"{resid:.4f} is not a valid reranker bonus")

    n = len(res)
    for field, value in (
        ("num_queries", n),
        ("correct_at_1_count", sum(r["correct_at_1"] for r in res)),
        ("hit_in_topk_count", sum(r["hit_in_topk"] for r in res)),
    ):
        if payload[field] != value:
            errors.append(f"{version}: summary {field}={payload[field]} != recomputed {value}")
    return errors


# ── Scoring ───────────────────────────────────────────────────────────────────

def classify(dist_ok: bool, rr_ok: bool, hit: bool) -> str:
    if dist_ok and rr_ok:
        return "both_correct"
    if dist_ok:
        return "rerank_hurt"          # distance-only correct, reranked wrong
    if rr_ok:
        return "rerank_helped"        # reranked correct, distance-only wrong
    return "both_fail_in_top5" if hit else "both_fail_miss"


def score(payload: dict) -> dict:
    per_query = []
    for r in payload["results"]:
        exp = r["expected_source"]
        reranked = r["retrieved"]
        by_dist = distance_order(reranked)
        d_top = by_dist[0]

        # Tie at the minimum distance whose outcome depends on tie-breaking.
        tied = [e for e in reranked if e["distance"] == d_top["distance"]]
        tie_ambiguous = len({matches(e["source"], exp) for e in tied}) > 1

        dist_ok = matches(d_top["source"], exp)
        rr_ok = r["correct_at_1"]
        per_query.append({
            "id": r["id"],
            "query": r["query"],
            "expected_source": exp,
            "distance_top1": d_top["source"],
            "distance_top1_chunk": d_top["chunk_index"],
            "distance_top1_distance": d_top["distance"],
            "reranked_top1": r["actual_top1"],
            "reranked_top1_chunk": reranked[0]["chunk_index"],
            "reranked_top1_distance": reranked[0]["distance"],
            "distance_correct_at_1": dist_ok,
            "reranked_correct_at_1": rr_ok,
            "hit_in_topk": r["hit_in_topk"],
            "expected_rank_distance": first_rank(by_dist, exp),
            "expected_rank_reranked": first_rank(reranked, exp),
            "category": classify(dist_ok, rr_ok, r["hit_in_topk"]),
            "tie_at_min_distance": len(tied) > 1,
            "tie_ambiguous": tie_ambiguous,
        })

    n = len(per_query)
    cats = {}
    for q in per_query:
        cats[q["category"]] = cats.get(q["category"], 0) + 1
    return {
        "source_file": None,
        "chunker_version": payload["chunker_version"],
        "git_commit": payload["git_commit"],
        "embedding_model_digest": payload["embedding_model_digest"],
        "num_chunks": payload["num_chunks"],
        "num_queries": n,
        "top_k": payload["top_k"],
        "distance_only_correct_at_1_count": sum(q["distance_correct_at_1"] for q in per_query),
        "reranked_correct_at_1_count": sum(q["reranked_correct_at_1"] for q in per_query),
        "hit_in_topk_count": sum(q["hit_in_topk"] for q in per_query),
        "categories": dict(sorted(cats.items())),
        "ambiguous_ties": [q["id"] for q in per_query if q["tie_ambiguous"]],
        "per_query": per_query,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", type=Path, help="Write JSON results here (new file)")
    args = parser.parse_args()

    if args.out and args.out.resolve() in {p.resolve() for p in PROTECTED}:
        parser.error(f"--out must not overwrite an existing evaluation artifact: {args.out}")

    with open(QUERIES_PATH, encoding="utf-8") as f:
        queries = json.load(f)
    payloads = {}
    for v, path in INPUTS.items():
        with open(path, encoding="utf-8") as f:
            payloads[v] = json.load(f)

    errors = [e for v, p in payloads.items() for e in validate(v, p, queries)]
    if errors:
        print("❌ Validation failed — not scoring:", *errors, sep="\n  ", file=sys.stderr)
        return 1
    print("✅ Validation passed (query sets, ranks, stored metrics, reranker residuals)")

    out = {}
    for v, p in payloads.items():
        out[v] = score(p)
        out[v]["source_file"] = INPUTS[v].as_posix()

    print(f"\n{'Metric':<28}{'V1':>8}{'V2':>8}")
    for label, key in (("Distance-only Accuracy@1", "distance_only_correct_at_1_count"),
                       ("Reranked Accuracy@1", "reranked_correct_at_1_count"),
                       ("Hit@5 (reference)", "hit_in_topk_count")):
        print(f"{label:<28}" + "".join(f"{out[v][key]:>5}/{out[v]['num_queries']}" for v in out))
    for v in out:
        print(f"\n{v} categories: {out[v]['categories']}  ambiguous ties: {out[v]['ambiguous_ties']}")
        for q in out[v]["per_query"]:
            if q["category"] != "both_correct":
                print(f"  [{q['id']}] {q['category']:<18} exp={q['expected_source']:<28} "
                      f"rank dist={q['expected_rank_distance']} rr={q['expected_rank_reranked']}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(out, f, indent=2)
            f.write("\n")
        print(f"\nResults saved → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
