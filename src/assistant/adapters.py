# src/assistant/adapters.py
from src.core.embedding_client import EmbeddingClient
from src.core.chroma_client import ChromaClient
from src.retrieval.search import semantic_search_reranked
from src.config.prompts import build_rag_prompt, SYSTEM_PROMPT
from src.models.llm import generate_chat_response


class SearchRetriever:
    """
    Retrieval adapter for RAGAssistant.

    Receives an EmbeddingClient and a ChromaClient instead of letting
    search.py construct its own defaults — the caller (app.py / test
    setup) owns the single shared instances for the process.
    """

    def __init__(
        self,
        embedding_client: EmbeddingClient | None = None,
        chroma_client: ChromaClient | None = None,
    ):
        self.embedding_client = embedding_client or EmbeddingClient()
        self.chroma_client = chroma_client or ChromaClient()

    def retrieve(self, question, k):
        return semantic_search_reranked(
            question,
            top_k=k,
            embedding_client=self.embedding_client,
            chroma_client=self.chroma_client,
        )


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