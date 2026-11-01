# PKA-AI — ChunkerV2 Evaluation Report

**ChunkerV1** · chunk_size = 1000 chars · overlap = 100 chars  
**ChunkerV2** · soft limit = 1200 chars · hard limit = 2000 chars · no overlap · structure/paragraph/sentence boundaries  
**Evaluation date:** 2026-11-01  
**Commit under test:** `277553bf324f9654cdfc1e5b08f4094cc2853c61`  
**Result files:** `eval_results_v1_isolated.json`, `eval_results_v2_isolated.json`

---

## 1. Objective and Methodology

### Objective

Determine whether ChunkerV2 improves on the ChunkerV1 baseline without regressing retrieval quality, as required by the success criteria in `chunking_v2.md`.

### The two evaluation suites

The project has two independent evaluation suites. Only one of them could be re-run.

| | Suite 1 — Readability eval | Suite 2 — Automated retrieval eval |
|---|---|---|
| Recorded in | `chunking_v1_eval_report.md` (2026-06-15) | `eval_results.json` (2026-06-28) |
| Documents | `doc_a_technical.md`, `doc_b_tutorial.md`, `doc_c_personal.md` | The 17 files in `data/raw/` |
| Queries | 15 (embedded in the report) | 20 (`eval_queries.json`) |
| Retrieval | TF-IDF proxy | `nomic-embed-text` + ChromaDB cosine + heuristic reranker |
| Scoring | Manual inspection of chunk boundaries | Automatic, by expected source filename |
| Metrics | Bad starts, bad ends, clean chunks, context splits | Accuracy@1, Hit Rate@5, wrong rank, complete miss |
| Re-runnable | **No** — the three documents are not in the repository or its history | **Yes** |

**This report covers Suite 2 only.** The V2 specification's readability criteria (Criterion 1 and 2) depend on Suite 1 and remain unevaluated — see [Limitations](#5-limitations).

### Metric definitions (unchanged from `scripts/evaluate_retrieval.py`)

| Metric | Definition | Better |
|---|---|---|
| Accuracy@1 | Expected filename appears in the source path of the rank-1 result | Higher |
| Hit Rate@5 | Expected filename appears in the source path of any top-5 result | Higher |
| Wrong rank | Hit@5 but not correct at rank 1 | Lower |
| Complete miss | Expected source absent from the top 5 | Lower |
| top1_distance | Cosine distance of the rank-1 result (diagnostic only) | Lower |

Matching is by filename rather than chunk ID, so the metrics stay valid when the two chunkers produce different numbers of chunks.

### Isolated-store approach

Each chunker was evaluated by `scripts/evaluate_chunkers.py` in a separate, fresh store:

1. A temporary directory is created for the run (`pka_eval_<chunker>_*` in the OS temp folder).
2. The `CHROMA_DB_PATH` config value is redirected to that directory **before** `src.retrieval.search` and `src.vectorstore.chroma_store` are imported, because both open the default store at import time. The evaluation `ChromaClient` is also injected explicitly into `store_chunks()` and `semantic_search_reranked()`.
3. All documents in `data/raw/` are chunked with the requested chunker only, embedded with `EmbeddingClient`, and stored in collection `eval_v1` or `eval_v2`.
4. An integrity check aborts the run unless the stored chunk count matches and every chunk carries the expected `chunker_version`.
5. The 20 queries run through the production `semantic_search_reranked()` pipeline, and are scored with the unchanged `correct_at_1()` / `hit_in_topk()` functions.
6. The temporary store is deleted after the run.

The original `./chroma_db` is never opened.

### Run parameters

| Parameter | V1 run | V2 run |
|---|---|---|
| Timestamp (UTC) | 2026-11-01T17:47:37 | 2026-11-01T17:48:32 |
| Embedding model | `nomic-embed-text` | `nomic-embed-text` |
| Model digest | `0a109f422b47e3a30ba2b10eca18548e944e8a23073ee3f3e947efcf3c45e59f` | same |
| Documents | 17 | 17 |
| Chunks | 82 | 66 |
| Queries | 20 | 20 |
| top_k | 5 | 5 |
| Reranker | unchanged (`src/utils/reranker.py`) | unchanged |

