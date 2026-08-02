from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QColor, QRadialGradient
import math

ORB_SIZE = 90

# Same state color language as the dashboard, kept consistent across both UIs
STATE_COLORS = {
    "idle":       ("#0d3038", "#4fd8f0"),
    "listening":  ("#0d3a30", "#4ff0c0"),
    "speaking":   ("#3a280d", "#f0b04f"),
    "processing": ("#2a0d3a", "#c04ff0"),
}


class FloatingOrb(QWidget):
    """Small always-on-top ambient indicator, shown when the main dashboard
    window isn't open/focused. Click it to bring the dashboard back."""

    def __init__(self, on_click_restore):
        super().__init__()
        self.on_click_restore = on_click_restore
        self.state = "idle"
        self.t = 0.0

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(ORB_SIZE, ORB_SIZE)

        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - ORB_SIZE - 30, screen.height() - ORB_SIZE - 70)

        self.timer = QTimer()
        self.timer.timeout.connect(self._animate)
        self.timer.start(30)

    def set_state(self, state: str, label: str = ""):
        self.state = state if state in STATE_COLORS else "idle"

    def _animate(self):
        self.t += 0.035
        self.update()

    def mousePressEvent(self, event):
        if self.on_click_restore:
            self.on_click_restore()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center = ORB_SIZE / 2
        dark, bright = STATE_COLORS[self.state]

        # Motion differs by state, so listening vs speaking FEEL different,
        # not just look different: listening = outward expanding rings (like
        # sound waves coming IN), speaking = tight fast inner pulse (like a
        # voice coming OUT).
        if self.state == "listening":
            base_radius = ORB_SIZE * 0.28
            # draw expanding ripple rings
            for i in range(3):
                phase = (self.t * 1.2 + i * 0.6) % 1.8
                ring_radius = base_radius + phase * (ORB_SIZE * 0.32)
                alpha = max(0, int(160 * (1 - phase / 1.8)))
                painter.setPen(Qt.NoPen)
                ring_color = QColor(bright)
                ring_color.setAlpha(alpha)
                painter.setBrush(Qt.NoBrush)
                painter.setPen(ring_color)
                painter.drawEllipse(QPointF(center, center), ring_radius, ring_radius)
            core_radius = base_radius

        elif self.state == "speaking":
            core_radius = ORB_SIZE * 0.26 + abs(math.sin(self.t * 9)) * ORB_SIZE * 0.09

        elif self.state == "processing":
            core_radius = ORB_SIZE * 0.27 + math.sin(self.t * 4) * ORB_SIZE * 0.03

        else:  # idle — slow gentle breathing
            core_radius = ORB_SIZE * 0.26 + math.sin(self.t * 1.2) * ORB_SIZE * 0.02

        gradient = QRadialGradient(QPointF(center, center), core_radius)
        gradient.setColorAt(0.0, QColor("#eafcff"))
        gradient.setColorAt(0.45, QColor(bright))
        edge = QColor(dark)
        edge.setAlpha(0)
        gradient.setColorAt(1.0, edge)

        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(center, center), core_radius, core_radius)