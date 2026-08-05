import ollama
import base64
import os
from datetime import datetime
from resource_path import writable_data_path

VISION_MODEL = "llava"
SUMMARY_MODEL = "llama3.1:8b"
SCREENSHOT_DIR = writable_data_path("screenshots")


def _take_screenshot_for_vision() -> str:
    """Takes a screenshot specifically for vision analysis and returns its filepath.
    Reuses the same screenshot mechanism as the take_screenshot skill."""
    import pyautogui

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    filename = f"vision_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)

    screenshot = pyautogui.screenshot()
    screenshot.save(filepath)

    return filepath


def see_screen(question: str = "Describe what's on the screen.") -> str:
    """Takes a screenshot and asks the local vision model to answer a question
    about what's currently displayed. Returns a short spoken-style answer."""

    filepath = _take_screenshot_for_vision()
    print(f"[LOG] Vision screenshot saved to {filepath}")

    with open(filepath, "rb") as f:
        image_bytes = f.read()

    response = ollama.chat(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": question,
                "images": [image_bytes]
            }
        ]
    )

    raw_description = response["message"]["content"]

    if not raw_description or not raw_description.strip():
        return "I couldn't make out anything useful on the screen."

    # Condense the verbose vision output into a short spoken reply using the
    # main LLM, which follows brevity instructions far more reliably than llava does.
    condense_prompt = f"""You are JARVIS, a voice assistant. Someone asked: "{question}"

A vision model looked at their screen and described it as:
{raw_description}

Give a direct, natural spoken answer in ONE short sentence based on that description.
No markdown, no mentioning "the image" or "the vision model" — just answer naturally.
"""

    condensed = ollama.chat(
        model=SUMMARY_MODEL,
        messages=[{"role": "user", "content": condense_prompt}]
    )

    return condensed["message"]["content"].strip()