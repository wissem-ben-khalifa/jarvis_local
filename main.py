import ollama

MODEL = "llama3.1:8b"

def ask_ollama(prompt: str) -> str:
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]

def main():
    print("JARVIS-Local (text mode) — type 'quit' to exit")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("quit", "exit"):
            break
        reply = ask_ollama(user_input)
        print(f"JARVIS: {reply}")

if __name__ == "__main__":
    main()