<<<<<<< HEAD
# app/ui/sidebar_mixin.py
from PyQt5 import QtCore, QtGui, QtWidgets


class SidebarMixin:
    """
    Provides:
      - Sidebar frame
      - Navigation buttons
      - Sidebar expand/collapse animation
    """

    def _build_sidebar(self):
        """Creates the left sidebar and returns the sidebar widget."""
        self.sidebar = QtWidgets.QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setMinimumWidth(0)
        self.sidebar.setMaximumWidth(220)

        sidebar_layout = QtWidgets.QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(12)

        # Logo
        logo = QtWidgets.QLabel("MyPlayer")
        logo.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")

        top_row = QtWidgets.QHBoxLayout()
        top_row.addWidget(logo)
        top_row.addStretch()
        sidebar_layout.addLayout(top_row)
        sidebar_layout.addSpacing(10)

        # Navigation buttons
        def nav(text):
            btn = QtWidgets.QPushButton(text)
            btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            return btn

        self.btn_nav_home = nav("Home")
        self.btn_nav_library = nav("Library")
        self.btn_nav_now_playing = nav("Now Playing")
        self.btn_nav_stats = nav("Statistics")

        sidebar_layout.addWidget(self.btn_nav_home)
        sidebar_layout.addWidget(self.btn_nav_library)
        sidebar_layout.addWidget(self.btn_nav_now_playing)
        sidebar_layout.addWidget(self.btn_nav_stats)

        sidebar_layout.addStretch()

        return self.sidebar

    # ------------------------------------------------------------
    # Sidebar expand/collapse animation
    # ------------------------------------------------------------
    def toggle_sidebar(self):
        if hasattr(self, "_sidebar_anim") and self._sidebar_anim and \
           self._sidebar_anim.state() == QtCore.QAbstractAnimation.Running:
            return

        self._sidebar_anim = QtCore.QPropertyAnimation(self.sidebar, b"maximumWidth")
        self._sidebar_anim.setDuration(250)

        if getattr(self, "_sidebar_expanded", True):
            self._sidebar_anim.setStartValue(self.sidebar.width())
            self._sidebar_anim.setEndValue(0)
            self._sidebar_expanded = False
        else:
            self._sidebar_anim.setStartValue(self.sidebar.width())
            self._sidebar_anim.setEndValue(220)
            self._sidebar_expanded = True

        self._sidebar_anim.start()
=======
# app/ui/sidebar_mixin.py
from PyQt5 import QtCore, QtGui, QtWidgets


class SidebarMixin:
    """
    Provides:
      - Sidebar frame
      - Navigation buttons
      - Sidebar expand/collapse animation
    """

    def _build_sidebar(self):
        """Creates the left sidebar and returns the sidebar widget."""
        self.sidebar = QtWidgets.QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setMinimumWidth(0)
        self.sidebar.setMaximumWidth(220)

        sidebar_layout = QtWidgets.QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(12)

        # Logo
        logo = QtWidgets.QLabel("MyPlayer")
        logo.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")

        top_row = QtWidgets.QHBoxLayout()
        top_row.addWidget(logo)
        top_row.addStretch()
        sidebar_layout.addLayout(top_row)
        sidebar_layout.addSpacing(10)

        # Navigation buttons
        def nav(text):
            btn = QtWidgets.QPushButton(text)
            btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            return btn

        self.btn_nav_home = nav("Home")
        self.btn_nav_library = nav("Library")
        self.btn_nav_now_playing = nav("Now Playing")
        self.btn_nav_stats = nav("Statistics")

        sidebar_layout.addWidget(self.btn_nav_home)
        sidebar_layout.addWidget(self.btn_nav_library)
        sidebar_layout.addWidget(self.btn_nav_now_playing)
        sidebar_layout.addWidget(self.btn_nav_stats)

        sidebar_layout.addStretch()

        return self.sidebar

    # ------------------------------------------------------------
    # Sidebar expand/collapse animation
    # ------------------------------------------------------------
    def toggle_sidebar(self):
        if hasattr(self, "_sidebar_anim") and self._sidebar_anim and \
           self._sidebar_anim.state() == QtCore.QAbstractAnimation.Running:
            return

        self._sidebar_anim = QtCore.QPropertyAnimation(self.sidebar, b"maximumWidth")
        self._sidebar_anim.setDuration(250)

        if getattr(self, "_sidebar_expanded", True):
            self._sidebar_anim.setStartValue(self.sidebar.width())
            self._sidebar_anim.setEndValue(0)
            self._sidebar_expanded = False
        else:
            self._sidebar_anim.setStartValue(self.sidebar.width())
            self._sidebar_anim.setEndValue(220)
            self._sidebar_expanded = True

        self._sidebar_anim.start()
>>>>>>> be9547aaccb1857afa059ff99cc82f20dba6ff7b
