import ollama
from skills.screenshot import take_screenshot

MODEL = "llama3.1:8b"

SYSTEM_PROMPT = """You are JARVIS, a local voice assistant running on the user's PC.
Rules:
- Keep replies short and conversational (1-3 sentences), since they will be spoken aloud via text-to-speech.
- Never use markdown, bullet points, or code formatting in your replies.
- Be helpful, direct, and slightly witty, but not overly chatty.
- If you don't know something or can't do something, say so briefly instead of guessing.
"""

def ask_ollama(prompt: str) -> str:
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )
    return response["message"]["content"]

def main():
    print("JARVIS-Local (text mode) — type 'quit' to exit, 'screenshot' to test the skill")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("quit", "exit"):
            break
        elif user_input.lower() == "screenshot":
            result = take_screenshot()
            print(f"JARVIS: {result}")
        else:
            reply = ask_ollama(user_input)
            print(f"JARVIS: {reply}")

if __name__ == "__main__":
    main()