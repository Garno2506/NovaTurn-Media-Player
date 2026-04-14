from PyQt5 import QtCore, QtGui, QtWidgets


class TopBarMixin:
    """
    Provides the top bar for the Library page:
      - Sidebar toggle button
      - Library search bar
      - Filter dropdown
      - YouTube search bar (with icon + hover highlight)
      - Library menu button
      - Login button
    """

    def _build_topbar(self):
        """Creates and returns the top bar layout."""
        top_bar = QtWidgets.QHBoxLayout()

        # ------------------------------------------------------------
        # Sidebar toggle button
        # ------------------------------------------------------------
        self.btn_toggle_sidebar = QtWidgets.QPushButton("☰")
        self.btn_toggle_sidebar.setFixedSize(32, 32)
        self.btn_toggle_sidebar.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_toggle_sidebar.setStyleSheet("""
            QPushButton {
                background-color: #2A2A2A;
                border: none;
                color: white;
                font-size: 18px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3A3A3A;
            }
        """)
        top_bar.addWidget(self.btn_toggle_sidebar)

        # ------------------------------------------------------------
        # Library search bar
        # ------------------------------------------------------------
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Search in library…")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setFixedHeight(34)
        self.search_edit.setFixedWidth(220)
        top_bar.addWidget(self.search_edit)

        # ------------------------------------------------------------
        # Filter dropdown
        # ------------------------------------------------------------
        self.search_filter = QtWidgets.QComboBox()
        self.search_filter.addItems(["All", "Audio Only", "Video Only"])
        self.search_filter.setFixedHeight(34)
        self.search_filter.setFixedWidth(120)
        top_bar.addWidget(self.search_filter)

        top_bar.addSpacing(10)

        # ------------------------------------------------------------
        # YouTube search bar (with icon + hover highlight)
        # ------------------------------------------------------------
        youtube_container = QtWidgets.QWidget()
        yt_layout = QtWidgets.QHBoxLayout(youtube_container)
        yt_layout.setContentsMargins(0, 0, 0, 0)
        yt_layout.setSpacing(4)

        self.youtube_search = QtWidgets.QLineEdit()
        self.youtube_search.setPlaceholderText("Search YouTube…")
        self.youtube_search.setFixedHeight(34)
        self.youtube_search.setFixedWidth(300)

        # Create themed search icon
        pixmap = QtGui.QPixmap(24, 24)
        pixmap.fill(QtCore.Qt.transparent)

        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtGui.QPen(QtGui.QColor("#1DB954"), 2))
        painter.drawEllipse(4, 4, 14, 14)
        painter.drawLine(15, 15, 20, 20)
        painter.end()

        search_icon = QtGui.QIcon(pixmap)

        # Add icon inside the search bar
        action = self.youtube_search.addAction(search_icon, QtWidgets.QLineEdit.TrailingPosition)

        # Hover highlight effect
        def highlight_icon(enter):
            color = "#1ED760" if enter else "#1DB954"
            pix = QtGui.QPixmap(24, 24)
            pix.fill(QtCore.Qt.transparent)
            p = QtGui.QPainter(pix)
            p.setRenderHint(QtGui.QPainter.Antialiasing)
            p.setPen(QtGui.QPen(QtGui.QColor(color), 2))
            p.drawEllipse(4, 4, 14, 14)
            p.drawLine(15, 15, 20, 20)
            p.end()
            action.setIcon(QtGui.QIcon(pix))

        # Local event filter for hover
        def youtube_event_filter(obj, event):
            if obj == self.youtube_search:
                if event.type() == QtCore.QEvent.Enter:
                    highlight_icon(True)
                elif event.type() == QtCore.QEvent.Leave:
                    highlight_icon(False)
            return False

        # Store reference so MediaPlayer.eventFilter can call it
        self._youtube_event_filter = youtube_event_filter
        self.youtube_search.installEventFilter(self)

        # Clicking the icon triggers the search
        action.triggered.connect(lambda: self.on_youtube_search_clicked())

        yt_layout.addWidget(self.youtube_search)

        # Shift the whole YouTube search area RIGHT by ~62px
        yt_layout.addSpacing(62)

        top_bar.addWidget(youtube_container)

        # ------------------------------------------------------------
        # Right‑side buttons
        # ------------------------------------------------------------
        top_bar.addStretch()

        self.menu_button = QtWidgets.QPushButton("Library ▾")
        self.menu_button.setFixedHeight(34)
        top_bar.addWidget(self.menu_button)

        self.login_button = QtWidgets.QPushButton("Login")
        self.login_button.setFixedHeight(34)
        top_bar.addWidget(self.login_button)

        return top_bar


