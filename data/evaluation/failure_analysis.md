# Phase E — Block 8: Failure Pattern Identification
# PKA-AI Retrieval Failure Analysis

**Status:** Active evaluation  
**System under test:** ChunkerV1 + nomic-embed-text + ChromaDB cosine + heuristic reranker  
**Evaluation corpus:** 3 test documents (doc_a_technical, doc_b_tutorial, doc_c_personal) — 16 chunks total  
**Prior baseline:** V1 eval report (15 queries, 3 docs, TF-IDF proxy)

---

## Failure Definition

A retrieval failure is any case where:

- Answer is incorrect or misleading
- Answer is incomplete (key facts present in corpus but absent from answer)
- Retrieved chunks exist but lack the information needed to answer
- Hallucination fills a gap that retrieved context should have covered
- Correct chunk was retrieved but at rank 2+ while an inferior chunk ranked 1

LLM tone or phrasing is **not** a failure criterion here. Only retrieval-driven failures count.

---

## Failure Log Template

Copy this block for each failed query:

```
---
Query ID    : [e.g. A-03]
Document    : [doc_a_technical | doc_b_tutorial | doc_c_personal | mixed]
Query       : [exact query text]

Expected answer (key points):
- [point 1]
- [point 2]

Retrieved chunks (rank order):
  Rank 1 | source: ___ | chunk: ___ | similarity: ___ | rerank: ___
         | text preview: "..."
  Rank 2 | source: ___ | chunk: ___ | similarity: ___ | rerank: ___
         | text preview: "..."
  Rank 3 | ...

Final answer produced:
[paste LLM output]

What went wrong:
[your free-text note before classification]

Primary failure bucket: [ CHUNKING | SIMILARITY | MISSING_CONTEXT ]
Secondary bucket (if any): [ CHUNKING | SIMILARITY | MISSING_CONTEXT | NONE ]

Evidence for classification:
[1–2 sentences tying the bucket to the specific observation]
---
```

---

## Pre-Loaded Failures from V1 Evaluation Report

The V1 eval report already contains 5 confirmed retrieval failures across the 15 test queries. These are pre-classified below using the Block 8 taxonomy to give you a starting point and a calibration reference.

---

### Failure A-02 — "How do I add documents to ChromaDB?"

```
Query ID    : A-02
Document    : doc_a_technical
Query       : How do I add documents to ChromaDB?

Expected answer (key points):
- collection.add() call
- documents, embeddings, ids parameters
- Complete code example

Retrieved chunks:
  Rank 1 | chunk 1 | similarity: 0.25
         | text preview: "n collection = client.get_or_create_collection(…"
  (chunk 2 holds the other half of the code block)

Final answer produced: [not recorded in V1 — inferred from chunk content]

What went wrong:
The .add() code example is split across chunks 1 and 2. Chunk 1 starts
mid-word ("n collection") — the variable name was severed at the boundary.
The LLM receives an orphaned code fragment with no recoverable declaration.

Primary failure bucket: CHUNKING
Secondary bucket: NONE

Evidence:
V1 report explicitly states "context split with chunk 2" and the chunk
inspection confirms chunk 1 starts mid-word. The add() example spans
the chunk boundary; a single chunk cannot answer this fully.
```

---

### Failure A-03 — "What distance metrics does ChromaDB support?"

```
Query ID    : A-03
Document    : doc_a_technical
Query       : What distance metrics does ChromaDB support?

Expected answer (key points):
- List of supported distance functions (cosine, l2, ip)
- Metadata setting for hnsw:space
- The metrics table

Retrieved chunks:
  Rank 1 | chunk 3 | similarity: 0.14
         | text preview: "ended for production)…"

What went wrong:
The distance-metrics table is split across chunks 2 and 3. Chunk 3 starts
mid-word ("ended for production)"). The table header and first rows are
in chunk 2; the remaining rows are in chunk 3. Neither chunk is self-contained.

Primary failure bucket: CHUNKING
Secondary bucket: NONE

Evidence:
V1 report: "Context split with chunk 2 — table cut across boundary."
Score of 0.14 is also the second-lowest in the document batch, suggesting
the embedding of an incomplete table is a weaker semantic signal.
```

