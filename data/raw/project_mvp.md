# PKA-AI MVP Definition

## Purpose

Create a personal knowledge assistant capable of answering questions using information contained in a user's personal document collection.

The system must provide trustworthy answers by grounding responses on retrieved source documents.

---

## What Is The Smallest Version That Is Genuinely Useful?

A local application where a user can:

- Add documents to a knowledge base
- Ask questions in natural language
- Receive answers generated from relevant document excerpts
- Inspect which document chunks were used

This alone provides real value and solves a concrete problem.

---

## Mandatory Features (MVP Scope)

### Document Ingestion

Must be able to:

- Read documents from a folder
- Process supported formats
- Extract text

---

### Chunking

Must:

- Split documents into chunks
- Preserve source metadata

---

### Embedding Generation

Must:

- Generate embeddings for chunks
- Generate embeddings for user queries

---

### Vector Storage

Must:

- Store embeddings
- Retrieve nearest neighbours

---

### Retrieval

Must:

- Return top-k relevant chunks
- Return distance/similarity scores

---

### Observability

Must:

- Log retrieval information
- Show:
    - query
    - chunk IDs
    - document sources
    - similarity scores

This is important because retrospectives identified observability as a weakness.

---

### Grounded Answer Generation

Must:

- Build a prompt from retrieved chunks
- Generate an answer
- Avoid answering from model memory when sources are absent

---

### Source Attribution

Must:

- Show document names
- Show chunk references

User should always know where information came from.

---

Basic CLI Interface

Must:

- Accept a question
- Display answer
- Display sources

A CLI is sufficient for MVP.

No GUI required.

---

## Postponed Features (Post-MVP)

These are valuable but not necessary to validate the project.

### Web Interface

Examples:

- Streamlit
- Flask
- React frontend

Reason:

CLI already proves usefulness.

---

### Conversation Memory

Example:

- Follow-up questions
- Multi-turn conversations

Reason:

Single-turn retrieval already validates the core system.

---

### Hybrid Search

Example:

- BM25 + Vector Search

Reason:

Can improve quality later.

---

Reranking Models

Example:

- Cross-encoders

Reason:

Optimization rather than necessity.

---

### Agent Capabilities

Example:

- Tool usage
- Task execution
- Planning

Reason:

Outside the core knowledge retrieval problem.

---

### User Authentication

Reason:

Single-user local system does not need it.

---

### Automated Document Monitoring

Example:

- Watch folders
- Auto-ingestion

Reason:

Manual ingestion is enough initially.

---

### Multiple Knowledge Bases

Example:

- Personal
- Work
- Projects

Reason:

Can start with a single repository.

---

### Knowledge Graphs

Reason:

Advanced enhancement.

Not needed to validate usefulness.

---

### Fine-Tuned Models

Reason:

Premature optimization.

---

### Personal 'ERP' Integration

Reason:

Interesting future direction, but unrelated to proving the core concept.

---

## MVP Success Criteria

### The MVP is considered successful if:
- A new document can be added in less than 5 minutes
- The system retrieves relevant chunks consistently
- Answers are grounded in retrieved content
- Sources can be inspected
- The system is useful enough that I voluntarily use it at least once per week