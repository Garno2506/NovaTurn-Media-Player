from PyQt5 import QtWidgets, QtGui, QtCore
import os

def resource_path(relative):
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)

class HelpWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("NovaTurn Help")
        self.resize(900, 600)

        # Central widget: QWebEngineView (HTML viewer)
        try:
            from PyQt5.QtWebEngineWidgets import QWebEngineView
            self.viewer = QWebEngineView()
        except ImportError:
            # Fallback: QTextBrowser if WebEngine is missing
            self.viewer = QtWidgets.QTextBrowser()

        self.setCentralWidget(self.viewer)

        # Load default help page
        self.load_page("index.html")

    def load_page(self, filename):
        path = resource_path(os.path.join("help", filename))
        if os.path.exists(path):
            if hasattr(self.viewer, "setUrl"):
                self.viewer.setUrl(QtCore.QUrl.fromLocalFile(path))
            else:
                with open(path, "r", encoding="utf-8") as f:
                    self.viewer.setHtml(f.read())
        else:
            self.viewer.setHtml(f"<h2>Help page not found:</h2><p>{filename}</p>")
