import sys
import os


def resource_path(relative_path: str) -> str:
    """Resolves a path to a bundled resource (like ui/dashboard.html), working
    correctly both when running from source (python run_app.py) and when
    running as a PyInstaller-frozen executable."""
    if getattr(sys, 'frozen', False):
        # Running as a bundled exe — PyInstaller onedir places data files
        # next to the executable, in the same folder as sys.executable.
        base_path = os.path.dirname(sys.executable)
    else:
        # Running from source — resolve relative to the project root
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)


def writable_data_path(relative_path: str) -> str:
    """Resolves a path for writable app data (memory_db, screenshots, .env)
    that should live next to the exe (or project root) either way, and be
    created if it doesn't exist."""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    full_path = os.path.join(base_path, relative_path)
    os.makedirs(os.path.dirname(full_path) if os.path.splitext(full_path)[1] else full_path, exist_ok=True)
    return full_path