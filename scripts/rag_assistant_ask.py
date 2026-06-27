from src.assistant.rag_assistant import RAGAssistant
from src.assistant.adapters import SearchRetriever, PromptBuilder, OllamaLLMClient

assistant = RAGAssistant(
    retriever=SearchRetriever(),
    prompt_builder=PromptBuilder(),
    llm_client=OllamaLLMClient(),
)

answer = assistant.ask("What went wrong during environment setup?")
print(answer)