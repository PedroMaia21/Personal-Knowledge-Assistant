# config/config.py
# ─────────────────────────────────────────────────────────────────────────────
# Runtime constants for PKA-AI.
#
# Rule: never hardcode these values in module files.
# Import from here so there is one place to change them.
# ─────────────────────────────────────────────────────────────────────────────

# ── Retrieval ─────────────────────────────────────────────────────────────────
DEFAULT_TOP_K = 5           # chunks returned per query

# ── Embedding model ───────────────────────────────────────────────────────────
EMBEDDING_MODEL = "nomic-embed-text"

# ── Chat model ────────────────────────────────────────────────────────────────
CHAT_MODEL = "llama3.1"

# ── Vector store ──────────────────────────────────────────────────────────────
CHROMA_DB_PATH = "./chroma_db"
CHROMA_COLLECTION_NAME = "knowledge_base"