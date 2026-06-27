"""
reranker.py — Heuristic reranker for PKA-AI.

Sits between semantic_search() and the caller.
Takes raw ChromaDB results and re-sorts them using three lightweight signals:

    final_score = distance_score + size_bonus + continuity_bonus

No external models. No ML. Pure signal engineering.

Signals
-------
1. Distance score      1 / (1 + distance)         — higher is closer match
2. Size penalty        -0.10 if word_count < 40    — penalises fragment chunks
3. Continuity bonus    +0.15 per adjacent neighbour — rewards neighbouring chunks
                       already present in the result set
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Tuneable constants ────────────────────────────────────────────────────────

MIN_WORDS: int = 40          # chunks shorter than this are penalised
SIZE_PENALTY: float = -0.10  # applied when word_count < MIN_WORDS

CONTINUITY_BONUS: float = 0.15   # applied per adjacent neighbour in results
ADJACENCY_GAP: int = 1           # chunk_index difference that counts as adjacent


# ── Core scoring ─────────────────────────────────────────────────────────────

def _distance_score(distance: float) -> float:
    """
    Converts a raw ChromaDB cosine distance into a positive score.

    distance = 0.0  →  score = 1.0  (perfect match)
    distance = 1.0  →  score = 0.5  (orthogonal)
    distance = 2.0  →  score = 0.33 (opposite)

    Formula: 1 / (1 + distance)
    """
    return 1.0 / (1.0 + distance)


def _size_bonus(text: str) -> float:
    """
    Returns 0.0 for normal-length chunks, SIZE_PENALTY for fragments.

    Very short chunks (headings, isolated list items, single sentences)
    rarely answer questions well on their own.
    """
    word_count = len(text.split())
    if word_count < MIN_WORDS:
        return SIZE_PENALTY
    return 0.0


def _continuity_bonus(chunk: dict[str, Any], others: list[dict[str, Any]]) -> float:
    """
    Rewards a chunk when an adjacent chunk from the same document also
    appears in the result set.

    Adjacency is defined as: same source document AND
    abs(chunk_index_A - chunk_index_B) <= ADJACENCY_GAP.

    Each adjacent neighbour found in *others* contributes +CONTINUITY_BONUS.
    A chunk with two neighbours present receives 2 × CONTINUITY_BONUS.

    Args:
        chunk  : The chunk being scored.
        others : All other chunks in the result set (excluding *chunk* itself).
    """
    meta = chunk.get("metadata", {})
    source = meta.get("source")
    index = meta.get("chunk_index")

    if source is None or index is None:
        return 0.0

    bonus = 0.0
    for other in others:
        other_meta = other.get("metadata", {})
        if other_meta.get("source") != source:
            continue
        other_index = other_meta.get("chunk_index")
        if other_index is None:
            continue
        if abs(index - other_index) <= ADJACENCY_GAP:
            bonus += CONTINUITY_BONUS

    return bonus


# ── Score computation ─────────────────────────────────────────────────────────

def compute_score(chunk: dict[str, Any], others: list[dict[str, Any]]) -> dict[str, float]:
    """
    Computes the composite reranking score for a single chunk.

    Args:
        chunk  : A chunk dict as returned by semantic_search().
        others : All other chunks in the result set.

    Returns:
        A dict with individual signal values and the final composite score:
            {
                "distance_score":   float,
                "size_bonus":       float,
                "continuity_bonus": float,
                "final_score":      float,
            }
    """
    ds = _distance_score(chunk.get("distance", 1.0))
    sb = _size_bonus(chunk.get("text", ""))
    cb = _continuity_bonus(chunk, others)

    return {
        "distance_score": ds,
        "size_bonus": sb,
        "continuity_bonus": cb,
        "final_score": ds + sb + cb,
    }


# ── Public API ────────────────────────────────────────────────────────────────

def rerank(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Re-sorts *chunks* by composite heuristic score (descending).

    Each chunk dict is annotated with a "rerank_scores" key containing
    the breakdown produced by compute_score(), which can be logged or
    printed for debugging.

    Args:
        chunks : Raw chunk dicts from semantic_search().

    Returns:
        The same chunks, sorted by final_score descending.
        The original "distance" and "similarity_score" fields are preserved.
    """
    if not chunks:
        return chunks

    scored: list[dict[str, Any]] = []

    for chunk in chunks:
        others = [c for c in chunks if c is not chunk]
        scores = compute_score(chunk, others)

        annotated = dict(chunk)          # shallow copy — keeps all original fields
        annotated["rerank_scores"] = scores
        scored.append(annotated)

    scored.sort(key=lambda c: c["rerank_scores"]["final_score"], reverse=True)

    return scored


def format_rerank_debug(chunk: dict[str, Any]) -> str:
    """
    Returns a human-readable score breakdown for a single chunk.

    Example output:
        [doc_notes.md | chunk 7]
          Distance score : 0.838
          Size bonus     : +0.000
          Continuity     : +0.150
          ─────────────────────
          Final score    : 0.988

    Useful for printing during development or adding to log_retrieval().
    """
    scores = chunk.get("rerank_scores", {})
    meta = chunk.get("metadata", {})
    source = meta.get("source", "unknown")
    idx = meta.get("chunk_index", "?")

    lines = [
        f"[{source} | chunk {idx}]",
        f"  Distance score : {scores.get('distance_score', 0):.3f}",
        f"  Size bonus     : {scores.get('size_bonus', 0):+.3f}",
        f"  Continuity     : {scores.get('continuity_bonus', 0):+.3f}",
        f"  {'─' * 21}",
        f"  Final score    : {scores.get('final_score', 0):.3f}",
    ]

    return "\n".join(lines)