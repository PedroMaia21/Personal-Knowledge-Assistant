# src/assistant/adapters.py

from src.retrieval.search import semantic_search_reranked
from src.config.prompts import build_rag_prompt, SYSTEM_PROMPT
from src.models.llm import generate_chat_response


class SearchRetriever:
    def retrieve(self, question, k):
        return semantic_search_reranked(question, top_k=k)


class PromptBuilder:
    def build(self, chunks, question, history=None):
        """
        Receives raw chunk dicts and delegates to build_rag_prompt(),
        which calls format_context_block() to embed [Source: ...] labels
        and format_conversation_block() to render prior turns.

        `history` is optional — RAGAssistant.ask() passes
        memory.get_history(); direct/manual callers can omit it for a
        single-turn prompt.

        The `chunks` parameter name matches the updated RAGAssistant.ask()
        signature — do not change to `context`.
        """
        return build_rag_prompt(question, chunks, history=history)


class OllamaLLMClient:
    def generate(self, prompt):
        return generate_chat_response(prompt, system_override=SYSTEM_PROMPT)