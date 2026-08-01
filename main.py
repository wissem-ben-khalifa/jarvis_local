import time
import ollama
from router import route
from skills.screenshot import take_screenshot
from skills.open_app import open_target
from skills.discord_send import send_discord_message
from skills.web_search import search_and_summarize
from skills.speak import speak
from skills.listen import listen
from skills.wake_word import wait_for_wake_word
from skills.interrupt import start_hotkey_listener, is_interrupted, clear_interrupt

MODEL = "llama3.1:8b"

# Actions that require explicit voice confirmation before running, since they have
# real-world, hard-to-undo effects (sending messages, etc.)
CONFIRMABLE_ACTIONS = {"send_discord_message"}

# Simple affirmative-word check for confirmation replies. Not perfect, but good
# enough given replies are short and STT is reasonably reliable for single words.
AFFIRMATIVE_WORDS = {"yes", "yeah", "yep", "confirm", "correct", "sure", "go ahead", "do it"}


def is_affirmative(text: str) -> bool:
    text = text.lower().strip()
    return any(word in text for word in AFFIRMATIVE_WORDS)


def build_confirmation_prompt(decision: dict) -> str:
    """Builds a short spoken confirmation question describing what's about to happen."""
    action = decision.get("action")
    args = decision.get("args", {})

    if action == "send_discord_message":
        contact = args.get("contact_name", "someone")
        message = args.get("message", "")
        return f'Send "{message}" to {contact} on Discord — confirm?'

    return "Are you sure you want me to do that?"

GREETING_SYSTEM_PROMPT = """You are JARVIS, a voice assistant that was just activated by the user saying "Hey Jarvis."
Respond with a SHORT greeting acknowledging you're ready to help, 3-8 words max.
Vary your wording each time — don't always say the same thing.
Examples of the right tone: "Yes, how can I help?", "I'm listening.", "What do you need?", "At your service."
No markdown, no explanation, just the greeting itself.
"""


def get_wake_greeting() -> str:
    """Asks the LLM to generate a short, varied greeting after wake word detection."""
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "system", "content": GREETING_SYSTEM_PROMPT},
                  {"role": "user", "content": "Generate the greeting now."}]
    )
    return response["message"]["content"].strip()


def execute_action(decision: dict) -> str:
    action = decision.get("action")
    args = decision.get("args", {})

    if action == "take_screenshot":
        return take_screenshot()

    elif action == "open_target":
        return open_target(args.get("name", ""))

    elif action == "send_discord_message":
        return send_discord_message(
            args.get("contact_name", ""),
            args.get("message", "")
        )

    elif action == "search_and_summarize":
        return search_and_summarize(args.get("query", ""))

    elif action == "general_chat":
        return args.get("reply", "I'm not sure how to respond to that.")

    else:
        return "I'm not sure what you want me to do."


def main():
    start_hotkey_listener()
    print("JARVIS-Local — say 'Hey Jarvis' to activate. Ctrl+C to exit. Ctrl+Shift+X to interrupt.")

    while True:
        wait_for_wake_word()

        greeting = get_wake_greeting()
        print(f"JARVIS: {greeting}")
        speak(greeting)

        if is_interrupted():
            clear_interrupt()
            continue

        time.sleep(1.5)  # let speaker echo die down before listening for command

        user_input = listen()
        print(f"You said: {user_input}")

        if is_interrupted():
            clear_interrupt()
            continue

        if not user_input:
            print("JARVIS: I didn't catch that.")
            continue

        decision = route(user_input)
        print(f"[DEBUG] Router decided: {decision}")

        if decision.get("action") == "stop_listening":
            print("JARVIS: Shutting down. Goodbye.")
            speak("Shutting down. Goodbye.")
            break

        if decision.get("action") in CONFIRMABLE_ACTIONS:
            confirmation_question = build_confirmation_prompt(decision)
            print(f"JARVIS: {confirmation_question}")
            speak(confirmation_question)

            if is_interrupted():
                clear_interrupt()
                continue

            time.sleep(1.5)

            confirmation_reply = listen()
            print(f"You said: {confirmation_reply}")

            if is_interrupted():
                clear_interrupt()
                continue

            if not is_affirmative(confirmation_reply):
                print("JARVIS: Okay, cancelled.")
                speak("Okay, cancelled.")
                time.sleep(1.5)
                continue

        result = execute_action(decision)
        print(f"JARVIS: {result}")
        speak(result)

        if is_interrupted():
            clear_interrupt()
            continue

        time.sleep(1.5)  # let speaker echo die down before re-arming wake word listener


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nJARVIS: Interrupted. Shutting down.")