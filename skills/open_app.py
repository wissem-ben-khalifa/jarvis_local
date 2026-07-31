import subprocess
import webbrowser

KNOWN_TARGETS = {
    "notepad": {"type": "app", "value": "notepad.exe"},
    "edge": {"type": "app", "value": "msedge.exe"},
    "youtube": {"type": "url", "value": "https://youtube.com"},
    "instagram": {"type": "url", "value": "https://instagram.com"},
    "tiktok": {"type": "url", "value": "https://tiktok.com"},
    "twitch": {"type": "url", "value": "https://twitch.tv"},
    "discord": {"type": "url", "value": "https://discord.com/app"},
    "gmail": {"type": "url", "value": "https://mail.google.com"},
    "google": {"type": "url", "value": "https://google.com"},
    "spotify": {"type": "url", "value": "https://open.spotify.com"},
    "twitter": {"type": "url", "value": "https://x.com"},
    "x": {"type": "url", "value": "https://x.com"},
    "facebook": {"type": "url", "value": "https://facebook.com"},
    "reddit": {"type": "url", "value": "https://reddit.com"},
    "netflix": {"type": "url", "value": "https://netflix.com"},
    "amazon": {"type": "url", "value": "https://amazon.com"},
    "whatsapp": {"type": "url", "value": "https://web.whatsapp.com"},
    "chatgpt": {"type": "url", "value": "https://chat.openai.com"},
    "calculator": {"type": "app", "value": "calc.exe"},
    "paint": {"type": "app", "value": "mspaint.exe"},
}

def open_target(name: str) -> str:
    """Opens a known app or website by name.
    Returns a short confirmation message (for JARVIS to speak)."""
    key = name.strip().lower()

    if key not in KNOWN_TARGETS:
        return f"I don't know how to open '{name}' yet."

    target = KNOWN_TARGETS[key]

    if target["type"] == "app":
        subprocess.Popen(target["value"])
    elif target["type"] == "url":
        webbrowser.open(target["value"])

    return f"Opening {name}."