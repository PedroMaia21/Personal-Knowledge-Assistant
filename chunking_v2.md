# ChunkerV2 — Design Specification

**Status:** Design (not yet implemented)  
**Supersedes:** ChunkerV1 (frozen baseline)  
**Author:** PKA-AI Project  
**Date:** 2026-06-19  

> This document is a design specification only.  
> No code. No implementation. No experimentation.  
> Implementation and evaluation come after this spec is reviewed and accepted.

---

## Context

ChunkerV1 established a working retrieval baseline using a sliding-window character splitter (1000 chars, 100-char overlap). The V1 evaluation report revealed:

- **81% bad starts** — chunks begin mid-word or mid-sentence
- **75% bad ends** — chunks terminate mid-word or mid-sentence
- **0 / 16 clean chunks** — not a single chunk passes both boundary checks
- **33% context splits** — one in three queries requires two chunks to answer fully
- **Code block fragmentation** — the most destructive failure mode; variable assignments split from their declarations, fenced blocks broken mid-syntax

Retrieval itself is sound: zero low-confidence results across 15 queries. The problem is not *finding* the right chunk — it is *reading* it once found. ChunkerV2 targets that problem.

---

## Design Principles

### Principle 1 — Semantic coherence over fixed size

Chunks should contain complete ideas. A chunk boundary is only valid at a natural linguistic or structural break. Mid-word, mid-sentence, and mid-heading cuts are never acceptable split points.

The 81% bad-start and 75% bad-end rates from the V1 evaluation are the primary quality targets for V2 to eliminate.

### Principle 2 — Retrieval first, generation second

A chunk must satisfy two jobs:

1. **Discoverable** — the embedding captures the topic well enough for semantic search to surface it.
2. **Understandable** — once retrieved, the chunk can be read by the LLM without requiring the adjacent chunk to reconstruct meaning.

ChunkerV1 achieves (1). ChunkerV2 must achieve (2) without sacrificing (1).

### Principle 3 — Preserve document structure

Structural elements carry meaning beyond their individual characters. Splitting through them destroys that meaning disproportionately. The following structures must be treated as units:

- Markdown headings and the content they introduce
- Fenced code blocks
- Tables (all rows belong together)
- Numbered and bulleted lists
- Paragraph blocks

Document A in the evaluation demonstrated the cost of violating this principle: a ChromaDB code example split mid-assignment rendered a chunk completely uninterpretable.

---

## Semantic Split Rules

The core question ChunkerV2 must answer at every candidate boundary:

> *"Is this a valid place to end a chunk?"*

Split locations are evaluated in priority order. The highest-priority valid boundary wins.

### Level 1 — Major document boundaries (best)

Split at major structural divisions:

- `# Heading` (H1)
- `## Section` (H2)
- `### Subsection` (H3)
- Equivalent non-Markdown structural markers (chapter breaks, horizontal rules used as section dividers)

**Rule:** If a section is within the target size range, keep it entirely in one chunk. Do not split a section unless it exceeds the hard size limit.

**Rationale:** A heading and its body form a single semantic unit. A heading isolated from its content, or content separated from its heading, is nearly meaningless in retrieval.

### Level 2 — Paragraph boundaries

Split at blank-line paragraph separators when a Level 1 boundary is not available within range.

**Rule:** A chunk must not terminate in the middle of a paragraph. Advance the cut point forward to the next blank line.

### Level 3 — Sentence boundaries

Split at sentence-ending punctuation when neither Level 1 nor Level 2 boundaries are within range:

- `.` followed by whitespace and an uppercase letter
- `!` followed by whitespace
- `?` followed by whitespace

**Rule:** Never split inside a sentence. A chunk must end on a complete sentence. Advance the cut point to the next valid sentence terminator.

### Level 4 — Hard size limit (last resort)

Apply a hard character/token ceiling only when:

- A single semantic unit (one section, one paragraph) exceeds the absolute size limit
- No internal sentence boundary exists within the limit (pathological case: dense code with no prose)

**Rule:** This level should be rare. If it triggers frequently, the target size parameters need revision.

---

## Protected Structures

The following document structures must be treated as **indivisible units** by the splitter. A cut point that falls inside one of these structures must be moved — either before the structure opens or after it closes.

### Fenced code blocks

```
```language
...code...
```
```

**Rule:** Never split inside a triple-backtick fence. If a cut point lands between the opening and closing fence, advance the boundary to the line after the closing fence.

**Rationale:** This was the most damaging failure in the V1 evaluation. Variable assignments split from their declarations produce syntactically invalid, semantically opaque fragments that provide no signal to the LLM.

