import math
from PySide6.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QPointF, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QRadialGradient, QFont

SPLASH_SIZE = 280


class SplashScreen(QWidget):
    """Boot-up loading screen shown while the heavy models (TTS, STT, LLM
    connection) load in the background. Fades out once loading is complete."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(480, 420)

        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )

        self.t = 0.0
        self.status_text = "INITIALIZING"

        self.status_label = QLabel(self)
        self.status_label.setGeometry(0, 340, 480, 30)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(
            "color: #7fdcf0; font-family: 'Consolas', monospace; "
            "font-size: 13px; letter-spacing: 4px; background: transparent;"
        )
        self.status_label.setText(self.status_text)

        self.timer = QTimer()
        self.timer.timeout.connect(self._animate)
        self.timer.start(30)

        self._anim = None

    def set_status(self, text: str):
        self.status_text = text
        self.status_label.setText(text)

    def _animate(self):
        self.t += 0.03
        self.update()

    def fade_out(self, on_finished):
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(450)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.InCubic)

        def finish():
            self.timer.stop()
            self.hide()
            self.close()
            on_finished()

        self._anim.finished.connect(finish)
        self._anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        cx, cy = 240, 190

        # Rotating outer rings (arcs, not full circles, for a "scanning" feel)
        for i, (radius, speed, arc_len, width) in enumerate([
            (95, 0.6, 100, 2),
            (115, -0.4, 60, 1.5),
            (135, 0.25, 140, 1),
        ]):
            painter.save()
            painter.translate(cx, cy)
            painter.rotate((self.t * speed * 60) % 360)
            color = QColor(79, 216, 240, 130 - i * 25)
            pen = painter.pen()
            pen.setColor(color)
            pen.setWidthF(width)
            painter.setPen(pen)
            painter.drawArc(int(-radius), int(-radius), int(radius * 2), int(radius * 2),
                             0, int(arc_len * 16))
            painter.restore()

        # Pulsing core, powering up over time (grows on first ~1.5s, then settles)
        power_up = min(1.0, self.t / 1.5)
        base_radius = 40 * power_up
        pulse = math.sin(self.t * 3) * 4 * power_up
        radius = base_radius + pulse

        grad = QRadialGradient(QPointF(cx, cy), max(radius, 1))
        grad.setColorAt(0.0, QColor(230, 250, 255, int(255 * power_up)))
        grad.setColorAt(0.5, QColor(79, 216, 240, int(220 * power_up)))
        edge = QColor(20, 80, 100, 0)
        grad.setColorAt(1.0, edge)

        painter.setBrush(grad)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), max(radius, 1), max(radius, 1))

        # Brand text
        painter.setPen(QColor(182, 243, 255, int(255 * power_up)))
        font = QFont("Consolas", 22, QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 8)
        painter.setFont(font)
        painter.drawText(0, 250, 480, 40, Qt.AlignCenter, "J.A.R.V.I.S.")