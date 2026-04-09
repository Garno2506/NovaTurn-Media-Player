<<<<<<< HEAD
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import os


def resource_path_dev(relative_path):
    """
    Dev mode: resolve path relative to project root (app/)
    """
    base = os.path.dirname(os.path.dirname(__file__))  # ui → app
    return os.path.join(base, relative_path)


def resource_path(relative_path):
    """
    PyInstaller-safe path resolver.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return resource_path_dev(relative_path)


class MiniKeyboard(QtWidgets.QFrame):
    keyPressed = QtCore.pyqtSignal(str)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "overlay"):
            self.overlay.setGeometry(self.rect())

    def __init__(self, parent=None):
        super().__init__(parent)

        # Correct path for BOTH dev and PyInstaller
        image_path = resource_path("banners/NovaTurn_OSK.png")

        # Overlay PNG across the entire keyboard
        self.overlay = QtWidgets.QLabel(self)
        self.overlay.setPixmap(QtGui.QPixmap(image_path))
        self.overlay.setScaledContents(True)
        self.overlay.setGeometry(self.rect())
        self.overlay.lower()

        self.setObjectName("miniKeyboard")
        self.setFixedHeight(300)
        self.setStyleSheet("""
        QPushButton {
            background-color: rgba(30, 30, 30, 160);
            color: white;
            font-size: 18px;
            border-radius: 6px;
            padding: 8px;
        }

        QPushButton:pressed {
            background-color: rgba(255, 215, 0, 180);
            color: black;
        }
        """)

        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)

        rows = [
            list("1234567890"),
            list("QWERTYUIOP"),
            list("ASDFGHJKL"),
            list("ZXCVBNM"),
        ]

        # Add rows
        for r, row in enumerate(rows):
            for c, char in enumerate(row):
                btn = QtWidgets.QPushButton(char)
                btn.clicked.connect(lambda _, ch=char: self.keyPressed.emit(ch))
                layout.addWidget(btn, r, c)

        # Space bar
        space = QtWidgets.QPushButton("SPACE")
        space.clicked.connect(lambda: self.keyPressed.emit(" "))
        layout.addWidget(space, 4, 0, 1, 6)

        # Backspace
        back = QtWidgets.QPushButton("⌫")
        back.clicked.connect(lambda: self.keyPressed.emit("\b"))
        layout.addWidget(back, 4, 6, 1, 2)

        # Enter
        enter = QtWidgets.QPushButton("ENTER")
        enter.clicked.connect(lambda: self.keyPressed.emit("\r"))
        layout.addWidget(enter, 4, 8, 1, 2)

    def keyPressEvent(self, event):
        event.accept()
=======
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import os


def resource_path_dev(relative_path):
    """
    Dev mode: resolve path relative to project root (app/)
    """
    base = os.path.dirname(os.path.dirname(__file__))  # ui → app
    return os.path.join(base, relative_path)


def resource_path(relative_path):
    """
    PyInstaller-safe path resolver.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return resource_path_dev(relative_path)


class MiniKeyboard(QtWidgets.QFrame):
    keyPressed = QtCore.pyqtSignal(str)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "overlay"):
            self.overlay.setGeometry(self.rect())

    def __init__(self, parent=None):
        super().__init__(parent)

        # Correct path for BOTH dev and PyInstaller
        image_path = resource_path("banners/NovaTurn_OSK.png")

        # Overlay PNG across the entire keyboard
        self.overlay = QtWidgets.QLabel(self)
        self.overlay.setPixmap(QtGui.QPixmap(image_path))
        self.overlay.setScaledContents(True)
        self.overlay.setGeometry(self.rect())
        self.overlay.lower()

        self.setObjectName("miniKeyboard")
        self.setFixedHeight(300)
        self.setStyleSheet("""
        QPushButton {
            background-color: rgba(30, 30, 30, 160);
            color: white;
            font-size: 18px;
            border-radius: 6px;
            padding: 8px;
        }

        QPushButton:pressed {
            background-color: rgba(255, 215, 0, 180);
            color: black;
        }
        """)

        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)

        rows = [
            list("1234567890"),
            list("QWERTYUIOP"),
            list("ASDFGHJKL"),
            list("ZXCVBNM"),
        ]

        # Add rows
        for r, row in enumerate(rows):
            for c, char in enumerate(row):
                btn = QtWidgets.QPushButton(char)
                btn.clicked.connect(lambda _, ch=char: self.keyPressed.emit(ch))
                layout.addWidget(btn, r, c)

        # Space bar
        space = QtWidgets.QPushButton("SPACE")
        space.clicked.connect(lambda: self.keyPressed.emit(" "))
        layout.addWidget(space, 4, 0, 1, 6)

        # Backspace
        back = QtWidgets.QPushButton("⌫")
        back.clicked.connect(lambda: self.keyPressed.emit("\b"))
        layout.addWidget(back, 4, 6, 1, 2)

        # Enter
        enter = QtWidgets.QPushButton("ENTER")
        enter.clicked.connect(lambda: self.keyPressed.emit("\r"))
        layout.addWidget(enter, 4, 8, 1, 2)

    def keyPressEvent(self, event):
        event.accept()
>>>>>>> be9547aaccb1857afa059ff99cc82f20dba6ff7b