---

### Tables

```markdown
| Column A | Column B |
|----------|----------|
| Value    | Value    |
```

**Rule:** Keep all rows of a table together in one chunk. If the full table exceeds the hard size limit, split only between logical row groups — never between a header row and its data rows.

**Rationale:** A table row without its header has no column context. A header without its rows is empty structure.

---

### Lists (numbered and bulleted)

```markdown
1. Step one
2. Step two
3. Step three
```

**Rule:** Do not split a list unless it exceeds the hard size limit. If a list must be split, split only at the boundary between distinct top-level items — never mid-item or mid-sub-list.

**Rationale:** A numbered procedure becomes dangerous when the first half of the steps is in one chunk and the remainder in another. The LLM may generate an incomplete answer with high confidence.

---

### Headings and their following content

```markdown
## Distance Metrics

ChromaDB returns cosine distance...
```

**Rule:** A heading must never appear as the final content of a chunk if the next chunk begins with the body that belongs to it. The heading and at least the first paragraph of its body must co-occur in the same chunk.

**Rationale:** A chunk ending with a bare heading — `## Distance Metrics` — contains no retrievable information. The heading token adds semantic noise without semantic signal.

---

## Chunk Size Philosophy

Exact token/character counts are intentionally deferred to the implementation phase. The following ranges and concepts define the intent.

### Target size

A chunk should contain **one coherent topic** — a section, a concept, a procedure, or a self-contained example.

Typical range: **~500–1500 tokens**

- Large enough to provide the LLM with sufficient context to answer a question without requiring adjacent chunks.
- Small enough that the embedding captures a specific topic rather than a diffuse blend of multiple topics.

### Soft limit

The preferred maximum chunk size. When a semantic unit (a section, a list, a code block) fits within the soft limit, keep it whole. If it exceeds the soft limit but a clean boundary exists shortly beyond it, extending to that boundary is preferred over splitting mid-structure.

### Hard limit

The absolute ceiling. Applied only when a semantic unit is so large that keeping it whole would produce a chunk that degrades embedding quality by covering too broad a topic. At this point, split at the best available Level 3 boundary within the limit.

**Design intent:** The hard limit should trigger infrequently. If analysis during implementation reveals it triggers for >10% of chunks, reconsider the target size parameters.

---

## Overlap Strategy

The V1 evaluation revealed a fundamental problem with the overlap design: the 100-character overlap copies the tail of chunk N into the head of chunk N+1, but the break point itself is still mid-word. The overlap creates duplication without repairing the boundary.

**ChunkerV2 overlap design principle:**

> Overlap exists to preserve contextual continuity between adjacent ideas — not to compensate for bad split points.

Because V2 splits at clean boundaries, overlap serves a different purpose: ensuring that a concept mentioned at the end of one chunk is still available as context at the start of the next.

### Adaptive overlap by structure type

Different document structures benefit from different overlap sizes. The implementation should select overlap based on the type of content at the boundary:

| Structure type | Overlap intent |
|----------------|----------------|
| Paragraph-ending chunks | Small — paragraph breaks are already strong contextual resets |
| Tutorial / long-form prose | Medium — ideas flow across paragraphs; continuity matters |
| Technical reference docs | Larger — definitions and API references are often referenced from nearby sections |
| Code-adjacent chunks | Larger — a code block often requires the prose explanation that precedes or follows it |

Exact overlap values (in tokens or characters) are an implementation decision. The design principle is that overlap size should be proportional to the contextual coupling between adjacent chunks.

---

## Metadata Schema

ChunkerV2 extends the V1 metadata schema to support post-ingestion observability and future automated evaluation.

### V1 metadata (retained)

```json
{
  "source": "notes.md",
  "chunk_index": 3,
  "chunk_length": 1000,
  "chunker_version": "v1"
}
```

### V2 additions

```json
{
  "source": "notes.md",
  "chunk_index": 3,
  "chunk_length": 847,
  "chunker_version": "v2",
  "chunk_type": "section",
  "parent_section": "Distance Metrics",
  "boundary_quality": "clean",
  "overlap_chars": 150
}
```

### Field definitions

| Field | Type | Description |
|-------|------|-------------|
| `chunk_type` | string | Structural type of the chunk: `"section"`, `"paragraph"`, `"code_block"`, `"table"`, `"list"`, `"mixed"` |
| `parent_section` | string | Title of the nearest ancestor heading, or `null` if none |
| `boundary_quality` | string | `"clean"` if both start and end are at valid boundaries; `"bad_start"` / `"bad_end"` / `"bad_both"` if the hard limit forced a non-semantic cut |
| `overlap_chars` | int | Actual overlap applied at the start of this chunk (for debugging and tuning) |

