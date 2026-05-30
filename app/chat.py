import ollama

MODEL = "llama3.1"

SYSTEM_PROMPT = """
You are a helpful assistant that provides information based on the user's queries. 
Use the knowledge you have been trained on to answer questions and provide insights.
Be concise, structured, actionable and informative in your responses. If you don't know the answer, it's okay to say so.
"""

def chat(prompt):
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )
    return response["message"]["content"]

def main():
    print("Welcome to the Personal Knowledge Assistant! Type 'exit' or 'quit' to quit.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        try:
            response = chat(user_input)
            print(f"Assistant: {response}\n")
        except Exception as e:
            print(f"[Error]: {e}\n")

if __name__ == "__main__":
    main()