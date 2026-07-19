# Personal-Knowledge-Assistant

## Project Overview
PKA-AI is a personal knowledge assistant that ingest documents,
creates embeddings, stores them in a vector database,
and retrieves relevant context for LLM-based question answering.

---

## Project Goal

Build a small local AI assistant that can:

- ingest your notes/documents
- search semantic meaning
- answer questions about your content
- summarize information
- extract TODOs/action items

All running locally with a 0€ budget.

---

## Architecture

### Core Stack

#### LLM Runtime

- Ollama

Reason:
- free
- local
- beginner-friendly
- excellent ecosystem

#### Models

**Chat Model**
- `llama3.1:8b`

**Embeding Model**
- `nomic-embed-text`

---

#### Backend

- FastAPI

Reason:
- modern
- simple
- production-relevant
- excellent with Python AI tooling

---

#### Vector Database

- ChromaDB

Reason:
- local
- extremely easy setup
- perfect for beginners

---

#### Frontend

Initially:
- terminal/CLI

Later:
- Streamlit

---

### Overall System Design

This reflects the pipeline as it runs today — not an aspirational future state.

```
                Documents
                     │
                     ▼
             Document Loader
                     │
                     ▼
               Text Chunking
                     │
                     ▼
           Embedding Client
                     │
                     ▼
                 ChromaDB
                     │
             Top-k Retrieval
                     │
              Heuristic Rerank
                     │
             Conversation Memory
                     │
                     ▼
             Prompt Construction
                     │
                     ▼
                 Ollama LLM
                     │
                     ▼
                  Response
```

Every question — from the CLI, the Streamlit app, or a script — enters and
exits through exactly one orchestrator: `RAGAssistant.ask()`. Nothing calls
retrieval, prompting, or the LLM directly outside of that class and the
adapters it's composed from.

**Conversation Memory is an implemented pipeline stage, not a planned one.**
It is injected into `RAGAssistant`, read on every `ask()` call to resolve
follow-up references ("it", "that"), and updated after each answer.

---

### Folder Structure
```
Personal-Knowledge-Assistant/
│
├── src/
|   ├── assistant/
│   │   ├── adapters.py
│   │   ├── rag_assistant.py
│   │   └── memory.py
│   ├── config/
│   │   ├── config.py
│   │   ├── prompts.py
│   │   └── config_chunking.py
│   ├── ingestion/
│   │   ├── chunking.py
│   │   └── loader.py
│   ├── models/
│   │   ├── embedding.py
│   │   └── llm.py
│   ├── retrieval/
│   │   └── search.py
│   ├── utils/
│   │   ├── helpers.py
│   │   ├── logging.py
│   │   └── reranker.py
|   ├── vectorstore/
│   │   └── chroma_store.py
│   └── core/
│       ├── embedding_client.py
│       └── chroma_client.py       
│
├── data/
│   ├── raw/
│   │   └── notes.md
│   └── evaluation/
|       ├── eval_queries.json
│       ├── distance_findings.md
│       └── chunking_v1_eval_report.md
│
├── scripts/
│   ├── chat_cli.py
│   ├── embedding_distance_analysis.py
│   ├── evaluate_retrieval.py
│   ├── ingest_data.py
│   ├── inspect_retrieval.py
│   ├── investigate_distances.py
│   ├── main.py
│   └── rag_assistant_ask.py
│
├── tests/
│   ├── integration/
│   │   ├── test_semantic_search.py
│   │   └── test_prompt_grounding.py
│   └── unit/
│       ├── test_embeddings.py
│       └── test_vector_store.py
│
├── app.py
├── requirements.txt
├── project_mvp.md
├── README.md
├── .gitignore
└── .env
```

---

### Versions during development

- **Python**: 3.14.2
- **Pip**: 25.3
- **Ollama**: 0.24.0
---

## Architecture Decisions

These are invariants, not conventions — code review should reject anything
that violates them.

- **All queries pass through `RAGAssistant`.** Retrieval, prompt
  construction, memory injection, and the LLM call are only ever invoked
  from inside `RAGAssistant.ask()`. The CLI, the Streamlit app, and any
  script are callers of that method, never independent implementations of
  the pipeline.
