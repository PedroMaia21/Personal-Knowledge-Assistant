# Personal Knowledge Base — Notes

---

## Productivity & Time Management

### Deep Work Principles
Deep work is the ability to focus without distraction on a cognitively demanding task.
It produces the most value and is becoming increasingly rare.
The key rule: schedule deep work blocks in advance and protect them like meetings.

Shallow work (emails, admin, quick replies) should be batched into one or two fixed windows per day.
Never let shallow work bleed into deep work hours.

The 90-minute rule: the brain can sustain high-focus work for roughly 90 minutes before needing a break.
After a deep work session, take a real break — no phone, no email.

### Time Blocking System
Every morning, block the calendar before checking messages.
Structure:
- 08:00–10:00 → Deep work block (hardest task of the day)
- 10:00–10:15 → Break
- 10:15–12:00 → Second focus block or meetings
- 13:00–14:00 → Shallow work batch (email, Slack, admin)
- 14:00–16:00 → Project work or learning
- 16:30 → Daily shutdown ritual

Shutdown ritual: review task list, capture loose ends, write tomorrow's plan, say "shutdown complete."
This signals the brain that work is done and prevents evening rumination.

### Weekly Review Process
Every Sunday evening, run the weekly review. Non-negotiable.

Steps:
1. Clear inbox to zero
2. Review calendar for last week — what happened, what was missed
3. Review task list — close completed items, reschedule incomplete ones
4. Review project list — is each project moving forward?
5. Review goals — am I drifting or on track?
6. Plan next week — set the 3 most important outcomes

The weekly review is the single highest-leverage habit in the productivity system.
Skipping it causes accumulation of mental debt that takes days to clear.

### Task Management Principles
Use a simple 3-tier system:
- Projects: outcomes that require multiple steps
- Tasks: single next actions attached to a project
- Someday/Maybe: ideas that are not active commitments

The most important question: "What is the next physical action?"
Vague tasks like "work on project X" are not actionable. Replace with "write first draft of section 2."

Capture everything immediately. The brain is for processing, not storing.

### Procrastination Patterns
Identified recurring blockers:
- Starting tasks that feel ambiguous or too large → fix: break into smaller pieces
- Perfectionism causing paralysis on writing tasks → fix: write a bad first draft intentionally
- Low-energy afternoons wasted on social media → fix: remove apps from phone during work hours

Most procrastination is not laziness. It is unclear next actions or emotional avoidance.

---

## AI & Machine Learning

### What is a Large Language Model
A large language model (LLM) is a neural network trained on massive text datasets to predict the next token.
Through this simple objective, the model learns grammar, facts, reasoning patterns, and even some world knowledge.

Key concepts:
- **Tokens**: the units the model processes (roughly 3/4 of a word on average)
- **Context window**: how much text the model can "see" at once
- **Temperature**: controls randomness in outputs (0 = deterministic, 1+ = creative/chaotic)
- **Parameters**: the weights of the network — more parameters generally means more capability

### Retrieval-Augmented Generation (RAG)
RAG is the pattern of combining a retrieval system with a language model.

Instead of relying solely on the model's training data, RAG:
1. Takes a user query
2. Searches a knowledge base for relevant documents
3. Injects those documents into the prompt as context
4. Asks the model to answer using only that context

Why RAG matters:
- Reduces hallucination (answers are grounded in real documents)
- Allows the model to access private or recent information
- Cheaper than fine-tuning for most use cases

### Embeddings and Vector Search
An embedding is a dense vector representation of a piece of text.
Texts with similar meaning produce vectors that are close together in vector space.

Vector search finds the nearest vectors to a query vector.
This enables semantic search: finding documents that mean the same thing, not just share the same words.

ChromaDB is a local vector database that stores embeddings and runs nearest-neighbour search.
The distance metric matters enormously:
- Cosine distance: measures angle between vectors, insensitive to magnitude — best for text embeddings
- L2 (Euclidean) distance: measures raw distance — not appropriate for high-dimensional text embeddings

nomic-embed-text produces 768-dimensional unit-normalised vectors.
For unit-normalised vectors, cosine distance is the correct choice.

### Ollama and Local Models
Ollama is a local model runtime that allows running LLMs on your own machine.
No API costs, no data sent to the cloud, no internet required once models are downloaded.

Models used in this project:
- `llama3.1:8b` — main chat and reasoning model
- `nomic-embed-text` — embedding model for semantic search

Trade-offs of local models:
- Slower than cloud APIs (depends on hardware)
- Limited context window compared to frontier models
- But: free, private, and always available

