import sys
import os
import signal
import threading
import json

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import (
    QUrl, QObject, Signal, Slot, QEvent, Qt, QTimer,
    QPropertyAnimation, QEasingCurve
)

from ui.floating_orb import FloatingOrb
from ui.splash import SplashScreen
from resource_path import resource_path

DASHBOARD_PATH = resource_path(os.path.join("ui", "dashboard.html"))
ASSETS_DIR = resource_path(os.path.join("ui", "assets"))
BOOT_INTRO_PATH = os.path.join(ASSETS_DIR, "boot_intro.wav")
BOOT_LOOP_PATH = os.path.join(ASSETS_DIR, "boot_loop.wav")
BOOT_READY_PATH = os.path.join(ASSETS_DIR, "boot_ready.wav")


class JarvisBridge(QObject):
    stateChanged = Signal(str, str)
    logAdded = Signal(str, str)
    shutdownRequested = Signal()

    @Slot(str)
    def sendText(self, text: str):
        import main as jarvis
        threading.Thread(target=jarvis.handle_text_input, args=(text,), daemon=True).start()

    @Slot(result=str)
    def getMemories(self):
        try:
            from skills.memory import _collection
            data = _collection.get()
            return json.dumps(data.get("documents", []))
        except Exception:
            return json.dumps([])

    @Slot()
    def requestShutdown(self):
        self.shutdownRequested.emit()

    @Slot()
    def _do_quit(self):
        print("Shutting down application...")
        QApplication.instance().quit()
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

        self._anim = None

    def _fade_out_then(self, callback):
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(220)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.InCubic)
        self._anim.finished.connect(callback)
        self._anim.start()

    def _fade_in(self):
        self.setWindowOpacity(0.0)
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(260)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()

    def closeEvent(self, event):
        event.ignore()
        self._fade_out_then(self._finish_minimize_to_orb)

    def _finish_minimize_to_orb(self):
        self.hide()
        self.setWindowOpacity(1.0)
        self.orb.animate_show()

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                self.showNormal()
                self._fade_out_then(self._finish_minimize_to_orb)
        super().changeEvent(event)

    def restore_from_orb(self):
        self.orb.animate_hide()
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self._fade_in()


class LoaderSignals(QObject):
    """Lets the background loading thread safely notify the main/GUI thread."""
    finished = Signal()
    status = Signal(str)


class BootController(QObject):
    """A proper QObject living on the main thread, so signal connections to its
    slots are guaranteed to run on the main/GUI thread via QueuedConnection —
    required since window/widget creation must happen on the main thread.

    Waits for BOTH the fixed boot sound to finish AND real model loading to
    finish before transitioning to the dashboard, so the sequence never cuts
    off early even if loading happens to finish faster."""

    def __init__(self, splash: SplashScreen):
        super().__init__()
        self.splash = splash
        self.loading_done = False
        self.sound_done = False

    @Slot(str)
    def on_status(self, text: str):
        self.splash.set_status(text)

    @Slot()
    def on_model_loading_finished(self):
        self.loading_done = True
        self._try_transition()

    @Slot()
    def on_sound_finished(self):
        self.sound_done = True
        self._try_transition()

    def _try_transition(self):
        if not (self.loading_done and self.sound_done):
            return

        from skills import ui_events

        bridge = JarvisBridge()
        ui_events.set_listener(bridge)

        orb = FloatingOrb(on_click_restore=None)
        bridge.stateChanged.connect(orb.set_state)

        window = JarvisWindow(bridge, orb)
        orb.on_click_restore = window.restore_from_orb

        bridge.shutdownRequested.connect(bridge._do_quit, Qt.QueuedConnection)

        def show_main_window():
            window.show()
            window._fade_in()
            window.browser.page().runJavaScript("playOpeningSequence();")
            voice_thread = threading.Thread(target=start_voice_loop, daemon=True)
            voice_thread.start()

        app = QApplication.instance()
        app._jarvis_bridge = bridge
        app._jarvis_orb = orb
        app._jarvis_window = window

        self.splash.fade_out(show_main_window)


def load_everything(signals: LoaderSignals, loading_done_event: threading.Event):
    """Runs on a background thread: imports main.py (which loads TTS/STT models),
    sets up the UI event bridge, and signals completion. Heavy work happens here
    so the splash screen keeps animating smoothly on the main thread."""
    signals.status.emit("LOADING VOICE SYNTHESIS")
    global jarvis
    import main as jarvis

    signals.status.emit("LOADING MEMORY SYSTEM")
    from skills import ui_events

    signals.status.emit("SYSTEMS READY")
    loading_done_event.set()
    signals.finished.emit()


class SoundSignals(QObject):
    """Lets the audio-playback thread safely tell the main thread its
    sequence (intro + loop-until-ready + ready chime) has fully finished."""
    finished = Signal()


def play_boot_sequence(loading_done_event: threading.Event, sound_signals: SoundSignals):
    """Runs on its own background thread: plays the intro once, loops the
    ambient section until loading_done_event is set, then plays the ready
    chime once and signals completion."""
    import sounddevice as sd
    import soundfile as sf

    try:
        intro_data, sr = sf.read(BOOT_INTRO_PATH)
        sd.play(intro_data, sr)
        sd.wait()

        loop_data, sr = sf.read(BOOT_LOOP_PATH)
        while not loading_done_event.is_set():
            sd.play(loop_data, sr)
            sd.wait()

        ready_data, sr = sf.read(BOOT_READY_PATH)
        sd.play(ready_data, sr)  # non-blocking — let it play while the dashboard opens
    except Exception as e:
        print(f"[WARN] Boot sound sequence failed: {e}")

    sound_signals.finished.emit()


def start_voice_loop():
    try:
        jarvis.main()
    except Exception as e:
        print(f"[ERROR] Voice loop crashed: {e}")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    keepalive_timer = QTimer()
    keepalive_timer.timeout.connect(lambda: None)
    keepalive_timer.start(200)

    # ---- Boot sequence ----
    splash = SplashScreen()
    splash.show()

    loading_done_event = threading.Event()

    loader_signals = LoaderSignals()
    sound_signals = SoundSignals()
    boot_controller = BootController(splash)

    loader_signals.status.connect(boot_controller.on_status, Qt.QueuedConnection)
    loader_signals.finished.connect(boot_controller.on_model_loading_finished, Qt.QueuedConnection)
    sound_signals.finished.connect(boot_controller.on_sound_finished, Qt.QueuedConnection)

    loader_thread = threading.Thread(
        target=load_everything, args=(loader_signals, loading_done_event), daemon=True
    )
    loader_thread.start()

    sound_thread = threading.Thread(
        target=play_boot_sequence, args=(loading_done_event, sound_signals), daemon=True
    )
    sound_thread.start()

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nInterrupted. Shutting down.")
        os._exit(0)