**Rationale:** The V1 evaluation required manual inspection of every chunk to assess boundary quality. Adding `boundary_quality` as a metadata field makes that assessment automatic and enables filtering during post-ingestion auditing without re-running the full evaluation pipeline.

---

## Success Criteria

ChunkerV2 is only considered an improvement if it improves measurable outcomes against the V1 baseline. The following criteria must be evaluated using the same 3 test documents and 15 queries used in the V1 evaluation report.

### Criterion 1 — Boundary quality (readability)

| Metric | V1 baseline | V2 target |
|--------|------------|-----------|
| Bad starts | 81% (13/16) | < 10% |
| Bad ends | 75% (12/16) | < 10% |
| Clean chunks (both OK) | 0% (0/16) | > 90% |

### Criterion 2 — Context splits (completeness)

| Metric | V1 baseline | V2 target |
|--------|------------|-----------|
| Queries requiring 2+ chunks | 33% (5/15) | < 10% |
| Code-query context splits | 60% (3/5) | < 15% |

### Criterion 3 — Retrieval quality (must not regress)

| Metric | V1 baseline | V2 target |
|--------|------------|-----------|
| Low-confidence retrievals | 0 / 15 | 0 / 15 |
| Correct top-1 chunk | ≥ 4/5 per document | ≥ 4/5 per document |

**Critical constraint:** Improving chunk readability must not degrade retrieval performance. If V2 produces cleaner chunks but the correct chunk drops from rank 1 to rank 2 or lower, that is a regression. Retrieval quality is the floor; boundary quality is the ceiling to improve toward.

### Criterion 4 — Metadata completeness

All chunks must emit the full V2 metadata schema. `boundary_quality: "bad_start"` or `"bad_end"` should appear on fewer than 10% of chunks. If it appears more frequently, the split logic has a defect.

---

## Experiment Discipline

Per project convention (established in `chunking_v1.md`):

- V1 parameters must not be modified
- ChunkerV2 is a new class: `ChunkerV2` in `src/ingestion/chunking.py`
- V2 constants go in a new block in `src/config/config_chunking.py`: `CHUNKER_V2_*`
- `chunker_version` metadata must be set to `"v2"`
- A full evaluation run must be recorded before switching production ingestion to V2
- The 15 evaluation queries from the V1 report should be run unchanged against V2 to enable direct comparison

### New chunker checklist

- [ ] New `ChunkerV2` class with its own constants block (`CHUNKER_V2_*`) in `config/config_chunking.py`
- [ ] `chunker_version` metadata set to `"v2"`
- [ ] Full V2 metadata schema emitted on every chunk
- [ ] Evaluation run completed against all 3 test documents
- [ ] Boundary quality, context split rate, and retrieval metrics recorded
- [ ] Results compared against V1 baseline before any production switch

---

## Open Questions for Implementation

The following decisions are intentionally deferred. They require empirical testing and should be resolved during the implementation phase.

1. **Exact soft and hard size limits** — What token/character counts work best for the target document types (technical reference, tutorial, personal notes)? Suggest starting with soft=1200 chars, hard=2000 chars and adjusting based on chunk count distribution.

2. **Sentence boundary detection method** — Simple regex (`. ` + uppercase) vs. a lightweight NLP tokenizer (e.g. `nltk.sent_tokenize`). Regex is faster and has no dependency; NLP is more robust for abbreviations and edge cases.

3. **Heading attachment threshold** — How many characters of body content must accompany a heading before it is allowed to stand as a chunk? Suggest a minimum of 200 chars, but this needs validation.

4. **Adaptive overlap values** — What specific overlap sizes (in chars) should each structure type use? These should be determined empirically by inspecting boundary continuity in the test documents.

5. **List split granularity** — For lists exceeding the hard limit, should the split always occur at the top-level item boundary, or is splitting between sub-items acceptable for deeply nested lists?

---

## Summary

ChunkerV2 addresses the single largest quality gap identified in the V1 evaluation: **chunks are retrievable but not readable**. By splitting at semantic boundaries (headings, paragraphs, sentences) in priority order, protecting structural elements (code blocks, tables, lists) from fragmentation, and emitting richer metadata, V2 aims to produce chunks that the LLM can use without needing to reconstruct context from adjacent chunks.

The retrieval pipeline (embeddings + ChromaDB + cosine similarity) is sound and must be preserved. V2 improves the content quality delivered to the LLM — not the search mechanism that finds it.