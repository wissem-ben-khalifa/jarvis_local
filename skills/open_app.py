import subprocess
import webbrowser

# Map of known targets -> how to open them.
# "app" = local program launched via subprocess
# "url" = website opened in default browser
KNOWN_TARGETS = {
    "notepad": {"type": "app", "value": "notepad.exe"},
    "edge": {"type": "app", "value": "msedge.exe"},
    "youtube": {"type": "url", "value": "https://youtube.com"},
    "instagram": {"type": "url", "value": "https://instagram.com"},
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