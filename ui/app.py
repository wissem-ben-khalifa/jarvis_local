import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Qt

# Path to the dashboard HTML file, relative to this script's location
DASHBOARD_PATH = os.path.join(os.path.dirname(__file__), "dashboard.html")


class JarvisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S.")
        self.resize(1200, 800)

        self.browser = QWebEngineView()
        self.browser.load(QUrl.fromLocalFile(DASHBOARD_PATH))
        self.setCentralWidget(self.browser)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JarvisWindow()
    window.show()
    sys.exit(app.exec())