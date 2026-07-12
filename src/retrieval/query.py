"""
query.py — DEPRECATED.

This module used to duplicate what RAGAssistant.ask() now does:
retrieve → build prompt → call LLM. That duplication is exactly what
the "single RAG entry point" refactor was meant to eliminate.

Retrieval, prompt-building, LLM invocation, and conversation memory
now live behind one orchestrator: src.assistant.rag_assistant.RAGAssistant.

Migration:
    OLD:
        from src.retrieval.query import answer_question
        result = answer_question(question, top_k=5)

    NEW:
        from src.assistant.rag_assistant import RAGAssistant
        from src.assistant.adapters import SearchRetriever, PromptBuilder, OllamaLLMClient

        assistant = RAGAssistant(
            retriever=SearchRetriever(),
            prompt_builder=PromptBuilder(),
            llm_client=OllamaLLMClient(),
        )
        result = assistant.ask(question, k=5)

`result` has the same shape either way: {"answer", "chunks", "prompt", "sources"}.

This module is intentionally left without a working `answer_question()`
so any remaining caller fails loudly at import time instead of silently
bypassing conversation memory and the shared pipeline.
"""

raise ImportError(
    "src.retrieval.query.answer_question has been removed. "
    "Use src.assistant.rag_assistant.RAGAssistant.ask() instead — "
    "see the module docstring for the migration snippet."
)