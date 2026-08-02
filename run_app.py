import sys
import os
import signal
import threading
import json

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QUrl, QObject, Signal, Slot, QEvent, Qt, QTimer

import main as jarvis
from skills import ui_events
from skills.memory import _collection
from ui.floating_orb import FloatingOrb

DASHBOARD_PATH = os.path.join(os.path.dirname(__file__), "ui", "dashboard.html")


class JarvisBridge(QObject):
    """Bridge object exposed to JavaScript via QWebChannel. Python -> JS updates
    go through the signals below; JS -> Python calls go through the slots."""

    stateChanged = Signal(str, str)   # (state, label)
    logAdded = Signal(str, str)       # (who, text)
    shutdownRequested = Signal()      # full app shutdown (not just voice loop)

    @Slot(str)
    def sendText(self, text: str):
        """Called from JavaScript when the user submits the command bar."""
        threading.Thread(target=jarvis.handle_text_input, args=(text,), daemon=True).start()

    @Slot(result=str)
    def getMemories(self):
        """Called from JavaScript to populate the Memory tab. Returns a JSON list."""
        try:
            data = _collection.get()
            docs = data.get("documents", [])
            return json.dumps(docs)
        except Exception:
            return json.dumps([])

    @Slot()
    def requestShutdown(self):
        """Called from the dashboard's shutdown button."""
        self.shutdownRequested.emit()

    @Slot()
    def _do_quit(self):
        """Runs on the main/GUI thread (guaranteed by the QueuedConnection
        this is connected with), actually terminates the application."""
        print("Shutting down application...")
        QApplication.instance().quit()
        # Hard safety net: if something (e.g. a stuck thread) prevents a clean
        # quit within 2 seconds, force-kill the process so it never hangs.
        QTimer.singleShot(2000, lambda: os._exit(0))


class JarvisWindow(QMainWindow):
    def __init__(self, bridge: JarvisBridge, orb: FloatingOrb):
        super().__init__()
        self.orb = orb
        self.setWindowTitle("J.A.R.V.I.S.")
        self.resize(1200, 800)

        self.browser = QWebEngineView()

        self.channel = QWebChannel()
        self.channel.registerObject("bridge", bridge)
        self.browser.page().setWebChannel(self.channel)

        self.browser.load(QUrl.fromLocalFile(DASHBOARD_PATH))
        self.setCentralWidget(self.browser)

    def closeEvent(self, event):
        # X button minimizes to the floating orb instead of quitting the app.
        # Real shutdown only happens via voice/text "shutdown" or the dashboard button.
        event.ignore()
        self.hide()
        self.orb.show()

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                self.hide()
                self.showNormal()  # undo the OS minimize so re-showing later isn't stuck minimized
                self.hide()
                self.orb.show()
        super().changeEvent(event)

    def restore_from_orb(self):
        self.orb.hide()
        self.showNormal()
        self.raise_()
        self.activateWindow()


def start_voice_loop():
    """Runs the existing voice assistant loop (wake word, listen, etc.) in the
    background, so voice control keeps working alongside the UI."""
    try:
        jarvis.main()
    except Exception as e:
        print(f"[ERROR] Voice loop crashed: {e}")


if __name__ == "__main__":
    # Make Ctrl+C actually work — Qt's C++ event loop normally swallows it.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # closing/hiding the window shouldn't quit the app

    # A no-op timer that fires periodically just to give Python's interpreter
    # a chance to check for signals (like Ctrl+C) between Qt event loop cycles.
    keepalive_timer = QTimer()
    keepalive_timer.timeout.connect(lambda: None)
    keepalive_timer.start(200)

    bridge = JarvisBridge()
    ui_events.set_listener(bridge)  # so main.py's emit_state/emit_log reach the UI

    orb = FloatingOrb(on_click_restore=None)  # callback set after window exists
    bridge.stateChanged.connect(orb.set_state)

    window = JarvisWindow(bridge, orb)
    orb.on_click_restore = window.restore_from_orb

    # Explicit queued connection: guarantees _do_quit runs on the main/GUI
    # thread's event loop, even though shutdownRequested may be emitted from
    # the background voice thread. This was the root cause of shutdown hanging.
    bridge.shutdownRequested.connect(bridge._do_quit, Qt.QueuedConnection)

    window.show()

    voice_thread = threading.Thread(target=start_voice_loop, daemon=True)
    voice_thread.start()

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nInterrupted. Shutting down.")
        os._exit(0)