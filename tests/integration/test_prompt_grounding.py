"""
test_prompt_grounding.py — Grounding enforcement tests for PKA-AI prompts.

What this tests:
    The SYSTEM_PROMPT + build_rag_prompt() combination must:
      1. Answer correctly when the answer IS in the context.
      2. Return NO_CONTEXT_REPLY when the answer is NOT in the context.

These are integration tests — they call the real local Ollama LLM, the same
model the production pipeline uses (llama3.1:8b via src/models/llm.py).

Prerequisites:
    - Ollama running locally  →  ollama serve
    - Model pulled            →  ollama pull llama3.1

Run:
    python -m pytest tests/integration/test_prompt_grounding.py -v
    # or directly:
    python test_prompt_grounding.py
"""

import sys

from src.config.prompts import build_rag_prompt, NO_CONTEXT_REPLY, SYSTEM_PROMPT
from src.models.llm import generate_chat_response


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_chunk(text: str, source: str = "test.md", chunk_index: int = 0) -> dict:
    """Constructs a minimal chunk dict matching the shape ChunkerV1 produces."""
    return {
        "text": text,
        "metadata": {
            "source": source,
            "chunk_index": chunk_index,
            "chunk_length": len(text),
            "chunker_version": "v1",
        },
    }


def _ask(context: str, question: str) -> str:
    """Builds the RAG prompt and calls the local LLM. Returns the answer string."""
    chunks = [_make_chunk(context)]
    prompt = build_rag_prompt(question, chunks)
    return generate_chat_response(prompt, system_override=SYSTEM_PROMPT).strip()


def _assert_grounded(answer: str, expect_grounded: bool, expected_contains: str = "") -> tuple[bool, str]:
    """
    Returns (passed: bool, reason: str).

    Grounded cases  : answer must contain the expected keyword and must NOT
                      contain the no-context reply.
    Ungrounded cases: answer must contain the exact NO_CONTEXT_REPLY string.
    """
    refused = NO_CONTEXT_REPLY.lower() in answer.lower()

    if expect_grounded:
        if refused:
            return False, f"Model refused but answer was present in context. Got: {answer!r}"
        if expected_contains and expected_contains.lower() not in answer.lower():
            return False, f"Expected {expected_contains!r} in answer. Got: {answer!r}"
        return True, f"Correctly answered: {answer!r}"
    else:
        if not refused:
            return False, f"Model answered from outside knowledge. Got: {answer!r}"
        return True, f"Correctly refused: {answer!r}"


# ── Test cases ────────────────────────────────────────────────────────────────

TEST_CASES = [
    {
        "id": 1,
        "description": "Answer IS in context — factual lookup",
        "context": "Python was created by Guido van Rossum.",
        "question": "Who created Python?",
        "expect_grounded": True,
        "expected_contains": "guido van rossum",
    },
    {
        "id": 2,
        "description": "Answer NOT in context — missing date",
        "context": "Python was created by Guido van Rossum.",
        "question": "When was Python created?",
        "expect_grounded": False,
    },
    {
        "id": 3,
        "description": "Answer IS in context — capital city",
        "context": "The capital of Portugal is Lisbon.",
        "question": "What is the capital of Portugal?",
        "expect_grounded": True,
        "expected_contains": "lisbon",
    },
    {
        "id": 4,
        "description": "Answer NOT in context — missing population",
        "context": "The capital of Portugal is Lisbon.",
        "question": "What is the population of Lisbon?",
        "expect_grounded": False,
    },
]


# ── Standalone runner ─────────────────────────────────────────────────────────

def run_tests() -> None:
    passed = 0
    failed = 0

    print("=" * 60)
    print("PKA-AI — Prompt Grounding Tests")
    print("=" * 60)

    for case in TEST_CASES:
        try:
            answer = _ask(case["context"], case["question"])
        except Exception as e:
            print(f"\n[TEST {case['id']}] {case['description']}")
            print(f"  ERROR: {e}")
            print(f"  Is Ollama running? →  ollama serve")
            failed += 1
            continue

        ok, reason = _assert_grounded(
            answer,
            case["expect_grounded"],
            case.get("expected_contains", ""),
        )
        status = "PASS" if ok else "FAIL"

        print(f"\n[TEST {case['id']}] {case['description']}")
        print(f"  Context  : {case['context']}")
        print(f"  Question : {case['question']}")
        print(f"  Answer   : {answer}")
        print(f"  Result   : {status} — {reason}")

        if ok:
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(TEST_CASES)} tests")
    print("=" * 60)

    if failed:
        sys.exit(1)


# ── pytest functions ──────────────────────────────────────────────────────────

def _run_single(case_id: int) -> None:
    case = next(c for c in TEST_CASES if c["id"] == case_id)
    answer = _ask(case["context"], case["question"])
    ok, reason = _assert_grounded(
        answer,
        case["expect_grounded"],
        case.get("expected_contains", ""),
    )
    assert ok, reason


def test_grounded_python_creator():
    _run_single(1)

def test_ungrounded_python_date():
    _run_single(2)

def test_grounded_portugal_capital():
    _run_single(3)

def test_ungrounded_lisbon_population():
    _run_single(4)


if __name__ == "__main__":
    run_tests()