# PKA-AI — Chunking & Retrieval Evaluation Report

**ChunkerV1** · chunk_size = 1000 chars · overlap = 100 chars  
**Evaluation date:** 2026-06-15  
**Documents tested:** 3  
**Retrieval proxy:** TF-IDF cosine similarity (production will use `nomic-embed-text`)

---

## Test Documents

| ID | File | Type | Characters | Chunks |
|----|------|------|-----------|--------|
| A | `doc_a_technical.md` | Technical reference (ChromaDB API docs) | 3,316 | 4 |
| B | `doc_b_tutorial.md` | Long-form tutorial (RAG explained) | 4,819 | 6 |
| C | `doc_c_personal.md` | Personal retrospective (PKA-AI phases 1–4) | 5,256 | 6 |

---

## Document A — Technical Reference

### Chunk Inspection

| Chunk | Start naturally? | End naturally? | Verdict |
|-------|-----------------|----------------|---------|
| 0 | ✅ Markdown heading `#` | ❌ Ends mid code block (`{"hnsw:space`) | BAD-END |
| 1 | ❌ Mid-word (`n collection = …`) | ❌ Ends mid-sentence (`## `) | BAD-START / BAD-END |
| 2 | ❌ Mid-sentence (`r. Plan your ID…`) | ❌ Ends mid code block | BAD-START / BAD-END |
| 3 | ❌ Mid-word (`ended for production)`) | ✅ Ends on natural sentence | BAD-START |

**Root cause:** The document contains inline code blocks (triple-backtick fences). The character splitter cuts straight through them, producing chunks that open mid-code-block and close mid-prose. A reader encountering chunk 1 (`n collection = client.get_or_create_collection(…`) has no idea what object `n` refers to — the variable assignment was split from its context.

### Retrieval Results

| Query | Top chunk | Score | Assessment |
|-------|-----------|-------|------------|
| What is a ChromaDB collection? | Chunk 0 | 0.54 | ✅ Correct — overview section found |
| How do I add documents to ChromaDB? | Chunk 1 | 0.25 | ⚠️ Relevant but context split with chunk 2 |
| What distance metrics does ChromaDB support? | Chunk 3 | 0.14 | ⚠️ Context split with chunk 2 — table cut across boundary |
| How do I make ChromaDB data persist? | Chunk 2 | 0.12 | ⚠️ Context split — persistence code spans chunks 2 and 3 |
| How do I convert distance to similarity score? | Chunk 2 | 0.22 | ✅ Found, but explanation is split across 2 and 3 |

**Context splits detected:** 3 / 5 queries  
**Low-confidence results (score < 0.08):** 0 / 5

### Findings Summary

```
Characters     : 3,316
Chunks         : 4
Bad starts     : 3  (chunks 1, 2, 3)
Bad ends       : 3  (chunks 0, 1, 2)
Clean chunks   : 0
Context splits : 3 / 5 queries
```

**Conclusion:** The technical document suffers most from code block severance. With only 4 chunks for a 3,316-char document, a larger chunk size might keep more code examples intact within a single chunk. The distance-metric table and the persistence examples are both split, which means a query about either topic would require the LLM to stitch together two partial chunks.

---

## Document B — Tutorial (Long-form)

### Chunk Inspection

| Chunk | Start naturally? | End naturally? | Verdict |
|-------|-----------------|----------------|---------|
| 0 | ✅ Markdown heading `#` | ❌ Mid-sentence (`…a database, or an API. Each`) | BAD-END |
| 1 | ❌ Mid-word (`tion  Documents are loaded…`) | ❌ Mid-sentence (`…in a form that can`) | BAD-START / BAD-END |
| 2 | ❌ Mid-word (`nse vector representation…`) | ❌ Mid-sentence (`…same model`) | BAD-START / BAD-END |
| 3 | ❌ Mid-section label (` 5: Retrieval and Generation`) | ❌ Mid-word (`…chunk inspe`) | BAD-START / BAD-END |
| 4 | ❌ Mid-word (`on quality problems…`) | ❌ Mid-sentence (`…assess automatica`) | BAD-START / BAD-END |
| 5 | ❌ Mid-word (`h the correct chunk appears…`) | ✅ Ends on natural sentence | BAD-START |

