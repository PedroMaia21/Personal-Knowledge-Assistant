"""
app.py — Streamlit demo UI for PKA-AI.

Responsibility: orchestrate user interaction only.
No retrieval logic, no prompt building, no LLM calls live here —
those all stay in the existing backend modules:

    app.py
        ↓
    src/assistant/rag_assistant.py   (RAGAssistant)
        ↓
    src/retrieval/search.py          (semantic_search_reranked)
        ↓
    src/vectorstore/chroma_store.py  (ChromaDB)
        ↓
    src/models/embedding.py          (nomic-embed-text via Ollama)

Run with:
    streamlit run app.py
"""

import tempfile
from pathlib import Path

import streamlit as st

from src.ingestion.loader import load_file
from src.ingestion.chunking import ChunkerV1
from src.core.embedding_client import EmbeddingClient
from src.core.chroma_client import ChromaClient
from src.vectorstore.chroma_store import store_chunks
from src.assistant.memory import ConversationMemory
from src.assistant.rag_assistant import RAGAssistant
from src.assistant.adapters import SearchRetriever, PromptBuilder, OllamaLLMClient

# ── Single shared embedding client for the whole app process ───────────────
embedding_client = EmbeddingClient()
chroma_client = ChromaClient()

# ── Backend wiring (Step "Before Coding") ──────────────────────────────────
# ingest_document(path)  → chunk → embed → store
# assistant.ask(question) → RAGAssistant, built from existing adapters

def ingest_document(
    path: Path,
    embedding_client: EmbeddingClient,
    chroma_client: ChromaClient,
) -> int:
    """Reads, chunks, embeds, and stores a single document. Returns chunk count."""
    text = load_file(path)

    chunker = ChunkerV1()
    chunks = chunker.chunk_document(text, source=path.name)

    if not chunks:
        return 0

    embedded = embedding_client.generate_many([c["text"] for c in chunks])
    vectors = [e["embedding"] for e in embedded]

    store_chunks(chunks, vectors, chroma_client=chroma_client)
    return len(chunks)

@st.cache_resource
def get_assistant() -> RAGAssistant:
    """Built once per Streamlit session process; shares both module-level clients."""
    return RAGAssistant(
        retriever=SearchRetriever(
            embedding_client=embedding_client,
            chroma_client=chroma_client,
        ),
        prompt_builder=PromptBuilder(),
        llm_client=OllamaLLMClient(),
        memory=ConversationMemory(),
    )
# ── Session state ───────────────────────────────────────────────────────────

if "ingested_files" not in st.session_state:
    st.session_state.ingested_files = set()   # filenames already ingested
if "last_result" not in st.session_state:
    st.session_state.last_result = None       # last {"answer","sources",...}
if "qa_log" not in st.session_state:
    st.session_state.qa_log = []              # list of (question, answer)


# ── Layout ───────────────────────────────────────────────────────────────────

st.title("Personal Knowledge Assistant")

st.header("Upload document")
uploaded_file = st.file_uploader("Choose a file", type=["txt", "md"])

if uploaded_file is not None:
    if uploaded_file.name in st.session_state.ingested_files:
        st.info(f"'{uploaded_file.name}' was already ingested this session.")
    else:
        with st.spinner(f"Processing '{uploaded_file.name}'..."):
            suffix = Path(uploaded_file.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = Path(tmp.name)

            try:
                num_chunks = ingest_document(tmp_path)
            finally:
                tmp_path.unlink(missing_ok=True)

        st.session_state.ingested_files.add(uploaded_file.name)
        st.success(f"'{uploaded_file.name}' ingested — {num_chunks} chunks stored.")

st.divider()

st.header("Question")
question = st.text_input("Ask something about your documents", key="question_input")
ask_clicked = st.button("Ask")

if ask_clicked and question.strip():
    assistant = get_assistant()
    with st.spinner("Thinking..."):
        result = assistant.ask(question)

    st.session_state.last_result = result
    st.session_state.qa_log.append((question, result["answer"]))

st.divider()

st.header("Answer")
if st.session_state.last_result:
    st.write(st.session_state.last_result["answer"])

    st.subheader("Sources")
    sources = st.session_state.last_result.get("sources") or []
    if sources:
        for src in sources:
            st.write(f"- {src['file']} (chunk {src['chunk_index']})")
    else:
        st.write("(no sources retrieved)")
else:
    st.write("_No question asked yet._")

# ── Conversation log (optional, useful for demoing multi-turn memory) ──────
if st.session_state.qa_log:
    with st.expander("Conversation history (this session)"):
        for q, a in st.session_state.qa_log:
            st.markdown(f"**You:** {q}")
            st.markdown(f"**Assistant:** {a}")
            st.markdown("---")