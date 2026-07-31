import pyautogui
import os
from datetime import datetime

SCREENSHOT_DIR = "screenshots"

def take_screenshot() -> str:
    """Takes a screenshot and saves it to the screenshots folder.
    Returns a short, spoken-friendly confirmation message (no filename)."""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)

    screenshot = pyautogui.screenshot()
    screenshot.save(filepath)

    print(f"[LOG] Screenshot saved to {filepath}")  # kept for debugging, not spoken

    return "Screenshot taken."