---

### Failure A-04 — "How do I make ChromaDB data persist?"

```
Query ID    : A-04
Document    : doc_a_technical
Query       : How do I make ChromaDB data persist?

Expected answer (key points):
- PersistentClient usage
- path parameter
- Code example

Retrieved chunks:
  Rank 1 | chunk 2 | similarity: 0.12

What went wrong:
Persistence code spans chunks 2 and 3. Score 0.12 is the lowest in the
document. The incomplete code example degrades the embedding — an
unfinished code block does not cleanly encode "persistence" semantics.

Primary failure bucket: CHUNKING
Secondary bucket: SIMILARITY

Evidence:
The low similarity score (0.12) relative to other same-doc queries
suggests the fragmented code block weakened the embedding signal.
This is a compounding failure: chunking broke the code block, which
degraded the embedding, which suppressed the similarity score.
```

---

### Failure B-03 — "Why does chunk size matter?"

```
Query ID    : B-03
Document    : doc_b_tutorial
Query       : Why does chunk size matter?

Expected answer (key points):
- Trade-off between specificity and context
- Too small → no context
- Too large → diffuse embedding

Retrieved chunks:
  Rank 1 | chunk 3 | similarity: 0.11

What went wrong:
The explanation of chunk size spans chunks 3 and 4. Chunk 3 starts with
" 5: Retrieval and Generation" (a section number without its heading).
The body of the chunk-size explanation is split across the boundary.

Primary failure bucket: CHUNKING
Secondary bucket: NONE

Evidence:
V1 report: "context split with chunk 4." Chunk 3 begins with a section
label that lost its introductory heading — the heading was cut into
the previous chunk, leaving a fragment that starts mid-sentence.
```

---

### Failure C-04 — "What would be done differently next time?"

```
Query ID    : C-04
Document    : doc_c_personal
Query       : What would be done differently next time?

Expected answer (key points):
- "What I Would Do Differently" section content
- Specific retrospective insights

Retrieved chunks:
  Rank 1 | chunk 0 | similarity: 0.15
  (Correct chunk: chunk 5)

What went wrong:
Chunk 5 starts with "00 produced too many fragments" — the "5" from
"500" was cut into chunk 4. The heading "What I Would Do Differently"
is therefore missing its first character. Embedding of a headingless
fragment does not match the query's keywords.
Chunk 0 (the summary header) ranked above chunk 5 despite containing
no relevant content.

Primary failure bucket: CHUNKING
Secondary bucket: SIMILARITY

Evidence:
This is a vocabulary failure caused by boundary damage. The query
keyword "differently" exists in the correct section heading, but that
heading was mutilated — losing "5" and a newline. The embedding of
the damaged chunk under-represents the section's topic. Chunk 0
"steals" rank 1 because its summary language superficially matches
"next time" better than the garbled chunk 5.
```

---

## Suggested New Queries for Expanded Evaluation

The 15 V1 queries cover the existing documents adequately for boundary testing but leave several failure modes untested. Run these additional queries to surface similarity and missing context failures — which the V1 set under-sampled because chunking failures dominated.

### Designed to test SIMILARITY failures

These queries use vocabulary that is semantically adjacent but not the same as the document text. If the embedding model over-weights surface keywords, these will retrieve the wrong chunk.

| ID | Query | Target doc | Expected chunk |
|----|-------|-----------|----------------|
| S-01 | "How does the system store vector data?" | doc_a_technical | chunk describing ChromaDB collection setup |
| S-02 | "What makes two pieces of text similar in this system?" | doc_a_technical | chunk describing distance/cosine metric |
| S-03 | "How are documents broken up before indexing?" | doc_b_tutorial | chunking explanation section |
| S-04 | "What is the process for turning text into a searchable form?" | doc_b_tutorial | embedding section |
| S-05 | "What slowed the project down the most?" | doc_c_personal | chunk describing env setup problems / dependency issues |

