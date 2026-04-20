# help_page.py
from PyQt5 import QtWidgets, QtGui, QtCore
from app.help_text import HELP_COL1, HELP_COL2, HELP_COL3


# ---------------------------------------------------------
# Custom QLineEdit (OSK-friendly)
# ---------------------------------------------------------
class OSKLineEdit(QtWidgets.QLineEdit):
    enterPressed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)

        # SAFE + REQUIRED for Windows touch keyboard
        self.setAttribute(QtCore.Qt.WA_InputMethodEnabled, True)
        self.setAttribute(QtCore.Qt.WA_AcceptTouchEvents, True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            self.enterPressed.emit()
        super().keyPressEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        QtCore.QTimer.singleShot(0, self._open_osk)

    def _open_osk(self):
        try:
            QtCore.QProcess.startDetached(
                r"C:\Program Files\Common Files\Microsoft Shared\ink\TabTip.exe"
            )
            import ctypes
            HWND = ctypes.windll.user32.GetForegroundWindow()
            ctypes.windll.user32.PostMessageW(HWND, 0x0501, 0, 0)
        except Exception:
            pass




class HelpPage(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Enable touch + IME for Windows touch keyboard
        self.setAttribute(QtCore.Qt.WA_InputMethodEnabled, True)
        self.setAttribute(QtCore.Qt.WA_AcceptTouchEvents, True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # -----------------------------
        # Internal state
        # -----------------------------
        self.current_column = 0
        self._help_matches = []
        self._help_match_index = -1


        # -----------------------------
        # Root layout
        # -----------------------------
        help_layout = QtWidgets.QVBoxLayout(self)
        help_layout.setContentsMargins(32, 32, 32, 32)
        help_layout.setSpacing(24)

        help_title = QtWidgets.QLabel("Help & Instructions")
        help_title.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        help_layout.addWidget(help_title)

        # -----------------------------
        # Search controls row (radios + clear)
        # -----------------------------
        search_controls = QtWidgets.QHBoxLayout()
        search_controls.setSpacing(20)

        self.rb_col1 = QtWidgets.QRadioButton("Search Column 1")
        self.rb_col2 = QtWidgets.QRadioButton("Search Column 2")
        self.rb_col3 = QtWidgets.QRadioButton("Search Column 3")
        self.rb_col1.setChecked(True)

        rb_style = "color: white; font-size: 12px;"
        self.rb_col1.setStyleSheet(rb_style)
        self.rb_col2.setStyleSheet(rb_style)
        self.rb_col3.setStyleSheet(rb_style)

        search_controls.addWidget(self.rb_col1)
        search_controls.addWidget(self.rb_col2)
        search_controls.addWidget(self.rb_col3)

        # Clear button
        self.help_clear_btn = QtWidgets.QPushButton("Clear")
        self.help_clear_btn.setFixedHeight(32)
        search_controls.addWidget(self.help_clear_btn)

        # Add the controls row to the layout
        help_layout.addLayout(search_controls)

        # -----------------------------
        # Search bar row (search bar alone)
        # -----------------------------
        search_bar_row = QtWidgets.QHBoxLayout()
        search_bar_row.setSpacing(20)

        self.help_search = OSKLineEdit()
        self.help_search.setPlaceholderText("Search help text… (Enter = next match)")
        search_bar_row.addWidget(self.help_search)

        # Add the search bar row to the layout
        help_layout.addLayout(search_bar_row)

        # -----------------------------
        # Match labels
        # -----------------------------
        self.help_match_label = QtWidgets.QLabel("0 matches")
        self.help_match_label.setStyleSheet("color: #888; font-size: 12px;")
        help_layout.addWidget(self.help_match_label)

        self.help_position_label = QtWidgets.QLabel("")
        self.help_position_label.setStyleSheet("color: #888; font-size: 12px;")
        help_layout.addWidget(self.help_position_label)

        # -----------------------------
        # Three-column help layout
        # -----------------------------
        columns = QtWidgets.QHBoxLayout()
        columns.setSpacing(24)

        self.help_col1 = self._make_column()
        self.help_col2 = self._make_column()
        self.help_col3 = self._make_column()

        self.help_col1.setHtml(HELP_COL1)
        self.help_col2.setHtml(HELP_COL2)
        self.help_col3.setHtml(HELP_COL3)

        columns.addWidget(self.help_col1)
        columns.addWidget(self.help_col2)
        columns.addWidget(self.help_col3)

        help_layout.addLayout(columns)
        help_layout.addStretch()

        # -----------------------------
        # Signals
        # -----------------------------
        self.help_search.textChanged.connect(self._run_search)
        self.help_search.enterPressed.connect(self._next_match)
        self.help_clear_btn.clicked.connect(self._clear_search)

        self.rb_col1.toggled.connect(lambda checked: checked and self._switch_column(0))
        self.rb_col2.toggled.connect(lambda checked: checked and self._switch_column(1))
        self.rb_col3.toggled.connect(lambda checked: checked and self._switch_column(2))

    # ---------------------------------------------------------
    # Column factory
    # ---------------------------------------------------------
    def _make_column(self):
        box = QtWidgets.QTextBrowser()
        box.setOpenExternalLinks(True)
        box.setFixedHeight(300)
        box.setStyleSheet(
            "font-size: 16px; color: #E0E0E0; background-color: #1E1E1E;"
        )
        box.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        return box

    # ---------------------------------------------------------
    # Column switching
    # ---------------------------------------------------------
    def _switch_column(self, index):
        self.current_column = index
        self._scroll_all_to_top()
        self._run_search()
        self.help_search.setFocus()

    # ---------------------------------------------------------
    # Search engine (stable doc.find version)
    # ---------------------------------------------------------
    def _run_search(self):
        text = self.help_search.text().strip()
        self._clear_highlights()

        if not text:
            self._help_matches = []
            self._help_match_index = -1
            self.help_match_label.setText("0 matches")
            self.help_position_label.setText("")
            return

        column = self._get_current_column()
        doc = column.document()

        cursor = QtGui.QTextCursor(doc)
        highlight_format = QtGui.QTextCharFormat()
        highlight_format.setBackground(QtGui.QColor("#1DB954"))
        highlight_format.setForeground(QtGui.QColor("black"))

        self._help_matches = []

        while True:
            cursor = doc.find(text, cursor)
            if cursor.isNull():
                break
            self._help_matches.append(cursor.selectionStart())
            cursor.mergeCharFormat(highlight_format)

        count = len(self._help_matches)
        if count == 0:
            self.help_match_label.setText("No matches found")
        elif count == 1:
            self.help_match_label.setText("1 match found")
        else:
            self.help_match_label.setText(f"{count} matches found")

        if self._help_matches:
            self._help_match_index = 0
            self._jump_to_match(0)
        else:
            self._help_match_index = -1
            self.help_position_label.setText("")

    # ---------------------------------------------------------
    # Jump to next match
    # ---------------------------------------------------------
    def _next_match(self):
        if not self._help_matches:
            return

        self._help_match_index = (self._help_match_index + 1) % len(self._help_matches)
        self._jump_to_match(self._help_match_index)

    # ---------------------------------------------------------
    # Jump helper
    # ---------------------------------------------------------
    def _jump_to_match(self, index):
        column = self._get_current_column()
        doc = column.document()

        cursor = QtGui.QTextCursor(doc)
        cursor.setPosition(self._help_matches[index])
        column.setTextCursor(cursor)
        column.ensureCursorVisible()

        pos_idx = index + 1
        total = len(self._help_matches)
        self.help_position_label.setText(f"Match {pos_idx} of {total}")

    # ---------------------------------------------------------
    # Clear search
    # ---------------------------------------------------------
    def _clear_search(self):
        self.help_search.clear()
        self._clear_highlights()
        self._scroll_all_to_top()
        self._help_matches = []
        self._help_match_index = -1
        self.help_match_label.setText("0 matches")
        self.help_position_label.setText("")
        self.help_search.setFocus()

    # ---------------------------------------------------------
    # Highlight clearing
    # ---------------------------------------------------------
    def _clear_highlights(self):
        for col in (self.help_col1, self.help_col2, self.help_col3):
            doc = col.document()
            cursor = QtGui.QTextCursor(doc)
            cursor.beginEditBlock()
            fmt = QtGui.QTextCharFormat()
            fmt.setBackground(QtCore.Qt.transparent)
            cursor.select(QtGui.QTextCursor.Document)
            cursor.setCharFormat(fmt)
            cursor.endEditBlock()
            cursor.clearSelection()
            col.setTextCursor(cursor)

    def reset_page(self):
        self.help_search.clear()
        self._clear_highlights()
        self._scroll_all_to_top()
        self._help_matches = []
        self._help_match_index = -1
        self.help_match_label.setText("0 matches")
        self.help_position_label.setText("")

    # ---------------------------------------------------------
    # Utility
    # ---------------------------------------------------------
    def _get_current_column(self):
        return [self.help_col1, self.help_col2, self.help_col3][self.current_column]

    def _scroll_all_to_top(self):
        self.help_col1.verticalScrollBar().setValue(0)
        self.help_col2.verticalScrollBar().setValue(0)
        self.help_col3.verticalScrollBar().setValue(0)

