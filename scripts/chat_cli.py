"""
scripts/chat_cli.py — Command-line interface for PKA-AI.

Responsibility: read a question, hand it to RAGAssistant, print the result.
That's it.

This file must never:
    - call semantic_search / semantic_search_reranked directly
    - build a prompt
    - call the LLM
    - touch ConversationMemory except via assistant.memory.clear()
      (a UI-level convenience, not a RAG step)

All of that lives behind RAGAssistant.ask(), which is the single
public entry point for the RAG pipeline (retrieval → memory injection →
prompt building → LLM call → memory update).
"""

from src.assistant.rag_assistant import RAGAssistant
from src.assistant.adapters import SearchRetriever, PromptBuilder, OllamaLLMClient
from src.assistant.memory import ConversationMemory
from src.utils.logging import display_answer

EXIT_COMMANDS = {"exit", "quit"}
RESET_COMMAND = "/reset"


def build_assistant() -> RAGAssistant:
    """
    Wires the same adapters used elsewhere (app.py) so retrieval,
    prompting, and generation behave identically across every
    interface. This is the only place the CLI touches the pipeline's
    internals — as construction, not as invocation.
    """
    return RAGAssistant(
        retriever=SearchRetriever(),
        prompt_builder=PromptBuilder(),
        llm_client=OllamaLLMClient(),
        memory=ConversationMemory(),
    )


def main() -> None:
    assistant = build_assistant()

    print("PKA-AI — Personal Knowledge Assistant")
    print(f"Type your question, '{RESET_COMMAND}' to clear memory, or 'exit' to quit.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not question:
            continue

        if question.lower() in EXIT_COMMANDS:
            break

        if question == RESET_COMMAND:
            assistant.memory.clear()
            print("(conversation memory cleared)\n")
            continue

        result = assistant.ask(question)
        display_answer(result)


if __name__ == "__main__":
    main()