# Answer-level Evaluation Dataset — Design Notes

**Dataset:** `answer_eval_dataset.json` (36 cases)
**Created:** 2026-11-21
**Knowledge-base snapshot:** `data/raw/`, 17 files. Combined fingerprint `3ecabcd6a87f5b79` (sha256 of the files concatenated in name order with CRLF normalised to LF; per-file hashes in §9).
**Status:** Design and data only. No answer-evaluation pipeline exists yet.

---

## 1. Purpose

The retrieval benchmark (`eval_queries.json`) checks whether the expected *source file* is ranked first or appears in the top 5. It cannot tell whether the final answer is correct, complete, grounded, or appropriately refuses.

This dataset adds that layer. Each case defines a question, a reference answer, the verbatim evidence for that answer, and explicit criteria for judging a generated response. Its purpose is repeatable comparison of system versions (chunkers, reranker settings, prompts, models) on answer quality.

## 2. Schema

The file is a plain JSON array, the same container format as `eval_queries.json`. Every case has all 14 fields.

| Field | Type | Definition |
|---|---|---|
| `id` | string | `a01`…`a36`. Stable; never reused. |
| `query` | string | The question submitted to PKA-AI, verbatim. |
| `category` | enum | Evaluation dimension: `direct_fact`, `multi_chunk_synthesis`, `contextual`, `precision`, `insufficient_information`, `ambiguous` (see §4). |
| `difficulty` | enum | `easy` / `medium` / `hard`. A design-time judgement (§6). |
| `expected_behavior` | enum | `answer`: a definitive answer exists. `answer_with_caveat`: the KB conflicts or requires interpretation, so a good answer surfaces that. `abstain`: the KB cannot answer. |
| `expected_answer` | string \| null | A reference answer written only from the evidence. **`null` for every `abstain` case**, so no fabricated reference exists. |
| `key_points` | string[] | Atomic facts a complete answer must contain. Basis for completeness scoring. Empty for `abstain`. |
| `forbidden_claims` | string[] | Statements whose presence is a failure (hallucinations, distractor confusions, outside knowledge). Basis for precision and faithfulness scoring. Required for `abstain`. |
| `evidence` | `{source, quote}[]` | **Support for the expected answer.** Each quote is a verbatim substring of `data/raw/<source>`. Empty for `abstain`. |
| `distractors` | `{source, quote}[]` | Verbatim passages that are related but wrong for this query. Used to diagnose why an answer went wrong. |
| `relevant_sources` | string[] | Files supporting the answer. Must equal the set of `evidence` sources. |
| `acceptance_criteria` | string | **The rule for grading a generated response**, including partial-credit and unacceptable cases. |
| `related_retrieval_query` | string \| null | The `eval_queries.json` id covering the same topic, so answer and retrieval failures can be cross-referenced. |
| `notes` | string | Known traps, KB-snapshot sensitivity, and links to known retrieval failures. |

The fields separate three concerns, as the task requested:
- **The answer:** `expected_answer`, broken down into `key_points`.
- **The evidence:** `evidence`, `relevant_sources`, and `distractors` as counter-evidence.
- **The grading:** `expected_behavior`, `acceptance_criteria` and `forbidden_claims`.

### Fields considered and not adopted

- **`relevant_chunks` (chunk IDs):** chunk IDs are `{source}_ch{chunk_index}` and differ between ChunkerV1 and ChunkerV2 (82 vs 66 chunks), so any fixed ID list would be wrong for one of them. Verbatim `evidence` quotes are chunker-independent. A pipeline can resolve them to the chunks of whichever store is under test by substring match, which allows evidence recall to be computed for each chunker.
- **Dataset-level metadata wrapper** (version, KB hash): this would break the plain-array convention of `eval_queries.json`. The KB fingerprint is recorded in this document instead.

## 3. Design decisions

1. **The KB, not the repository, is the ground truth.** `data/raw` holds *snapshot copies* of project files, several older than the live `src/`. Examples: `loader.py` supports `.txt/.md` only; `chunking_v2.md` says "not yet implemented"; the snapshot `rag_assistant.py` predates conversation memory. Expected answers reflect what the assistant can actually see. Cases sensitive to this are flagged in `notes` (a07, a28).
2. **Use real inconsistencies for ambiguity.** All four `ambiguous` cases come from contradictions that already exist in the KB, not from contrived prompts:
   - a25: `normalize_similarity`'s docstring vs its formula.
   - a31: two different `SYSTEM_PROMPT`s.
   - a32: an unchecked action item vs code that already implements it.
   - a33: the documented vs the imported constants path.
