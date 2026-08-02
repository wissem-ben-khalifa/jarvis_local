import sys
import signal
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QColor, QRadialGradient

ORB_SIZE = 120


class Orb(QWidget):
    def __init__(self):
        super().__init__()

        # Frameless, always-on-top, transparent background circular window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(ORB_SIZE, ORB_SIZE)

        # Position it in the bottom-right corner of the screen
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - ORB_SIZE - 40, screen.height() - ORB_SIZE - 80)

        self.pulse_value = 0.0
        self.pulse_direction = 1

        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)  # ~33 FPS

    def animate(self):
        self.pulse_value += 0.03 * self.pulse_direction
        if self.pulse_value >= 1.0 or self.pulse_value <= 0.0:
            self.pulse_direction *= -1
        self.update()  # triggers a repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Orb radius pulses gently between 80% and 100% of max size
        radius = ORB_SIZE * (0.4 + 0.1 * self.pulse_value)
        center = ORB_SIZE / 2

        # Radial gradient: bright glowing core fading to a soft transparent edge
        gradient = QRadialGradient(QPointF(center, center), radius)
        gradient.setColorAt(0.0, QColor(180, 220, 255, 255))  # bright near-white core
        gradient.setColorAt(0.4, QColor(100, 180, 255, 220))  # blue mid
        gradient.setColorAt(1.0, QColor(40, 100, 220, 0))     # fades to fully transparent at edge

        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center - radius, center - radius, radius * 2, radius * 2)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()


if __name__ == "__main__":
    # Make Ctrl+C actually work — Qt's C++ event loop normally swallows it.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)

    # A no-op timer that fires periodically just to give Python's interpreter
    # a chance to check for signals (like Ctrl+C) between Qt event loop cycles.
    keepalive_timer = QTimer()
    keepalive_timer.timeout.connect(lambda: None)
    keepalive_timer.start(200)

    orb = Orb()
    orb.show()

    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nClosed.")
        sys.exit(0)