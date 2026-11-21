# Distance-only Accuracy@1 — ChunkerV1 vs ChunkerV2

**Date:** 2026-11-21
**Inputs (unchanged):** `eval_results_v1_isolated.json`, `eval_results_v2_isolated.json` (Task 24 runs, 2026-11-01, commit `277553b`, nomic-embed-text digest `0a109f42…`)
**Script:** `scripts/rescore_distance_only.py` (stdlib only; never imports `src.*`, never opens ChromaDB)
**Output:** `distance_only_acc1.json`

## 1. Results

| Metric (n = 20 queries) | V1 | V2 |
|---|---:|---:|
| **Distance-only Accuracy@1** | **12/20** | **14/20** |
| Existing final (reranked) Accuracy@1 | 13/20 | 10/20 |
| Hit@5 (reference; identical under both orderings) | 17/20 | 18/20 |
| Net reranker effect on Acc@1 | +1 | −4 |

## 2. Metric definition and method

- **Accuracy@1 rule (unchanged):** a query counts as correct when its `expected_source` string is a substring of the rank-1 chunk's source path (`correct_at_1()` in `scripts/evaluate_retrieval.py`). The re-score uses the same rule, queries and expected sources. Only the ordering changes.
- **Why this is valid without re-running retrieval:** `semantic_search_reranked()` = `rerank(semantic_search(query, top_k=5))`. `rerank()` only re-sorts the 5 chunks ChromaDB returned. It never adds or removes candidates. The stored `retrieved` lists therefore contain exactly the distance top-5, each with its raw cosine `distance`.
- **Distance-only rank 1:** the stored entry with the smallest `distance`, which is the chunk `semantic_search()` would rank first. No query has a tie at the minimum distance.
- **Hit@5** is identical under both orderings because both see the same 5 chunks.

## 3. Evaluation dataset

- 20 queries from `eval_queries.json`. The ids, texts and expected sources are identical in both result files (checked by the script).
- The corpus is the same 17 documents in `data/raw`, chunked into 82 chunks for V1 and 66 for V2. Each chunker was evaluated in its own isolated temporary store.

## 4. Per-query findings

Ranks are the position of the first chunk from the expected source (— = not in the top 5). The signal column comes from the stored score decomposition (`final_score − 1/(1+distance)`).

### Distance-only correct, reranked wrong (reranking hurt)

| Chunker | Query | Expected | Rank: dist → reranked | What moved it, from the score decomposition |
|---|---|---|---|---|
| V1 | q05 | chroma_store.py | 1 → 3 | +0.15 continuity on two adjacent `chunking_v1_eval_report.md` chunks |
| V1 | q20 | query.py | 1 → 3 | +0.15 continuity on two adjacent `rag_assistant.py` chunks |
| V2 | q04 | embedding.py | 1 → 3 | +0.15 continuity on two adjacent `notes.md` chunks |
| V2 | q16 | project_mvp.md | 1 → 4 | +0.30/+0.15 continuity on three adjacent `notes.md` chunks |
| V2 | q17 | project_mvp.md | 1 → 3 | +0.15 continuity on two adjacent `notes.md` chunks |
| V2 | q18 | chunking.py | 1 → 4 | −0.10 size penalty on the expected chunk (<40 words) |

### Reranked correct, distance-only wrong (reranking helped)

| Chunker | Query | Expected | Rank: dist → reranked | What moved it |
|---|---|---|---|---|
| V1 | q03 | chunking_v1_eval_report.md | 2 → 1 | continuity on three adjacent expected chunks |
| V1 | q11 | reranker.py | 2 → 1 | continuity on adjacent expected chunks; −0.10 size penalty on the distance-top `search.py` chunk |
| V1 | q18 | chunking.py | 3 → 1 | continuity on two adjacent expected chunks |
| V2 | q03 | chunking_v1_eval_report.md | 2 → 1 | continuity on three adjacent expected chunks |

### Both fail