3. **Insufficient-information cases have tempting near-misses.** Each one has a `distractors` entry from a related passage (temperature defined but never configured, hardware mentioned generically, V2 targets that are not results, project progress without a deadline), so abstention is tested under pressure, not trivially.
4. **False-premise questions are not abstentions.** a29 ("which book am I reading?") has a stated answer ("to be decided"), so it is a `precision` case.
5. **Reuse of retrieval queries.** 14 cases link to an `eval_queries.json` query. The questions were reworded to target a specific answer, and the expected sources were re-derived from the evidence rather than copied. Cases a01 (q10) and a15 (q06) deliberately cover topics where retrieval is a complete miss for both chunkers.
6. **No answer depends on outside knowledge.** Derived statements (e.g. a25's "0.0" from evaluating the formula, a17's model-vs-heuristic distinction) are marked `answer_with_caveat` and their criteria accept a transparent "the KB does not say" response.

## 4. Coverage

| Dimension | Cases | Ids |
|---|---:|---|
| `direct_fact` | 9 | a01 a02 a03 a05 a06 a07 a09 a34 a36 |
| `precision` | 7 | a04 a14 a21 a22 a23 a24 a29 |
| `contextual` | 7 | a15 a16 a17 a18 a19 a20 a35 |
| `multi_chunk_synthesis` | 5 | a08 a10 a11 a12 a13 |
| `insufficient_information` | 4 | a26 a27 a28 a30 |
| `ambiguous` | 4 | a25 a31 a32 a33 |

**Difficulty:** 12 easy, 17 medium, 7 hard.
**Expected behaviour:** 27 `answer`, 5 `answer_with_caveat`, 4 `abstain`.
**Domains:** 8 cases cover personal productivity and goals (a04 a05 a06 a09 a19 a24 a29 a34); the rest cover the project's technical documents and code.

**Source coverage:** all 17 KB files support at least one case. 11 cases need more than one file.

| Source | Cases |
|---|---:|
| notes.md | 15 |
| project_mvp.md, chunking_v2.md | 4 each |
| prompts.py | 3 |
| config.py, reranker.py, query.py, chroma_store.py, chunking_v1.md, chunking.py, chunking_v1_eval_report.md | 2 each |
| loader.py, helpers.py, llm.py, search.py, embedding.py, rag_assistant.py | 1 each |

**"Multi-chunk" is about passages, not chunk counts.** The category means the answer combines several separate passages (sections, list items, files). How many chunks that takes depends on the chunker. Reproducing ChunkerV1's deterministic 1000/100 window over the KB shows:
- All 108 evidence quotes fit inside a single V1 chunk.
- 17 cases need evidence from at least 2 V1 chunks.
- No case needs more than 5, so every case is answerable from a top-5 context in principle.
- a13 is labelled synthesis but fits in one V1 chunk.

Compute the chunk spread for each chunker at evaluation time; don't rely on the label.

## 5. Construction methodology

1. Read all 17 KB files in full.
2. For each candidate question, located the supporting text first, then wrote the question and the reference answer from that text only.
3. Recorded each supporting line verbatim as an `evidence` quote, and recorded competing passages as `distractors`.
4. Wrote `key_points`, `forbidden_claims` and `acceptance_criteria`. For abstain cases: `expected_answer = null`, no evidence, and explicit forbidden claims.
5. Dropped candidates that duplicated another case's evidence. For example, a "plain vs reranked search in query.py" question was folded into a12 as a forbidden claim, and a separate "ChunkerV2 status" question was dropped because a28 covers it.

## 6. Quality review

The validator (run 2026-11-21, result PASS) checked the following:
- **Schema:** all 14 fields are present with the correct types and enum values, and ids are unique and sequential.
- **Evidence:** every `evidence` and `distractors` quote occurs verbatim in its source file (after CRLF→LF), and no quote is both evidence and distractor.
- **Source consistency:** `relevant_sources` equals the set of evidence sources.
- **Behaviour rules:**
  - `abstain` ⇔ `insufficient_information`, with a null answer, no evidence and non-empty forbidden claims.
  - Answerable cases have an answer, evidence and key points.
  - Every `ambiguous` case is `answer_with_caveat`.
