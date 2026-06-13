import ollama

MODEL = "llama3.1"
SYSTEM_PROMPT = """You are a helpful personal knowledge assistant. 
Use the provided knowledge base context elements to resolve user queries concisely and transparently."""

def generate_chat_response(prompt: str, system_override: str = SYSTEM_PROMPT) -> str:
    """Interacts directly with the local Ollama LLM framework service instances."""
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_override},
            {"role": "user", "content": prompt}
        ]
    )
    return response["message"]["content"]