The 17 documents, 20 queries and `evaluate_retrieval.py` were confirmed identical to their state at the June baseline commit (`3aaeefa`), ignoring line-ending differences.

---

## 2. Reproducibility

### Original V1 baseline vs isolated V1 re-run

| Metric | Baseline (2026-06-28, `./chroma_db`) | Isolated V1 (2026-11-01) | Isolated V1 second run |
|---|---|---|---|
| Accuracy@1 | 13/20 | 13/20 | 13/20 |
| Hit Rate@5 | 17/20 | 17/20 | 17/20 |
| Wrong rank | 4 | 4 | 4 |
| Complete miss | 3 | 3 | 3 |

- **Query-level match with the baseline:** for all 20 queries, `actual_top1`, `correct_at_1`, `hit_in_topk` and `top1_distance` (to 4 decimal places) are identical to `eval_results.json`.
- **Run-to-run determinism:** a second isolated V1 run produced a `results` array identical to the first, including the full top-5 lists and scores.
- **Chunk count:** a fresh V1 ingestion produces 82 chunks, the same as the original store, with the same count per file.

Conclusion: the pipeline, embedding model and dataset have not drifted since the baseline. Differences between V1 and V2 below are attributable to the chunker, and to how the unchanged reranker reacts to its output.

### Preservation of original artifacts

| Artifact | Check | Result |
|---|---|---|
| `./chroma_db/` | SHA-256, mtime and size of every file, before vs after all runs | Identical |
| `data/evaluation/eval_results.json` | SHA-256 before vs after | Identical |
| `data/evaluation/eval_queries.json` | SHA-256 before vs after | Identical |
| Temporary stores | Directory listing after runs | All removed |

---

## 3. Results

| Metric | V1 | V2 | Change |
|---|---|---|---|
| Documents | 17 | 17 | — |
| Chunks | 82 | 66 | −16 (−20%) |
| **Accuracy@1** | **13/20 (65%)** | **10/20 (50%)** | **−3 queries** |
| **Hit Rate@5** | **17/20 (85%)** | **18/20 (90%)** | **+1 query** |
| Wrong rank | 4 | 8 | +4 |
| Complete miss | 3 | 2 | −1 |

### Per-query outcome

`Y/Y` = correct@1 / hit@5.

| ID | Query (short) | V1 | V2 | V2 top-1 source |
|---|---|---|---|---|
| q01 | What is chunking? | −/Y | −/Y | chunking.py |
| q02 | ChunkerV2 improvements | Y/Y | Y/Y | chunking_v2.md |
| q03 | Chunk boundary problems | Y/Y | Y/Y | chunking_v1_eval_report.md |
| **q04** | **Embeddings generation** | **Y/Y** | **−/Y** | **notes.md** |
| **q05** | **Store chunks in ChromaDB** | **−/Y** | **Y/Y** | **chroma_store.py** |
| q06 | Vector store distance metric | −/− | −/− | notes.md |
| q07 | RAG prompt assembly | −/Y | −/Y | rag_assistant.py |
| q08 | System prompt | Y/Y | Y/Y | prompts.py |
| **q09** | **Configured models** | **−/−** | **−/Y** | **llm.py** |
| q10 | Default top_k | −/− | −/− | chunking_v1_eval_report.md |
| q11 | Reranker final score | Y/Y | Y/Y | reranker.py |
| q12 | Continuity bonus | Y/Y | Y/Y | reranker.py |
| q13 | Distance → similarity | Y/Y | Y/Y | helpers.py |
| q14 | Loader file formats | Y/Y | Y/Y | loader.py |
| q15 | RAG pipeline end to end | Y/Y | Y/Y | rag_assistant.py |
| **q16** | **MVP success criteria** | **Y/Y** | **−/Y** | **notes.md** |
| **q17** | **Postponed features** | **Y/Y** | **−/Y** | **notes.md** |
| **q18** | **Chunk metadata** | **Y/Y** | **−/Y** | **prompts.py** |
| q19 | Semantic search query | Y/Y | Y/Y | search.py |
| q20 | Query pipeline wiring | −/Y | −/Y | rag_assistant.py |

