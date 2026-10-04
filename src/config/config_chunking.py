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

# ── V2 Structure-aware ───────────────────────────────────────
# Starting values from chunking_v2.md (Open Question 1).
# Soft limit: preferred maximum; units are packed up to this size.
# Hard limit: absolute ceiling; no chunk ever exceeds it.
CHUNKER_V2_SOFT_LIMIT = 1200
CHUNKER_V2_HARD_LIMIT = 2000
CHUNKER_V2_VERSION = "v2"