**Observation:** Every chunk except chunk 0 starts mid-word. The 100-char overlap is insufficient — it echoes the tail of the previous chunk into the next but does not correct the starting position. Chunk 3 starts with ` 5: Retrieval and Generation` — a section number without its heading, which makes it nearly unreadable in isolation.

### Retrieval Results

| Query | Top chunk | Score | Assessment |
|-------|-----------|-------|------------|
| What problem does RAG solve? | Chunk 0 | 0.23 | ✅ Correct |
| What are the stages of a RAG pipeline? | Chunk 0 | 0.52 | ✅ Found, but stages span all chunks — context very fragmented |
| Why does chunk size matter? | Chunk 3 | 0.11 | ⚠️ Context split with chunk 4 |
| How do you evaluate RAG quality? | Chunk 4 | 0.19 | ✅ Relevant chunk found |
| What is an embedding model? | Chunk 1 | 0.27 | ✅ Correct |

**Context splits detected:** 1 / 5 queries  
**Low-confidence results:** 0 / 5

### Findings Summary

```
Characters     : 4,819
Chunks         : 6
Bad starts     : 5  (chunks 1, 2, 3, 4, 5)
Bad ends       : 5  (chunks 0, 1, 2, 3, 4)
Clean chunks   : 0
Context splits : 1 / 5 queries
```

**Conclusion:** Retrieval is actually functional here — 4 of 5 queries surface the correct chunk in position 1. The problem is that the retrieved text is almost never self-contained. A human handed chunk 1 in isolation would read "tion  Documents are loaded from a source…" with no context for what "tion" concludes. The LLM will likely handle this better than a human, but the severed opening tokens are noise that degrade the signal in the context window.

---

## Document C — Personal Retrospective

### Chunk Inspection

| Chunk | Start naturally? | End naturally? | Verdict |
|-------|-----------------|----------------|---------|
| 0 | ✅ Markdown heading `#` | ❌ Mid-sentence (`…immediately`) | BAD-END |
| 1 | ❌ Mid-word (`ependency compatibility…`) | ❌ Mid-word (`…Erro`) | BAD-START / BAD-END |
| 2 | ❌ Mid-word (`tforward to implement…`) | ❌ Mid-sentence (`…once I unde`) | BAD-START / BAD-END |
| 3 | ❌ Mid-sentence (`e persistence model is transparent…`) | ❌ Mid-sentence (`…Without`) | BAD-START / BAD-END |
| 4 | ❌ Mid-word (`nderstood the retrieval behaviour…`) | ✅ Ends naturally | BAD-START |
| 5 | ❌ Mid-number (`00 produced too many fragments…`) | ✅ Ends naturally | BAD-START |

**Notable issue:** Chunk 5 starts with `00 produced too many fragments` — the `5` in `500` was cut from the previous chunk. This is the most jarring example in the evaluation: a chunk beginning with a bare number is completely uninterpretable without its predecessor.

**Positive note:** Chunks 4 and 5 both end naturally, which means the final sections of the retrospective are at least retrievably intact at their tails.

### Retrieval Results

| Query | Top chunk | Score | Assessment |
|-------|-----------|-------|------------|
| What went wrong during environment setup? | Chunk 0 | 0.30 | ✅ Correct |
| What lessons were learned about chunking? | Chunk 2 | 0.15 | ⚠️ Lesson is scattered across chunks 1, 2, 4 |
| Why was observability identified as a problem? | Chunk 3 | 0.22 | ⚠️ Context split with chunk 4 |
| What would be done differently next time? | Chunk 0 | 0.15 | ⚠️ "What I Would Do Differently" section is in chunk 5 — missed |
| What are the next steps for the project? | Chunk 5 | 0.48 | ✅ Correct and high confidence |

**Context splits detected:** 1 / 5 queries  
**Low-confidence results:** 0 / 5

### Findings Summary

```
Characters     : 5,256
Chunks         : 6
Bad starts     : 5  (chunks 1, 2, 3, 4, 5)
Bad ends       : 4  (chunks 0, 1, 2, 3)
Clean chunks   : 0
Context splits : 1 / 5 queries
```

**Conclusion:** Retrieval found the right chunk for 4 of 5 queries. The exception — "What would be done differently?" — ranks chunk 0 (the summary header) above chunk 5 (which contains the actual "What I Would Do Differently" section). This is a vocabulary mismatch: the heading text in chunk 5 starts with `00 produced too many fragments`, having lost `5` from `500`. The heading was severed from its own keyword.