Six queries changed outcome: two improved and four regressed. The other 14 have the same outcome under both chunkers.

---

## 4. Query-Level Analysis

### Background: what the reranker can and cannot change

`semantic_search_reranked()` retrieves the top 5 chunks by cosine distance, then `rerank()` re-sorts **those same 5** by:

```
final_score = 1 / (1 + distance)            # distance score
            + (−0.10 if word_count < 40)    # size penalty
            + (+0.15 per adjacent chunk     # continuity bonus
               from the same source in the result set)
```

Two consequences follow directly from the code:

- **Hit Rate@5 is unaffected by the reranker.** It only depends on which 5 chunks are nearest, which is determined by chunking and embedding.
- **Accuracy@1 depends on the reranker.** The rank-1 result can differ from the nearest chunk.

In each table below, distance score (DS), size penalty (SP) and continuity bonus (CB) are reconstructed from the recorded `distance` and `final_score` values. In every case they sum exactly to the recorded `final_score`.

### Improvements

#### q05 — "How do I store chunks in ChromaDB?" (wrong rank → correct@1)

| Run | Rank | Source / chunk | Distance | DS | SP | CB | Final |
|---|---|---|---|---|---|---|---|
| V1 | 1 | chunking_v1_eval_report.md #2 | 0.3538 | 0.739 | 0 | +0.15 | 0.889 |
| V1 | 2 | chunking_v1_eval_report.md #1 | 0.3914 | 0.719 | 0 | +0.15 | 0.869 |
| V1 | 3 | **chroma_store.py #0** | **0.2391** | 0.807 | 0 | 0 | 0.807 |
| V2 | 1 | **chroma_store.py #0** | **0.2394** | 0.807 | 0 | 0 | 0.807 |

**Observation (proven from recorded scores):** `chroma_store.py` was the nearest chunk under both chunkers. In V1, two adjacent eval-report chunks each received +0.15 and outranked it. In V2, the adjacent pair is not retrieved together, so no bonus applies and the nearest chunk stays at rank 1.

**Not proven:** why V2's chunking of the eval report stopped producing an adjacent pair in the top 5.

#### q09 — "What chat and embedding models are configured?" (miss → hit@5)

| Run | Top-5 sources (distance) |
|---|---|
| V1 | llm.py (0.3537), notes.md #3 (0.3750), embedding.py (0.3785), prompts.py #3 (0.3538), query.py #2 (0.3687) |
| V2 | llm.py (0.3537), embedding.py (0.3785), prompts.py #2 (0.3890), **config.py (0.3942)**, notes.md #3 (0.4028) |

**Observation:** `config.py` entered the top 5 at distance 0.3942. Under V1 every top-5 chunk was closer than 0.3942, so `config.py` ranked 6th or lower. Under V2, the competing chunks from `notes.md`, `prompts.py` and `query.py` are further away or absent, which made room for it. This is a retrieval-level change; the reranker played no part.

**Not proven:** `config.py`'s V1 distance was not recorded (it was outside the top 5), so whether its own embedding changed cannot be confirmed from these results. Accuracy@1 still fails because `llm.py` is the nearest chunk under both chunkers.

### Regressions

In all four regressions, the expected source is the **nearest chunk in the top 5** under V2, but the reranker moved it down.

#### q04 — "What are embeddings and how are they generated?"

| Run | Rank | Source / chunk | Distance | DS | SP | CB | Final |
|---|---|---|---|---|---|---|---|
| V1 | 1 | **embedding.py #0** | **0.3214** | 0.757 | 0 | 0 | 0.757 |
| V1 | 2 | notes.md #4 | 0.3282 | 0.753 | 0 | 0 | 0.753 |
| V2 | 1 | notes.md #3 | 0.3519 | 0.740 | 0 | +0.15 | 0.890 |
| V2 | 2 | notes.md #4 | 0.4509 | 0.689 | 0 | +0.15 | 0.839 |
| V2 | 3 | **embedding.py #0** | **0.3214** | 0.757 | 0 | 0 | 0.757 |

The `embedding.py` chunk scores exactly the same in both runs. The change is that V2 retrieves two adjacent `notes.md` chunks, and they boost each other above it.

#### q16 — "What are the MVP success criteria?"