| Chunker | Query | Expected | Rank: dist / reranked | Type |
|---|---|---|---|---|
| V1 | q01 | chunking_v1.md | 4 / 4 | in top 5, not first |
| V1 | q07 | prompts.py | 2 / 4 | in top 5, not first |
| V1 | q06 | chroma_store.py | — | complete miss |
| V1 | q09 | config.py | — | complete miss |
| V1 | q10 | config.py | — | complete miss |
| V2 | q01 | chunking_v1.md | 2 / 3 | in top 5, not first |
| V2 | q07 | prompts.py | 5 / 5 | in top 5, not first |
| V2 | q09 | config.py | 4 / 4 | in top 5, not first |
| V2 | q06 | chroma_store.py | — | complete miss |
| V2 | q10 | config.py | — | complete miss |

q06 and q10 are complete misses for both chunkers, and q01 and q07 fail for both under either ordering. Reranking cannot fix these, because the gap is in retrieval or in the query set.

### V1 vs V2 under distance-only

V2 is correct on q11 and q18 where V1 is not. V1 has no distance-only wins over V2. All other queries agree.

## 5. Interpretation

- **Per query:** in every changed outcome, the decomposition shows which signal flipped rank 1. The continuity bonus produced every "helped" case and 5 of the 6 "hurt" cases. In each of those, it lifted adjacent chunks, either from the expected document or from a competing one. The size penalty caused the remaining hurt case (V2 q18).
- **The pattern is asymmetric only in V2:** there, reranking hurt 5 queries and helped 1. One plausible but untested explanation is that V2's structure-aware splitting creates more adjacent same-document pairs and more short chunks, which the reranker's fixed constants were tuned against V1. That would need checking with the chunk-level data.
- **For V1, the reranker is close to neutral:** 3 helped and 2 hurt, net +1.
- **What this does not show:** with n = 20, neither difference is statistically meaningful. V1 vs V2 distance-only differs on 2 queries (2–0, exact two-sided sign test p = 0.50). The V2 reranker effect is 5–1 (p ≈ 0.22). V2's distance-only lead also depends partly on V2 q18, where the expected chunk wins by a distance margin of only **0.0004**. "V2 retrieves better than V1" is not established. What is established is that the current reranker removes V2's distance-only advantage on this query set.

## 6. Limitations and sources of bias

1. **Small sample:** 20 queries, each worth 5 percentage points.
2. **Single run:** one embedding run per chunker. Run-to-run stability was not measured.
3. **Rounding:** distances are stored rounded to 4 decimal places. No rank-1 ties exist at that precision, but V2 q18 (gap 0.0004) is effectively within noise.
4. **Approximate search:** HNSW search is approximate. The stored top 5 is whatever ChromaDB returned, not a guaranteed exact nearest-neighbour set. This affects both orderings equally.
5. **Coarse matching rule:** the substring rule credits any chunk from the expected file, not the specific passage that answers the query.
6. **Query set bias:** the queries were written against the V1-era corpus and expected sources, and `data/raw` contains copies of the project's own code and docs. Some queries have plausible alternative answers. For example, the `notes.md` chunks in q04, q16 and q17 may be genuinely relevant.
7. **Missing reproducibility inputs:** the V2 spec's readability criteria cannot be reproduced because doc_a/b/c are missing. This re-score does not depend on them.

## 7. Validation

The script refuses to score unless all of the following hold for both files:
- The query set matches `eval_queries.json`.
- Every query has exactly 5 entries ranked 1–5.
- `retrieved[0]` matches the stored `actual_top1` and `top1_distance`.
- The stored `correct_at_1` and `hit_in_topk` values can be reproduced from `retrieved`.
- `final_score` is non-increasing, which confirms the stored order is the reranked order.
- For every entry, `final_score − 1/(1+distance)` equals a valid reranker bonus (size penalty plus a multiple of 0.15), which confirms `distance` is the raw value the reranker scored.
- The summary counts match the recomputed values.

The validator was also tested against six deliberately corrupted in-memory copies and caught all six. A separate one-line recomputation gave the same 12 and 14. The input files' SHA-256 hashes were unchanged after the run.