- **Retrieval links:** `related_retrieval_query` ids exist in `eval_queries.json`.
- **Near-duplicates:** one query pair was flagged (a21 chat model vs a26 temperature). I reviewed it as a false positive: the queries share vocabulary but test different things.

### Problems found and fixed during review
- a14 and a18 listed supporting sources with no evidence quote.
- a33 linked to an unrelated retrieval query.
- A note on a19 claimed a quote was non-unique; it wasn't.

### Residual concerns
- **Concentration on notes.md:** 15/36 cases. It is the largest prose document and the only personal one, but a weak spot in notes.md handling will weigh heavily.
- **Difficulty labels are a single author's judgement** and have not been validated against observed failure rates.
- **Interpretive cases** (a17, a32) need human or carefully prompted LLM judgement. Keyword matching won't grade them reliably.

## 7. Known limitations

1. **Small and single-author.** 36 cases, one writer, no second annotator, so ambiguity in questions and criteria has had one reviewer only.
2. **Snapshot coupling.** Refreshing `data/raw` (e.g. syncing the live `src/`) will invalidate a07 and a28 and may break evidence quotes. Re-run the validator after any KB change.
3. **The corpus is about itself.** The KB is mostly the project's own code and docs, so the model's pretraining knowledge of RAG, ChromaDB or Ollama can produce answers that are plausible but ungrounded. `forbidden_claims` covers the most likely ones only.
4. **Single-turn only.** The live `RAGAssistant` has conversation memory; multi-turn behaviour is not covered.
5. **Few abstention cases.** 4 cases are enough for a smoke test, not for a reliable abstention-rate estimate.
6. **Original eval documents are missing.** The original eval documents (doc_a/b/c) are not in the KB, so their content cannot be tested.

## 8. Implications for a future answer-evaluation pipeline

- **Isolation:** reuse the `evaluate_chunkers.py` pattern (temporary store, CHROMA_DB_PATH redirected before import). Never query `./chroma_db` from an evaluation.
- **Fresh state per case:** create a new `RAGAssistant` or `ConversationMemory` for each case. Otherwise earlier answers leak into later prompts.
- **Record everything:** for each case, store the answer, retrieved chunks with distances and rerank scores, sources and prompt. This allows re-scoring without re-generation, as was done for distance-only Accuracy@1.
- **Separate metrics:**
  - Evidence recall: share of evidence quotes contained in retrieved chunks.
  - Key-point coverage.
  - Forbidden-claim rate.
  - Abstention correctness: `abstain` cases vs answerable cases that wrongly abstain.
  - Caveat detection for `answer_with_caveat`.
  - Comparing evidence recall with answer correctness separates retrieval failures from generation failures.
- **Refusal detection:** the exact string `I don't know based on the provided context.` is a strict check. a03 is a correct answer that *contains* that string, so detection must be case-aware.
- **Grading method:** key points and forbidden claims suit a deterministic check plus an LLM judge. Interpretive cases need a rubric-based judge or human review. The judge model must be fixed and recorded, like the embedding digest, or scores won't be comparable across runs.
- **Determinism:** the chat call sets no temperature (see a26). Fix generation settings or run several samples before comparing versions.

## 9. Recommendations for expansion

1. Add a second reviewer pass on acceptance criteria before the first scored run.
2. Grow `insufficient_information` and `ambiguous` to about 8 each for usable rates.
3. Add cases on under-covered sources (search.py, rag_assistant.py, loader.py), and reduce the share from notes.md as the KB grows.
4. Add multi-turn cases once the KB snapshot includes the memory-aware assistant.
5. Version the dataset in this document's header whenever cases change. Never renumber or reuse ids.

### KB snapshot fingerprint (sha256 of LF-normalised content, first 12 hex chars)

```
772bba1e28d1  chroma_store.py          5d3ba5b12b88  helpers.py
cfe5802b45cd  chunking.py              4bd475fdcd03  llm.py
09da9c2b5b12  chunking_v1.md           98bd4f44b0ed  loader.py
8ce7d1a63cc3  chunking_v1_eval_report  c5c970021d8d  notes.md
c3fb4276349e  chunking_v2.md           4f1b2c6346b8  project_mvp.md
67b60c4439dc  config.py                ab7caa375cdf  prompts.py
3a3cb6b7bf7e  embedding.py             c761e1c130cd  query.py
63d0dfa365ae  rag_assistant.py         9f4f28f36ef9  reranker.py
f152a693467c  search.py
```