- **Embeddings are generated exclusively through `EmbeddingClient`.**
  No module calls `ollama.embeddings(...)` directly. The old
  `src/models/embedding.py` functions have been removed in favor of this.
- **ChromaDB is accessed only through `ChromaClient`.** No module
  constructs `chromadb.PersistentClient(...)` or calls
  `get_or_create_collection()` on its own — collection name, DB path, and
  the `hnsw:space` metric are configured in exactly one place.
- **Chunking parameters are versioned, never mutated.** `ChunkerV1`'s
  constants are frozen; new strategies are added as `ChunkerV2`, `V3`, etc.,
  each with its own constants block, so retrieval-quality comparisons stay
  attributable to the right variable.
- **Conversation memory and retrieved chunks are separate concerns.**
  `ConversationMemory` only ever stores `{question, answer}` pairs. It knows
  nothing about chunks, sources, or embeddings, and is never merged into the
  context block sent to the LLM.
- **`src/retrieval/query.py` has been removed.** It previously duplicated
  the retrieve → prompt → LLM flow that `RAGAssistant` now owns exclusively.
  No file in this project imports from it.

---

## Scope Definition

### MVP Scope

For version 1, the assistant only needs to:

1.  read .txt and .md
2. split text into chunks
3. generate embeddings
4. store embeddings
5. answer questions

---

## Roadmap

### Phase 1 - Environment Setup

**Goal**
Get local AI Working

- [x] Install Python + Create Project
    - [x] Project Folder
    - [x] virtual environment
    - [x] git repository
- [x] Install Ollama
    - [x] Ollama Installed
    - [x] local model running
    - Test:
```bash
ollama run llama3.1:8b
```
```bash
ollama run nomic-embed-text
```
- [x] Create basic FastAPI App
    - Example:
```python
@app.get("/")
def root():
    return {"status": "running"}
```

---

### Phase 2 - Basic AI Interaction

**Goal**
Talk to the local model

- [x] Install Ollama Python Client
    - Instalation:
```bash
pip install ollama
```
- [x] Create simple chat script
    - CLI Example:
```
You: summarize productivity systems
AI: ...
```

---

### Phase 3 - Document Processing

**Goal**
Load Files

- [x] Create Document Loader
    - [x] read `.txt`
    - [x] read `.md`
    - [x] iterate folder contents
- [x] Implement Text Chunking
    - [x] Split large text into chunks
    - Strategy:
        - 500–1000 characters
        - overlap of 100

---

### Phase 4 - Embeddings + Vector Search

**Goal**
Semantic Search

- [x] Install ChromaDB
```bash
pip install chromadb
```
- [x] Generate Embeddings
    - [x] Generate embeddings for chunks
```python
nomic-embed-text
```
- [x] Store Embeddings in ChromaDB
- [x] Implement Semantic Search
    - Input: `"What were the productivity review conclusions?"`
    - Outputs:
        - top relevant chunks

---

### Phase 5 - Build the AI Assistant

**Goal**
Combine retrieval + Generation

- [x] Create Retrieval Prompt
**Prompt Structure:**
```
Use ONLY the provided context.

Context:
...

Question:
...
```
- [x] Implement RAG pipeline
**Flow:**
```
Question
→ retrieve chunks
→ build prompt
→ ask LLM
→ answer
```

---

### Phase 6 - Quality Improvements

**Implemented**

- [x] Source references
    - Example: `Source: weekly_review_may.txt`
- [x] Conversation memory
    - Stores the last 5 question/answer exchanges (`MAX_HISTORY`), in-memory only, per session — not persisted to disk, not embedded, not summarized.
    - Resolves follow-up references ("it", "that") without treating history as a source of facts.
- [x] Heuristic reranker
    - Re-scores raw ChromaDB results using distance + a fragment-size penalty + an adjacency/continuity bonus. No ML model — pure signal engineering.
- [x] Shared, centralized clients
    - One `EmbeddingClient`, one `ChromaClient` per process, injected everywhere instead of constructed ad hoc.
- [x] Single RAG orchestration path
    - `RAGAssistant` is the only entry point; the old duplicate pipeline in `src/retrieval/query.py` has been removed.