| Run | Rank | Source / chunk | Distance | DS | SP | CB | Final |
|---|---|---|---|---|---|---|---|
| V1 | 1 | **project_mvp.md #3** | 0.3318 | 0.751 | 0 | +0.15 | 0.901 |
| V1 | 2 | project_mvp.md #2 | 0.4674 | 0.682 | 0 | +0.15 | 0.832 |
| V2 | 1 | notes.md #8 | 0.4877 | 0.672 | 0 | +0.30 | 0.972 |
| V2 | 2 | notes.md #7 | 0.4583 | 0.686 | 0 | +0.15 | 0.836 |
| V2 | 3 | notes.md #9 | 0.4869 | 0.673 | 0 | +0.15 | 0.823 |
| V2 | 4 | **project_mvp.md #0** | **0.3833** | 0.723 | 0 | 0 | 0.723 |

In V1, the continuity bonus *helped*: adjacent `project_mvp.md` chunks reinforced each other. In V2, `project_mvp.md` is 3 chunks instead of 4, and the two retrieved (#0 and #2) are not adjacent. Meanwhile, three consecutive `notes.md` chunks give #8 a +0.30 bonus. The worst-distance chunk in the top 5 (0.4877) ends up at rank 1.

#### q17 — "What features are postponed after the MVP?"

| Run | Rank | Source / chunk | Distance | DS | SP | CB | Final |
|---|---|---|---|---|---|---|---|
| V1 | 1 | **project_mvp.md #2** | 0.3853 | 0.722 | 0 | +0.15 | 0.872 |
| V2 | 1 | notes.md #2 | 0.4715 | 0.680 | 0 | +0.15 | 0.830 |
| V2 | 2 | notes.md #1 | 0.4826 | 0.674 | 0 | +0.15 | 0.825 |
| V2 | 3 | **project_mvp.md #0** | **0.4662** | 0.682 | 0 | 0 | 0.682 |

The same pattern as q16: an adjacent `notes.md` pair outranks a closer, isolated `project_mvp.md` chunk.

#### q18 — "What metadata does each chunk include?"

| Run | Rank | Source / chunk | Distance | DS | SP | CB | Final |
|---|---|---|---|---|---|---|---|
| V1 | 1 | **chunking.py #1** | 0.3014 | 0.768 | 0 | +0.15 | 0.918 |
| V1 | 2 | chunking.py #0 | 0.3541 | 0.739 | 0 | +0.15 | 0.889 |
| V2 | 1 | prompts.py #1 | 0.3087 | 0.764 | 0 | 0 | 0.764 |
| V2 | 4 | **chunking.py #1** | **0.3013** | 0.769 | **−0.10** | 0 | 0.669 |

Here the size penalty is responsible. V2 splits `data/raw/chunking.py` into chunks of 134 and 26 words; V1 produced 110 and 59. The 26-word V2 chunk #1 is the nearest match, but it falls below the 40-word threshold and loses 0.10. It also lacks the V1 continuity bonus, because chunk #0 is no longer retrieved alongside it.

### Observations vs proven causes

**Proven** — follows directly from the recorded scores and the reranker code:

- In q04, q16, q17 and q18, the expected source was the nearest chunk in V2's top 5, and the reranker moved it below rank 1.
- In q04, q16 and q17, the decisive factor was the continuity bonus given to adjacent `notes.md` chunks. In q18 it was the size penalty on a 26-word chunk.
- In q05, the improvement came from the *absence* of a continuity bonus that had misfired in V1.
- The Hit Rate@5 changes (q09) are retrieval-level and independent of the reranker.

**Observed but not proven:**

- **Single-chunk documents.** A document stored as one chunk can never receive a continuity bonus. V2 turns more documents into a single chunk (`embedding.py`, `helpers.py`, `loader.py` and `chunking_v1.md` went from 2 chunks to 1), so those documents may be systematically disadvantaged against multi-chunk documents like `notes.md`. This is plausible, but has not been measured.
- **No overlap.** V2's lack of overlap changes which chunks land together in the top 5. Its contribution has not been isolated.
- **Whether V2 would match or beat V1 without the reranker** has not been tested. The pre-rerank (distance) ordering is recorded in both result files, but no distance-only score has been computed, because that would be a new metric outside the agreed methodology.
- **Statistical significance.** With 20 queries, each query is worth 5 percentage points. A 3-query difference in Accuracy@1 is suggestive, not conclusive.

---

## 5. Limitations

1. **The original readability evaluation documents are missing.** `doc_a_technical.md`, `doc_b_tutorial.md` and `doc_c_personal.md` are not in the repository or its git history, and no TF-IDF script was committed. Suite 1 cannot be reproduced.
2. **Readability was not evaluated.** Bad starts, bad ends, clean chunks and context splits — the primary targets of `chunking_v2.md` Criteria 1 and 2 — were not measured for either chunker.
3. **V2 is incomplete relative to its specification.** It does not yet implement overlap, heading (Level 1) splitting or the extended metadata schema (`boundary_quality`, `parent_section`, etc.). Criterion 4 (metadata completeness) cannot be evaluated. These results describe the current V2, not the specified design.
4. **The reranker heuristics were tuned for V1.** The 40-word size threshold and the +0.15 adjacency bonus were designed around V1's uniform ~1000-character chunks. V2 produces fewer, more varied chunks and more single-chunk documents, and the analysis above shows these heuristics deciding the outcome of all four regressions.
5. **Small sample.** 20 queries; one query = 5 percentage points.
6. **Labelled by source file, not by answer.** The metrics confirm the right *file* was retrieved, not that the retrieved chunk contains a complete answer. The readability benefit V2 targets is invisible to them.
7. **Corpus composition.** 12 of the 17 indexed documents are Python files, which contain little prose. V2's paragraph and sentence logic has limited opportunity to show its benefit there.

---

## 6. Conclusion

- **V2 improves Hit Rate@5 from 85% to 90%** (17 → 18 of 20): the correct source reaches the top 5 slightly more often.
- **V2 reduces Accuracy@1 from 65% to 50%** (13 → 10 of 20): the correct source is ranked first less often.
- **The current implementation does not satisfy the specification's no-regression criterion.** `chunking_v2.md` Criterion 3 states that retrieval quality is the floor, and that a correct chunk dropping from rank 1 counts as a regression. Four queries regressed this way.
- **The readability improvement — V2's main purpose — remains unverified.** No boundary-quality measurement exists for this comparison.
- **The regressions appear to come mainly from the reranker's interaction with V2's chunk structure, not from worse embedding matches.** In every regressed query, the correct source was the nearest chunk in the top 5. Reranker compatibility should be investigated before drawing conclusions about V2 itself.

**ChunkerV2 should not replace ChunkerV1 in production ingestion at this stage.**

---

## 7. Recommended Follow-Up Work

### 1. Reranker heuristic investigation and calibration

- Record pre-rerank (distance-only) rank alongside final rank for every query, as `failure_analysis.md` already recommends ("Log the raw cosine rank alongside the final rerank rank for every failure"). Both result files already contain the data needed.
- Evaluate whether the continuity bonus should be capped, scaled, or replaced. It currently rewards documents for being split into many chunks and penalises single-chunk documents.
- Re-examine the 40-word size threshold against V2's chunk-length distribution. V2 deliberately keeps short structural units (such as a short code tail) as their own chunks.
- Any reranker change must be evaluated against **both** chunkers with `scripts/evaluate_chunkers.py`, so V1 and V2 remain comparable. Any new metric definition should be agreed before it is introduced.

### 2. New manual readability comparison using the 17 indexed documents

- Apply the Suite 1 rubric (bad start, bad end, clean chunk) to V1's 82 and V2's 66 chunks of the `data/raw/` corpus.
- Report the result as a **new baseline on a new corpus**. It is not comparable with the original 81% / 75% / 0% figures, which came from different documents.
- Where possible, write expected answers for the 20 queries, so context splits (answer spans 2+ chunks) can also be assessed.
- Separately, search for the original `doc_a/b/c` documents outside the repository. If found, commit them to `data/evaluation/` so Suite 1 becomes reproducible.

### 3. Re-evaluate after V2 is complete

Repeat both evaluations once overlap and heading splitting are implemented, since both are likely to change which chunks are retrieved together.
