# Chunker V1

**Status:** Baseline (frozen)

---

## Parameters

| Parameter   | Value |
|-------------|-------|
| Chunk Size  | 1000 characters |
| Overlap     | 100 characters |
| Algorithm   | Sliding-window character splitter |

---

## Implementation

- Class: `ChunkerV1` in `src/ingestion/chunking.py`
- Constants: `src/config/chunking.py`

---

## Purpose

Initial MVP chunking strategy.
Establishes the retrieval quality baseline before any optimisation experiments.

---

## Metadata emitted per chunk

```json
{
  "source": "notes.md",
  "chunk_index": 42,
  "chunk_length": 1000,
  "chunker_version": "v1"
}
```

---

## Experiment discipline

Any future chunking experiments **must** introduce a new versioned class:

- `ChunkerV2`
- `ChunkerV3`
- etc.

**Never modify V1 parameters.**
Changing them silently invalidates all past retrieval comparisons and makes it
impossible to attribute quality changes to the right variable.

New chunker checklist:
- [ ] New class with its own constants block in `config/chunking.py`
- [ ] `chunker_version` metadata set to the new version string
- [ ] Separate evaluation run recorded before switching production ingestion