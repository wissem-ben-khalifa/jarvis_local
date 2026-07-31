import pyautogui
import pygetwindow as gw
import time
import subprocess
import os
import glob

pyautogui.PAUSE = 0.3


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

    pyautogui.hotkey("ctrl", "k")
    time.sleep(0.5)

    pyautogui.typewrite(contact_name, interval=0.03)
    time.sleep(1)

    pyautogui.press("enter")
    time.sleep(1)

    pyautogui.typewrite(message, interval=0.02)
    time.sleep(0.5)

    pyautogui.press("enter")
    time.sleep(0.5)

    return f"Sent your message to {contact_name}."