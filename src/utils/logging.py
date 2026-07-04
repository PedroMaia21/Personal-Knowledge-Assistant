"""
logging.py — Retrieval observability for PKA-AI.

log_retrieval()      : human-readable display (default, easy to scan)
log_retrieval_json() : full JSON dump (machine-readable, for debugging/tests)
"""

import json


def log_retrieval(query: str, chunks: list) -> None:
    """
    Prints a compact, human-readable retrieval summary.

    Output format:
        ══════════════════════════════════════════
        Query: What is a ChromaDB collection?
        ══════════════════════════════════════════

        #1  notes.md  (chunk 3)
            Distance: 0.462  │  Similarity: 0.538
            ──────────────────────────────────────
            A collection is the core organisational unit in ChromaDB...

        #2  ...

    Args:
        query  : The user's question (logged at the top).
        chunks : List of chunk dicts as returned by semantic_search_reranked().
                 Each dict is expected to have: text, metadata, distance,
                 similarity_score, and optionally id / rerank_scores.
    """
    divider = "═" * 50
    thin    = "─" * 50

    print(f"\n{divider}")
    print(f"Query: {query}")
    print(divider)

    if not chunks:
        print("  (no chunks retrieved)\n")
        return

    for rank, chunk in enumerate(chunks, start=1):
        metadata   = chunk.get("metadata") or {}
        source     = metadata.get("source", "unknown")
        chunk_idx  = metadata.get("chunk_index", "?")
        distance   = chunk.get("distance")
        similarity = chunk.get("similarity_score")
        chunk_id   = chunk.get("id", "")

        # ── header line ───────────────────────────────────────────────────────
        print(f"\n#{rank}  {source}  (chunk {chunk_idx})")
        if chunk_id:
            print(f"    id: {chunk_id}")

        # ── scores ────────────────────────────────────────────────────────────
        score_parts = []
        if distance is not None:
            score_parts.append(f"Distance: {distance:.3f}")
        if similarity is not None:
            score_parts.append(f"Similarity: {similarity:.3f}")

        rerank = chunk.get("rerank_scores") or {}
        if rerank.get("final_score") is not None:
            score_parts.append(f"Rerank: {rerank['final_score']:.3f}")

        if score_parts:
            print("    " + "  │  ".join(score_parts))

        # ── text preview ──────────────────────────────────────────────────────
        print(f"    {thin}")
        text = (chunk.get("text") or "").strip()
        # Show first 300 chars so the log stays scannable
        preview = text[:300] + ("…" if len(text) > 300 else "")
        # Indent each line for visual grouping
        for line in preview.splitlines():
            print(f"    {line}")

    print(f"\n{divider}\n")


def log_retrieval_json(query: str, chunks: list) -> None:
    """
    Prints the full retrieval result as indented JSON.

    Useful for tests, CI output, or copy-pasting into analysis tools.
    Preserves every field returned by semantic_search_reranked().
    """
    payload = {
        "query": query,
        "results": [],
    }

    for rank, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata") or {}
        payload["results"].append({
            "rank":        rank,
            "id":          chunk.get("id"),
            "source":      metadata.get("source", "unknown"),
            "chunk_index": metadata.get("chunk_index"),
            "distance":    chunk.get("distance"),
            "similarity":  chunk.get("similarity_score"),
            "rerank":      chunk.get("rerank_scores"),
            "chunk_text":  chunk.get("text"),
        })

    print(json.dumps(payload, indent=2))

def display_answer(result: dict) -> None:
    """
    Prints the LLM answer followed by a formatted source list.

    Expects the dict returned by answer_question() or RAGAssistant.ask():
        {
            "answer":  str,
            "chunks":  list,
            "sources": list[{"file": str, "chunk_index": int}],
        }

    Example output:
        ══════════════════════════════════════════════════
        Answer
        ══════════════════════════════════════════════════

        ChromaDB stores vectors in a persistent local directory...

        ──────────────────────────────────────────────────
        Sources
        ──────────────────────────────────────────────────
          [1]  doc_a_technical.md  (chunk 0)
          [2]  doc_a_technical.md  (chunk 1)
    """
    divider = "═" * 50
    thin    = "─" * 50

    print(f"\n{divider}")
    print("Answer")
    print(divider)
    print()
    print(result.get("answer", "").strip())
    print()

    sources = result.get("sources") or []
    if sources:
        print(thin)
        print("Sources")
        print(thin)
        for i, src in enumerate(sources, start=1):
            print(f"  [{i}]  {src['file']}  (chunk {src['chunk_index']})")
    else:
        print(thin)
        print("  (no sources retrieved)")

    print()