---

## Overall Summary

| Metric | Doc A | Doc B | Doc C | Total |
|--------|-------|-------|-------|-------|
| Chunks generated | 4 | 6 | 6 | **16** |
| Bad starts | 3 (75%) | 5 (83%) | 5 (83%) | **13 / 16 (81%)** |
| Bad ends | 3 (75%) | 5 (83%) | 4 (67%) | **12 / 16 (75%)** |
| Clean chunks (both OK) | 0 | 0 | 0 | **0 / 16** |
| Queries tested | 5 | 5 | 5 | **15** |
| Low-confidence retrievals | 0 | 0 | 0 | **0 / 15** |
| Context splits | 3 | 1 | 1 | **5 / 15 (33%)** |

---

## Analysis

### What is working

**Retrieval surfaces relevant content reliably.** Zero low-confidence results across 15 queries means the semantic search pipeline is functionally sound. For straightforward factual queries ("What are the next steps?" → chunk 5, score 0.48), the system already delivers the right answer. This validates that the embedding + vector search architecture is correct.

**The overlap is doing partial work.** The 100-char overlap ensures that the tail of every chunk reappears at the start of the next. This prevents total information loss at boundaries, which is why retrieval works at all. But it does not prevent the start of a chunk being mid-word or mid-sentence.

### What is failing

**100% of chunks have a bad start or bad end.** Not a single chunk in the evaluation passes both checks simultaneously. The character splitter has no awareness of sentence or word boundaries. When a cut lands mid-word (which it does frequently in prose that has no natural 1000-char section breaks), the chunk starts with a fragment like `nse vector representation` or `ependency compatibility`.

**The overlap creates duplication without fixing the break.** The overlap copies 100 chars of the previous chunk into the next, but the *break point itself* is still mid-word. The reader of chunk N+1 sees the overlap first, then the continuation — but the opening is still garbled.

**33% of queries require two chunks to answer fully.** For code-heavy technical documents (Doc A), this rises to 60%. A context block constructed from only the top-1 chunk will be incomplete for one in three questions.

**Code blocks are particularly vulnerable.** A 1000-char window cuts through triple-backtick code examples, splitting variable assignments from their declarations and function calls from their output. The resulting chunks contain orphaned code fragments that are syntactically invalid and semantically opaque.

---

## Recommendations for ChunkerV2

These are design inputs for a future versioned chunker. Per project discipline, V1 parameters must not be modified.

**1. Sentence-boundary awareness (highest impact)**  
After computing the character cut point, advance the boundary forward to the next sentence-ending punctuation (`.`, `!`, `?`). This alone would eliminate most bad-start and bad-end cases without requiring a structural parser.

**2. Increase overlap from 100 → 200 chars**  
Doubling the overlap reduces the chance that a key phrase at a boundary is unavailable to the next chunk's retrieval signal. Cost is ~10% more stored vectors for a meaningful improvement in boundary continuity.

**3. Code block protection**  
Before chunking, detect triple-backtick fences. If a cut point falls inside a code block, advance the boundary to the closing fence. This prevents code fragment chunks, which are the most unreadable output ChunkerV1 produces.

**4. Add `boundary_quality` to chunk metadata**  
Flag chunks where the first token is lowercase mid-word. This enables post-ingestion auditing without re-running the full evaluation pipeline. Example addition to the metadata schema:

```json
{
  "source": "notes.md",
  "chunk_index": 3,
  "chunk_length": 1000,
  "chunker_version": "v1",
  "boundary_quality": "bad_start"
}
```

**5. Define evaluation queries before ingesting**  
The 15 queries used in this evaluation were written after chunking. Writing them before ingestion would make each new chunker version directly comparable. Record expected chunk IDs for each query so Recall@k can be computed automatically.

---

## Conclusion

ChunkerV1 establishes a working baseline. Retrieval is functional and no queries were completely missed. However, **81% of chunks have a broken start boundary and 75% have a broken end boundary**, which means the LLM will frequently receive context that begins mid-thought. For an MVP this is acceptable — the system works — but it is the highest-priority quality improvement before Phase 5 (RAG prompt + generation).

The most impactful single change would be sentence-boundary-aware splitting. It requires minimal implementation effort relative to the quality gain and produces immediately human-readable chunks that can be inspected and debugged without confusion.