# src/assistant/adapters.py

from src.retrieval.search import semantic_search_reranked
from src.config.prompts import build_rag_prompt, SYSTEM_PROMPT
from src.models.llm import generate_chat_response

class SearchRetriever:
    def retrieve(self, question, k):
        return semantic_search_reranked(question, top_k=k)

class PromptBuilder:
    def build(self, context, question):
        # reuse your existing build_rag_prompt,
        # or pass context directly as pre-built chunks
        return build_rag_prompt(question, [{"text": context, "metadata": {}}])

class OllamaLLMClient:
    def generate(self, prompt):
        return generate_chat_response(prompt, system_override=SYSTEM_PROMPT)