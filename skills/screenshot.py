import pyautogui
import os
from datetime import datetime

SCREENSHOT_DIR = "screenshots"

def take_screenshot() -> str:
    """Takes a screenshot and saves it to the screenshots folder.
    Returns a short confirmation message (for JARVIS to speak)."""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)

    screenshot = pyautogui.screenshot()
    screenshot.save(filepath)

    return f"Screenshot saved as {filename}."