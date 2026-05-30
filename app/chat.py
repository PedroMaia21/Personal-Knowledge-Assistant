import ollama

MODEL = "llama3.1"

def chat(prompt):
    response = ollama.chat(
        model=MODEL,
        messages=[
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