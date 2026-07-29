import pyautogui
import pygetwindow as gw
import time
import subprocess
import os
import glob

pyautogui.PAUSE = 0.3
DEBUG_DIR = "debug_screenshots"


def find_discord_path():
    """Finds the Discord executable path dynamically, since the version folder changes on updates."""
    matches = glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Discord\app-*\Discord.exe"))
    return matches[0] if matches else None


def find_discord_window():
    for window in gw.getAllWindows():
        if "Discord" in window.title:
            return window
    return None


def focus_window(win):
    """More reliable window focusing on Windows — minimizes then restores,
    which forces the OS to actually bring it to foreground. .activate() alone
    can silently fail on Windows without raising an error."""
    try:
        win.minimize()
        time.sleep(0.3)
        win.restore()
        time.sleep(0.3)
        win.activate()
        time.sleep(0.3)
    except Exception:
        pass


def _debug_shot(label: str):
    os.makedirs(DEBUG_DIR, exist_ok=True)
    pyautogui.screenshot().save(os.path.join(DEBUG_DIR, f"{label}.png"))


def send_discord_message(contact_name: str, message: str) -> str:
    """Opens Discord (if not already open), searches for a contact by name,
    and sends them a message as if typed by the user."""

    win = find_discord_window()

    if win is None:
        discord_path = find_discord_path()
        if not discord_path:
            return "I couldn't find Discord installed on this PC."
        subprocess.Popen(discord_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(6)
        win = find_discord_window()
        if win is None:
            return "I couldn't open Discord."

    focus_window(win)
    _debug_shot("1_after_focus")

    pyautogui.hotkey("ctrl", "k")
    time.sleep(0.5)
    _debug_shot("2_after_search_open")

    pyautogui.typewrite(contact_name, interval=0.03)
    time.sleep(1)
    _debug_shot("3_after_typing_name")

    pyautogui.press("enter")
    time.sleep(1)
    _debug_shot("4_after_enter")

    pyautogui.typewrite(message, interval=0.02)
    time.sleep(0.5)
    _debug_shot("5_after_typing_message")

    pyautogui.press("enter")
    time.sleep(0.5)
    _debug_shot("6_after_send")

    return f"Sent your message to {contact_name}."