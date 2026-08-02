# Simple event bus so any part of the backend (voice loop or typed commands)
# can notify the UI in real time, without every module needing to know about
# PySide6/QWebChannel directly. The UI registers itself as the listener at startup.

_listener = None


def set_listener(listener):
    global _listener
    _listener = listener


def emit_state(state: str, label: str):
    """state: one of 'idle', 'listening', 'speaking', 'processing'."""
    if _listener:
        _listener.stateChanged.emit(state, label)


def emit_log(who: str, text: str):
    """who: 'You' or 'JARVIS'."""
    if _listener:
        _listener.logAdded.emit(who, text)


def emit_shutdown():
    """Signals the UI/app to fully shut down (not just stop the voice loop)."""
    if _listener:
        _listener.shutdownRequested.emit()