### Designed to test MISSING CONTEXT failures

These queries are ambiguous or use pronouns/references that only resolve within the document.

| ID | Query | Expected failure mode |
|----|-------|-----------------------|
| M-01 | "How does it handle large files?" | "it" unresolved — no explicit large-file handling section |
| M-02 | "What version is being used?" | Multiple versions exist (Python, Ollama, ChromaDB) — ambiguous |
| M-03 | "Did the fix work?" | No prior context — completely ambiguous |
| M-04 | "What is the next step?" | Depends on current phase — could match any phase section |
| M-05 | "Why was that approach chosen?" | "that approach" unresolved — requires conversation history |

### Designed to test RERANKER behavior specifically

These queries test whether the heuristic reranker (`distance_score + size_bonus + continuity_bonus`) improves or degrades rank vs raw cosine.

| ID | Query | What to check |
|----|-------|--------------|
| R-01 | Any query where a short heading chunk ranks 1 by cosine | Does size_penalty (-0.10) correctly demote it? |
| R-02 | Any query where the correct chunk has an adjacent chunk also retrieved | Does continuity_bonus (+0.15) over-promote the wrong adjacent chunk? |
| R-03 | "What are the phases of the project?" | Multiple phase chunks present — does continuity bonus create a cluster? |

---

## Classification Decision Tree

Use this for every failure before assigning a bucket.

```
START
  │
  ▼
Did the corpus contain the correct answer?
  │
  ├─ NO ──────────────────────────────────────────► MISSING_CONTEXT
  │                                                  (information doesn't exist)
  │
  └─ YES
       │
       ▼
     Was the correct answer fully present in the top-1 retrieved chunk?
       │
       ├─ NO: correct chunk not retrieved at all ──► SIMILARITY
       │      (wrong chunks ranked above correct)
       │
       ├─ NO: correct chunk retrieved but incomplete ► CHUNKING
       │      (answer split across chunk boundary)
       │
       └─ YES: correct chunk retrieved, complete
                │
                ▼
              Was the chunk ranked 1, or buried at rank 2+?
                │
                ├─ Rank 2+ despite being correct ──► SIMILARITY
                │                                    (reranker or embedding issue)
                │
                └─ Rank 1, complete, correct
                          │
                          ▼
                        Answer still wrong?
                          │
                          └─ YES ──────────────────► PROMPT/LLM
                                                     (out of scope for this block)
```

---

## System-Specific Failure Patterns to Watch

Based on the codebase and V1 report, these are the most likely recurring patterns in your system. Flag when you see them.

### Pattern: Code block severing (CHUNKING)
The character splitter cuts through triple-backtick fences. Any query about API usage, function calls, or code examples is at risk. The resulting chunk contains an orphaned code fragment that embeds poorly.

Watch for: low similarity scores on technical queries despite the answer existing in the corpus.

### Pattern: Heading isolation (CHUNKING)
A heading appears at the end of chunk N. Its body is in chunk N+1. The heading alone is not retrievable — it carries the topic label but none of the semantic content. Chunk N+1 starts without the heading keyword, so queries using the heading's exact words miss both chunks.

Watch for: queries that use exact section titles returning wrong chunks.

### Pattern: Continuity bonus misfire (SIMILARITY — reranker-specific)
The reranker adds +0.15 per adjacent chunk present in the result set. If two adjacent chunks are both retrieved (common when a topic spans a boundary), both get +0.15. The chunk with the slightly lower cosine score may end up ranked 1 if its neighbor was also retrieved, even if it's the less complete half.

Watch for: rank 1 chunk is the "setup" half of a split explanation, while rank 2 is the "answer" half.

