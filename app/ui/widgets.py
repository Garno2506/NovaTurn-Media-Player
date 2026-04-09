<<<<<<< HEAD
# app/ui/widgets.py
from PyQt5 import QtCore, QtGui, QtWidgets
import random

class VideoWidget(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Force a real native window for VLC
        self.setAttribute(QtCore.Qt.WA_NativeWindow, True)
        self.setAttribute(QtCore.Qt.WA_DontCreateNativeAncestors, True)

        self.setObjectName("videoWidget")
        self.setStyleSheet("background-color: black;")

    def get_handle(self):
        """Return the native window handle (HWND on Windows)."""
        return int(self.winId())


class EqualizerWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, bars=12):
        super().__init__(parent)
        self.bars = bars
        self.levels = [0.0] * bars
        self.setMinimumHeight(24)
        self.setMaximumHeight(32)

    def set_levels(self, levels):
        self.levels = levels[:self.bars] + [0.0] * max(0, self.bars - len(levels))
        self.update()

    def randomize_levels(self, intensity=1.0):
        self.levels = [random.random() * intensity for _ in range(self.bars)]
        self.update()

    def clear_levels(self):
        self.levels = [0.0] * self.bars
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        rect = self.rect()
        bar_width = max(2, rect.width() // (self.bars * 2))
        gap = bar_width
        max_height = rect.height()

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor("#00F0FF"))

        x = gap // 2
        for level in self.levels:
            h = int(max_height * level)
            y = rect.bottom() - h
            painter.drawRect(QtCore.QRect(x, y, bar_width, h))
            x += bar_width + gap

        painter.end()
=======
# app/ui/widgets.py
from PyQt5 import QtCore, QtGui, QtWidgets
import random

class VideoWidget(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Force a real native window for VLC
        self.setAttribute(QtCore.Qt.WA_NativeWindow, True)
        self.setAttribute(QtCore.Qt.WA_DontCreateNativeAncestors, True)

        self.setObjectName("videoWidget")
        self.setStyleSheet("background-color: black;")

    def get_handle(self):
        """Return the native window handle (HWND on Windows)."""
        return int(self.winId())


class EqualizerWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, bars=12):
        super().__init__(parent)
        self.bars = bars
        self.levels = [0.0] * bars
        self.setMinimumHeight(24)
        self.setMaximumHeight(32)

    def set_levels(self, levels):
        self.levels = levels[:self.bars] + [0.0] * max(0, self.bars - len(levels))
        self.update()

    def randomize_levels(self, intensity=1.0):
        self.levels = [random.random() * intensity for _ in range(self.bars)]
        self.update()

    def clear_levels(self):
        self.levels = [0.0] * self.bars
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        rect = self.rect()
        bar_width = max(2, rect.width() // (self.bars * 2))
        gap = bar_width
        max_height = rect.height()

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor("#00F0FF"))

        x = gap // 2
        for level in self.levels:
            h = int(max_height * level)
            y = rect.bottom() - h
            painter.drawRect(QtCore.QRect(x, y, bar_width, h))
            x += bar_width + gap

        painter.end()
>>>>>>> be9547aaccb1857afa059ff99cc82f20dba6ff7b
