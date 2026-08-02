import time
import ollama
from router import route
from skills.screenshot import take_screenshot
from skills.open_app import open_target
from skills.discord_send import send_discord_message
from skills.web_search import search_and_summarize
from skills.vision import see_screen
from skills.memory import add_memory, search_memory
from skills.speak import speak
from skills.listen import listen
from skills.wake_word import wait_for_wake_word
from skills.interrupt import start_hotkey_listener, is_interrupted, clear_interrupt
from skills import ui_events

MODEL = "llama3.1:8b"

# How long to wait for a follow-up command before requiring "Hey Jarvis" again
FOLLOW_UP_WAIT_SECONDS = 6.0

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


def speak_and_notify(text: str):
    """Speaks text aloud AND notifies the UI (if connected) so the orb/log
    stay in sync regardless of whether this came from voice or typed input."""
    ui_events.emit_state("speaking", "Speaking")
    ui_events.emit_log("JARVIS", text)
    speak(text)
    ui_events.emit_state("idle", "Standby")


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

    elif action == "see_screen":
        return see_screen(args.get("question", "Describe what's currently on the screen."))

    elif action == "remember_fact":
        fact = args.get("fact", "")
        if fact:
            add_memory(fact)
            return "Got it, I'll remember that."
        return "I didn't catch what to remember."

    elif action == "general_chat":
        return args.get("reply", "I'm not sure how to respond to that.")

    else:
        return "I'm not sure what you want me to do."


def process_single_action(decision: dict) -> bool:
    """Handles confirmation (if needed) and execution for one action.
    Returns False if the whole batch should stop (interrupt or stop_listening),
    True to continue to the next action in the list."""

    action = decision.get("action")

    if action == "stop_listening":
        print("JARVIS: Shutting down. Goodbye.")
        speak_and_notify("Shutting down. Goodbye.")
        ui_events.emit_shutdown()
        return False

    if action in CONFIRMABLE_ACTIONS:
        confirmation_question = build_confirmation_prompt(decision)
        print(f"JARVIS: {confirmation_question}")
        speak_and_notify(confirmation_question)

        if is_interrupted():
            clear_interrupt()
            return False

        time.sleep(1.5)

        ui_events.emit_state("listening", "Listening")
        confirmation_reply = listen()
        print(f"You said: {confirmation_reply}")

        if is_interrupted():
            clear_interrupt()
            return False

        if not is_affirmative(confirmation_reply):
            print("JARVIS: Okay, cancelled.")
            speak_and_notify("Okay, cancelled.")
            time.sleep(1.5)
            return True  # skip this action, but continue with any remaining ones

    ui_events.emit_state("processing", "Processing")
    result = execute_action(decision)
    print(f"JARVIS: {result}")
    speak_and_notify(result)

    if is_interrupted():
        clear_interrupt()
        return False

    time.sleep(1.0)  # brief gap between chained actions
    return True


def handle_command(user_input: str) -> bool:
    """Routes and processes one full user command (which may expand into multiple
    chained actions). Returns False if the program should exit (stop_listening)."""

    ui_events.emit_log("You", user_input)
    ui_events.emit_state("processing", "Processing")

    relevant_memories = search_memory(user_input)
    memory_context = "\n".join(f"- {m}" for m in relevant_memories) if relevant_memories else ""

    actions = route(user_input, memory_context=memory_context)
    print(f"[DEBUG] Router decided {len(actions)} action(s): {actions}")

    for decision in actions:
        keep_going = process_single_action(decision)
        if not keep_going:
            if decision.get("action") == "stop_listening":
                return False
            break  # stop processing further actions in this batch, but keep the program running

    return True


def handle_text_input(text: str) -> None:
    """Entry point for commands typed into the UI (not spoken). Reuses the exact
    same routing/execution pipeline as voice, so behavior is identical either way.
    Note: 'stop_listening' from text input does NOT close the app — that only
    makes sense for the voice loop. It's treated as a no-op acknowledgment here."""
    if not text or not text.strip():
        return
    ui_events.emit_log("You", text.strip())
    ui_events.emit_state("processing", "Processing")

    relevant_memories = search_memory(text.strip())
    memory_context = "\n".join(f"- {m}" for m in relevant_memories) if relevant_memories else ""
    actions = route(text.strip(), memory_context=memory_context)
    print(f"[DEBUG] Router decided {len(actions)} action(s): {actions}")

    for decision in actions:
        if decision.get("action") == "stop_listening":
            speak_and_notify("Shutting down. Goodbye.")
            ui_events.emit_shutdown()
            return
        keep_going = process_single_action(decision)
        if not keep_going:
            break


def main():
    start_hotkey_listener()
    print("JARVIS-Local — say 'Hey Jarvis' to activate. Ctrl+C to exit. Ctrl+Shift+X to interrupt.")

    while True:
        wait_for_wake_word()
        ui_events.emit_state("processing", "Waking up")

        greeting = get_wake_greeting()
        print(f"JARVIS: {greeting}")
        speak_and_notify(greeting)

        if is_interrupted():
            clear_interrupt()
            continue

        time.sleep(1.5)  # let speaker echo die down before listening for command

        # Inner conversation loop: keep handling commands without requiring
        # "Hey Jarvis" again, as long as the user keeps talking within the
        # follow-up window. Falls back to wake-word mode on silence.
        in_conversation = True
        first_turn = True

        while in_conversation:
            wait_time = 15.0 if first_turn else FOLLOW_UP_WAIT_SECONDS
            first_turn = False

            ui_events.emit_state("listening", "Listening")
            user_input = listen(max_wait_for_speech=wait_time)
            print(f"You said: {user_input}")

            if is_interrupted():
                clear_interrupt()
                in_conversation = False
                continue

            if not user_input:
                print("Ending conversation, back to wake-word mode.")
                ui_events.emit_state("idle", "Standby")
                in_conversation = False
                continue

            should_continue_program = handle_command(user_input)

            if not should_continue_program:
                return  # stop_listening was triggered, exit the whole program

            if is_interrupted():
                clear_interrupt()
                in_conversation = False
                continue

            time.sleep(0.5)  # let speaker echo die down before listening for the next turn


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nJARVIS: Interrupted. Shutting down.")