### Pattern: Pronoun queries (MISSING_CONTEXT)
Queries like "How does it work?" or "Why was that changed?" have no resolvable referent. The embedding will match any chunk with plausible surface vocabulary. The failure appears as a confident but topically incorrect retrieval.

Watch for: similarity scores in the 0.25–0.45 range with retrieved content that is thematically adjacent but semantically wrong.

### Pattern: Size penalty over-penalising headings (SIMILARITY — reranker-specific)
The size penalty (-0.10) fires on chunks with < 40 words. Section headings and short introductory paragraphs often fall below this threshold. If the correct answer *is* a short chunk (e.g. "What is the default top_k? → 5"), the size penalty may drop it below a longer but less relevant chunk.

Watch for: short factual queries where the answer is a single sentence or definition.

---

## Running Summary Table

Fill this in as you log failures.

| Query ID | Query (short) | Primary bucket | Secondary bucket | Pattern tag |
|----------|--------------|----------------|-----------------|-------------|
| A-02 | Add docs to ChromaDB | CHUNKING | — | code-block-split |
| A-03 | Distance metrics | CHUNKING | — | table-split |
| A-04 | Persist ChromaDB | CHUNKING | SIMILARITY | code-block-split + embedding-degraded |
| B-03 | Chunk size trade-off | CHUNKING | — | heading-isolation |
| C-04 | Do differently | CHUNKING | SIMILARITY | heading-mutilation + keyword-miss |
| | | | | |
| | | | | |

*(Add rows as you run new queries)*

---

## Final Distribution Report Template

Complete this after running your full evaluation set.

```
═══════════════════════════════════════════════
PKA-AI Retrieval Failure Distribution
Evaluation date:
Queries tested:
Failures identified:
═══════════════════════════════════════════════

Top failure distribution:

  Chunking issues    : ___%  (__/__ failures)
  Similarity issues  : ___%  (__/__ failures)
  Missing context    : ___%  (__/__ failures)

─────────────────────────────────────────────
Top recurring patterns:

  1.
  2.
  3.

─────────────────────────────────────────────
Chunking patterns:

  -

Similarity patterns:

  -

Missing context patterns:

  -

─────────────────────────────────────────────
Reranker-specific observations:

  -

─────────────────────────────────────────────
Retrieval quality floor (must not regress):

  Low-confidence retrievals (score < 0.08): __ / __
  Correct top-1 chunk:                      __ / __

─────────────────────────────────────────────
Primary conclusion:

  "Most failures are ___ problems →
   the highest-priority fix is ___."
═══════════════════════════════════════════════
```

---

## Notes on Methodology

**Why TF-IDF was used as the retrieval proxy in V1**
The V1 report used TF-IDF cosine similarity rather than `nomic-embed-text` embeddings. TF-IDF is keyword-based — it surface-matches tokens rather than encoding meaning. This means the V1 similarity scores understate the quality of the real system (nomic-embed-text will handle paraphrase and synonym queries better) and overstate it for exact-keyword queries. When you run Block 8 with the real embedding pipeline, expect:
- Similarity failures to decrease slightly (semantic model handles paraphrase)
- Missing context failures to become more visible (no keyword fallback)

**Why the reranker adds a new failure surface**
The raw cosine search + heuristic reranker introduces a second ranking stage with its own failure modes. A failure at the reranker level looks like a similarity failure (wrong rank) but has a different fix (reranker weight tuning vs. embedding model change). Log the raw cosine rank alongside the final rerank rank for every failure — this lets you distinguish reranker misfire from embedding weakness.

**Minimum viable sample size**
The 15 V1 queries are enough to identify the dominant failure bucket. If chunking failures represent > 50% of the sample (as the V1 data strongly suggests), that is a statistically stable conclusion at this sample size. You do not need 50+ queries to make an actionable decision about ChunkerV2 priority.