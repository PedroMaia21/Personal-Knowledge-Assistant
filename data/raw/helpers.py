"""
helpers.py — shared utility functions for PKA-AI.

Keep conversion/normalisation logic here so no scattered
`score = 1 - distance` expressions appear elsewhere in the codebase.
"""


def normalize_similarity(distance: float) -> float:
    """
    Converts a ChromaDB cosine distance into a [0.0, 1.0] similarity score.

    ChromaDB returns cosine *distance* in the range [0, 2]:
        0.0 → identical vectors  (perfect match)
        1.0 → orthogonal vectors (no relation)
        2.0 → opposite vectors   (anti-correlated)

    This function maps that to an intuitive similarity score:
        1.0 → perfect match
        0.5 → orthogonal
        0.0 → opposite / clamped floor

    Args:
        distance: Raw cosine distance value returned by ChromaDB.

    Returns:
        Normalised similarity score in [0.0, 1.0].

    Usage:
        score = normalize_similarity(chunk["distance"])
        # Never write:  score = 1 - distance   ← scattered conversion
    """
    return max(0.0, min(1.0, 1.0 - distance))