import pytest
from retrieval.query import semantic_search, query_with_context

def test_semantic_search_execution():
    query = "How do vector databases store data?"
    results = semantic_search(query, top_k=2)
    
    assert isinstance(results, list)
    if len(results) > 0:
        assert "text" in results[0]
        assert "distance" in results[0]

def test_rag_query_generation():
    response = query_with_context("What is vector space exploration?")
    assert isinstance(response, str)
    assert len(response) > 0