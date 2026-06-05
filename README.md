# Personal-Knowledge-Assistant

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
```
Documents
   ↓
Chunking
   ↓
Embeddings
   ↓
ChromaDB
   ↓
User Question
   ↓
Semantic Search
   ↓
Relevant Chunks
   ↓
LLM Prompt
   ↓
Answer
```

---

### Folder Structure
```
Personal-Knowledge-Assistant/
│
├── app/
│   ├── main.py
│   ├── ingest.py
│   ├── query.py
│   ├── prompts.py
│   ├── chunking.py
│   ├── utils.py
|   ├── loader.py
|   ├── chat.py
|   └── embeddings.py
│
├── data/
│   ├── raw/
│   └── chroma/
│
├── requirements.txt
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
- [ ] Implement Semantic Search
    - Input: `"What were the productivity review conclusions?"`
    - Outputs:
        - top relevant chunks

---

### Phase 5 - Build the AI Assistant

**Goal**
Combine retrieval + Generation

- [ ] Create Retrieval Prompt
**Prompt Structure:**
```
Use ONLY the provided context.

Context:
...

Question:
...
```
- [ ] Implement RAG pipeline
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

- [ ] Add source references
    - Example: `Source: weekly_review_may.txt`
- [ ] Add converation memory
    - Store:
        - [ ] previous questions
        - [ ] previous answers
    - Simple in-memory list is enough.

---

### Phase 7 - Optional UI
Only when backend works

- [ ] Create Streamlit interface
    - [ ] Upload file
    - [ ] Ask Questions
    - [ ] Show Answers

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

### 6. Run the API server
```bash
uvicorn app.main:app --reload
```
Then open:

http://localhost:8000
http://localhost:8000/docs

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