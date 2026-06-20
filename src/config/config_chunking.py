# config/chunking.py
# ─────────────────────────────────────────────────────────────
# Chunking strategy constants.
#
# Rule: never edit values here to "try something".
# Instead, add a new block (CHUNKER_V2_SIZE, etc.) and
# create a corresponding ChunkerV2 class in chunking.py.
# ─────────────────────────────────────────────────────────────

# ── V1 Baseline ──────────────────────────────────────────────
CHUNKER_V1_SIZE = 1000
CHUNKER_V1_OVERLAP = 100
CHUNKER_V1_VERSION = "v1"