### AI Project Learnings
Key lesson from building PKA-AI: the distance metric bug.
ChromaDB defaults to L2 distance but text embeddings need cosine distance.
When wrong, similarity scores are meaningless — all clamped to 0.
Always declare `metadata={"hnsw:space": "cosine"}` explicitly at collection creation.

Observability is more important than it seems at the start.
Logging query, retrieved chunks, distances, and sources early saves enormous debugging time later.
Build retrieval inspection tools before building the answer generation layer.

---

## Project Planning & Retrospectives

### PKA-AI Project — Current Status
Phase 1–4 complete: document ingestion, chunking, embedding, vector storage, semantic search.
Phase 5 in progress: RAG pipeline and grounded answer generation.

Remaining MVP tasks:
- Build the retrieval prompt template
- Connect search results to LLM call
- Add source attribution to answers
- Build basic CLI interface
- Evaluate answer quality on test queries

Success criteria: system is useful enough to use voluntarily at least once per week.

### Retrospective — Phase 4 (Embeddings + Vector Search)

**What went well:**
- ChromaDB was extremely easy to set up locally
- nomic-embed-text produces high-quality embeddings with no configuration
- Semantic search returns intuitively relevant results

**What went wrong:**
- Distance metric defaulted to L2, producing garbage similarity scores
- Took a full investigation cycle to identify the root cause
- `normalize_similarity` formula was correct but the input values were wrong

**What to do differently:**
- Always check which distance metric the vector database is using before writing normalisation code
- Add an integration test that asserts similarity scores are in a plausible range (e.g. > 0.3 for relevant queries)
- Document infrastructure assumptions explicitly in config

**Action items from retrospective:**
- [ ] Add `hnsw:space: cosine` to collection creation and re-ingest all documents
- [ ] Write integration test for similarity score sanity
- [ ] Add metric type to config.py so it is never hardcoded in two places

### Project Planning Principles
Before starting a new feature, write a one-sentence definition of done.
If you cannot define done, the feature is not ready to be worked on yet.

Break work into phases with explicit goals, not just task lists.
Each phase should answer: "What capability does this add that didn't exist before?"

Keep a running blockers list. Review it at the start of every work session.
Most blockers are not real blockers — they are decisions that have not been made yet.

### Retrospective Format
A retrospective is useful only if it produces concrete action items.
Format:
- What went well (keep doing)
- What went wrong (stop or fix)
- What was learned (explicit capture)
- Action items (specific, assigned, time-boxed)

The most common retrospective failure: identifying problems but not writing action items.
A problem without an action item is just a complaint.

---

## Personal Goals & Habits

### Current Active Goals

**Learning goal:** Build a working RAG-based personal assistant from scratch.
Progress: ~70% complete. Retrieval works. Generation is next.
Why it matters: understanding the full stack makes me a better AI engineer.

**Health goal:** Walk at least 30 minutes every day.
Current streak: variable. Biggest obstacle: days with long coding sessions.
Fix: schedule the walk immediately after the daily shutdown ritual.

**Reading goal:** Read one technical book per month.
Current book: to be decided after finishing PKA-AI phase 5.
Backlog: Designing Data-Intensive Applications, The Pragmatic Programmer.

### Habit Tracking Observations
Habits that have stuck:
- Weekly review (Sunday evening)
- Daily shutdown ritual
- Morning deep work block

Habits that keep failing:
- Consistent exercise schedule
- Reading before bed (usually replaced by phone)
- Daily journaling

Pattern: habits that are tied to existing anchors (shutdown → walk, Sunday → review) survive.
Habits that float without an anchor drift and disappear.

### Energy Management
Energy levels follow a consistent pattern:
- Morning (08:00–11:00): high focus, creative work
- Early afternoon (13:00–15:00): lower energy, good for meetings and admin
- Late afternoon (15:00–17:00): second wind, good for learning and reading

Matching task type to energy level is more effective than forcing focus through willpower.
Never schedule creative or analytical work in the low-energy window.

### Values and Priorities
Core values that guide decisions:
1. Autonomy — work I control, on problems I care about
2. Mastery — continuous improvement in skills that matter
3. Contribution — building things that are genuinely useful to others

When in doubt about a decision, run it against these three. Most decisions become obvious.

### Weekly Intentions Template
Each week, set three intentions (not tasks — intentions):
- One for work / project
- One for learning
- One for health or relationships

Intentions are directional, not binary. They orient energy without creating pass/fail pressure.