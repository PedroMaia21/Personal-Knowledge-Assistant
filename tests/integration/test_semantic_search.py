"""
tests/integration/test_semantic_search.py

Exercises the real retrieval + RAG surface:
    - src.retrieval.search.semantic_search_reranked   (raw retrieval)
    - src.assistant.rag_assistant.RAGAssistant.ask()  (retrieval + prompt + LLM)

`semantic_search_reranked` has always lived in src/retrieval/search.py, never
in src/retrieval/query.py. `query_with_context` never existed anywhere in the
codebase — the previous version of this test imported both from
`src.retrieval.query`, which is why it never actually ran.
"""

import pytest

from src.retrieval.search import semantic_search_reranked
from src.assistant.rag_assistant import RAGAssistant
from src.assistant.adapters import SearchRetriever, PromptBuilder, OllamaLLMClient


def test_semantic_search_execution():
    query = "How do vector databases store data?"
    results = semantic_search_reranked(query, top_k=2)

    assert isinstance(results, list)
    if len(results) > 0:
        assert "text" in results[0]
        assert "distance" in results[0]


def test_rag_query_generation():
    assistant = RAGAssistant(
        retriever=SearchRetriever(),
        prompt_builder=PromptBuilder(),
        llm_client=OllamaLLMClient(),
    )
    result = assistant.ask("What is vector space exploration?")

    assert isinstance(result, dict)
    assert "answer" in result
    assert isinstance(result["answer"], str)
    assert len(result["answer"]) > 0