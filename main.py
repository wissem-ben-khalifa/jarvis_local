from router import route
from skills.screenshot import take_screenshot
from skills.open_app import open_target
from skills.discord_send import send_discord_message
from skills.web_search import search_and_summarize


def execute_action(decision: dict) -> str:
    """Takes the router's decision dict and actually calls the right skill function."""

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
    print("JARVIS-Local — type 'quit' to exit")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("quit", "exit"):
            break

        decision = route(user_input)
        print(f"[DEBUG] Router decided: {decision}")  # temporary, remove once trusted

        result = execute_action(decision)
        print(f"JARVIS: {result}")


if __name__ == "__main__":
    main()