<<<<<<< HEAD
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import os


def resource_path_dev(relative_path: str) -> str:
    """
    Dev mode: resolve path relative to project root (app/).
    Assumes this file lives in app/ui/.
    """
    base = os.path.dirname(os.path.dirname(__file__))  # ui → app
    return os.path.join(base, relative_path)


def resource_path(relative_path: str) -> str:
    """
    PyInstaller-safe path resolver.
    Uses sys._MEIPASS when running from a bundled EXE.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return resource_path_dev(relative_path)


class MiniKeyboard(QtWidgets.QFrame):
    """
    Floating mini on-screen keyboard.

    - Emits keyPressed(str) for each key.
    - Draggable by clicking/dragging the background.
    - PNG overlay is visual only (mouse-transparent).
    - Positioning (docking) is handled by the main window.
    """

    keyPressed = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Track whether the user has manually moved the keyboard
        self.user_moved = False

        # Load overlay image (works in dev and PyInstaller)
        self.image_path = resource_path("banners/NovaTurn_OSK.png")

        self.overlay = QtWidgets.QLabel(self)
        self.overlay.setPixmap(QtGui.QPixmap(self.image_path))
        self.overlay.setScaledContents(True)
        self.overlay.setGeometry(self.rect())
        self.overlay.lower()

        # Let mouse events pass through the overlay to the buttons
        self.overlay.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

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

        # Letter/number rows
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

    # ----- Drag handling -----

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.buttons() & QtCore.Qt.LeftButton:
            self.user_moved = True
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    # ----- Keep overlay covering the whole keyboard -----

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        if hasattr(self, "overlay"):
            self.overlay.setGeometry(self.rect())

    # ----- Block physical keyboard input when OSK has focus -----

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        # Prevent physical keyboard from doing anything while OSK has focus
        event.accept()
=======
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import os


def resource_path_dev(relative_path: str) -> str:
    """
    Dev mode: resolve path relative to project root (app/).
    Assumes this file lives in app/ui/.
    """
    base = os.path.dirname(os.path.dirname(__file__))  # ui → app
    return os.path.join(base, relative_path)


def resource_path(relative_path: str) -> str:
    """
    PyInstaller-safe path resolver.
    Uses sys._MEIPASS when running from a bundled EXE.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return resource_path_dev(relative_path)


class MiniKeyboard(QtWidgets.QFrame):
    """
    Floating mini on-screen keyboard.

    - Emits keyPressed(str) for each key.
    - Draggable by clicking/dragging the background.
    - PNG overlay is visual only (mouse-transparent).
    - Positioning (docking) is handled by the main window.
    """

    keyPressed = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Track whether the user has manually moved the keyboard
        self.user_moved = False

        # Load overlay image (works in dev and PyInstaller)
        self.image_path = resource_path("banners/NovaTurn_OSK.png")

        self.overlay = QtWidgets.QLabel(self)
        self.overlay.setPixmap(QtGui.QPixmap(self.image_path))
        self.overlay.setScaledContents(True)
        self.overlay.setGeometry(self.rect())
        self.overlay.lower()

        # Let mouse events pass through the overlay to the buttons
        self.overlay.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

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

        # Letter/number rows
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

    # ----- Drag handling -----

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.buttons() & QtCore.Qt.LeftButton:
            self.user_moved = True
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    # ----- Keep overlay covering the whole keyboard -----

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        if hasattr(self, "overlay"):
            self.overlay.setGeometry(self.rect())

    # ----- Block physical keyboard input when OSK has focus -----

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        # Prevent physical keyboard from doing anything while OSK has focus
        event.accept()
>>>>>>> be9547aaccb1857afa059ff99cc82f20dba6ff7b
