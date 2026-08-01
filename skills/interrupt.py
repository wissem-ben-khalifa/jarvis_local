import keyboard
import threading

_interrupt_event = threading.Event()


def _on_hotkey():
    print("\n[INTERRUPT] Ctrl+Shift+X pressed — stopping current action.")
    _interrupt_event.set()


def start_hotkey_listener():
    """Registers the global interrupt hotkey. Call once at program startup."""
    keyboard.add_hotkey("ctrl+shift+x", _on_hotkey)
    print("Global interrupt hotkey registered: Ctrl+Shift+X")


def is_interrupted() -> bool:
    return _interrupt_event.is_set()


def clear_interrupt():
    _interrupt_event.clear()