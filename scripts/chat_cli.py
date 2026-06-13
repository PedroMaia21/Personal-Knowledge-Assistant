import sys
from pathlib import Path

# Add root src path dynamically to execution runtime to ensure clean local modules access
sys.path.append(str(Path(__file__).parent.parent / "src"))
from models.llm import generate_chat_response

def main():
    print("🤖 Knowledge Base CLI Session Initiated. (Type 'exit' or 'quit' to close)\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("Closing interface pipeline.")
                break
                
            response = generate_chat_response(user_input)
            print(f"\nAssistant: {response}\n")
            
        except KeyboardInterrupt:
            print("\nSession Terminated.")
            break
        except Exception as e:
            print(f"\n[Runtime Error]: {e}\n")

if __name__ == "__main__":
    main()