---

### Phase 7 - Optional UI
Only when backend works

- [x] Create Streamlit interface
    - [x] Upload file
    - [x] Ask Questions
    - [x] Show Answers

--- 

### Phase 8 - Nice Extra Features
Later

- [ ] TODO Extraction
    - Prompt: `Extract actionable tasks from this text.`
- [ ] Weekly Review Generator
    - Input
        - Notes
        - Logs
    - Output
        - Achievments
        - Blockers
        - Priorities

---

## Current Features

- Document ingestion (`.txt`, `.md`, `.py`)
- Sentence-agnostic chunking (`ChunkerV1` — frozen baseline; see `chunking_v1.md`)
- Embedding generation via a single shared `EmbeddingClient`
- Vector storage via a single shared `ChromaClient`
- Semantic retrieval with heuristic reranking (`semantic_search_reranked`)
- Retrieval observability logging (query, chunk IDs, sources, similarity scores)
- Grounded answer generation with source attribution
- Short-term conversation memory (last 5 exchanges, in-memory)
- One orchestration path for every caller: `RAGAssistant`
- Streamlit UI (`app.py`) and CLI (`scripts/chat_cli.py`), both built on the same pipeline

---

## Known Limitations (Technical Debt)

Recorded here so it becomes the backlog, not a surprise.

- **Memory is not persistent.** `ConversationMemory` lives in process memory only — it resets on every new CLI run or Streamlit session restart.
- **No cross-encoder reranking.** The current reranker is heuristic (distance + size + adjacency signals), not a trained model. See `reranker.py`.
- **No citation confidence.** Sources are shown, but there's no scored confidence that a cited chunk actually supports a given sentence in the answer.
- **No automated evaluation benchmark.** `chunking_v1_eval_report.md` and `failure_analysis.md` are manual evaluation passes; there's no CI-run regression suite comparing chunker/retriever versions.
- **ChunkerV1's boundary quality is poor.** 81% of chunks have a broken start boundary and 75% a broken end boundary (see `chunking_v1_eval_report.md`). `ChunkerV2` is designed (`chunking_v2.md`) but **not implemented**.
- **No hybrid search (BM25 + vector).** Postponed per `project_mvp.md`.
- **No multi-user / auth.** Single-user local system by design.
- **No automated document monitoring.** Ingestion is manual; no folder-watching.

---

## Expected Final MVP

You can ask:

“What did I conclude about productivity systems?”

“What recurring tasks keep getting postponed?”

“Generate action items from these notes.”

And it answers using your own knowledge base.

---

## Long-Term Evolution Path

This project can later evolve into:

- personal second brain
- ERP assistant
- company knowledge assistant
- engineering documentation assistant
- AI operations dashboard
- autonomous workflow system

---

## Installation Guide

### Prerequisites

Before installing PKA-AI, make sure you have:

- Python 3.10+
- Git
- At least ~6GB RAM available (for local models via Ollama)
- Windows / Linux / macOS

---

### 1. Clone the repository
```bash
git clone https://github.com/PedroMaia21/Personal-Knowledge-Assistant.git
cd Personal-Knowledge-Assistant
```

---

### 2. Create a virtual environment
**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

---

### 4. Install Ollama

Download and install Ollama:

https://ollama.com

Verify installation:
```bash
ollama --version
```

---

### 5. Download required models
**Main chat model**
```bash
ollama run llama3.1
```
This will automatically download the model on first run.

**Embedding model**
```bash
ollama run nomic-embed-text
```

---

### 6. Run the assistant

**Streamlit UI** (upload documents, ask questions, view sources):
```bash
streamlit run app.py
```

**CLI** (same underlying `RAGAssistant` pipeline):
```bash
python scripts/chat_cli.py
```

`scripts/main.py` is a separate, minimal FastAPI health-check stub
(`GET /` → `{"status": "running"}`) and is not currently wired to the RAG
pipeline — it isn't the app entrypoint.

---

### 7. Quick sanity check

Test Ollama manually:
```bash
ollama run llama3.1
```
Then type:
```
Hello!
```