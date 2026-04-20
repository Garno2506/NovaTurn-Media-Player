# help_page.py
from PyQt5 import QtWidgets, QtGui, QtCore
from app.help_text import HELP_COL1, HELP_COL2, HELP_COL3


class HelpPage(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

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
        # Search controls row
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

        # Clear button BEFORE search bar
        self.help_clear_btn = QtWidgets.QPushButton("Clear")
        self.help_clear_btn.setFixedHeight(32)
        search_controls.addWidget(self.help_clear_btn)

        # Search bar (QLineEdit) expands
        self.help_search = QtWidgets.QLineEdit()
        self.help_search.setPlaceholderText("Search help text… (Enter = next match)")
        self.help_search.setFixedHeight(32)
        search_controls.addWidget(self.help_search, 1)

        help_layout.addLayout(search_controls)

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
        self.help_search.textChanged.connect(self._help_search_update)
        self.help_search.returnPressed.connect(self._help_search_next)
        self.help_clear_btn.clicked.connect(self._clear_search)

        self.rb_col1.toggled.connect(lambda checked: checked and self._switch_column(0))
        self.rb_col2.toggled.connect(lambda checked: checked and self._switch_column(1))
        self.rb_col3.toggled.connect(lambda checked: checked and self._switch_column(2))

    # ---------------------------------------------------------
    # Column factory
    # ---------------------------------------------------------
    def _make_column(self):
        box = QtWidgets.QTextEdit()
        box.setReadOnly(True)
        box.setFixedHeight(300)  # roughly half-height; tweak if needed
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
        # Re-run search on the newly active column
        self._help_search_update(self.help_search.text())
        self.help_search.setFocus()

    # ============================================================
    # HELP PAGE SEARCH + HIGHLIGHT ENGINE
    # ============================================================
    def _help_get_active_editor(self):
        if self.rb_col1.isChecked():
            return self.help_col1
        if self.rb_col2.isChecked():
            return self.help_col2
        return self.help_col3

    def _help_search_update(self, text: str):
        editor = self._help_get_active_editor()

        # Clear previous highlights
        cursor = editor.textCursor()
        cursor.beginEditBlock()
        fmt = QtGui.QTextCharFormat()
        fmt.setBackground(QtCore.Qt.transparent)
        cursor.select(QtGui.QTextCursor.Document)
        cursor.setCharFormat(fmt)
        cursor.endEditBlock()

        self._help_matches = []
        self._help_match_index = -1

        text = text.strip()
        if not text:
            self.help_match_label.setText("0 matches")
            self.help_position_label.setText("")
            return

        # Full-word search (case-insensitive)
        doc_text = editor.toPlainText()
        highlight_fmt = QtGui.QTextCharFormat()
        highlight_fmt.setBackground(QtGui.QColor("#1DB954"))
        highlight_fmt.setForeground(QtGui.QColor("black"))

        cursor = editor.textCursor()
        pattern = r"\b" + text + r"\b"
        regex = QtCore.QRegExp(pattern, QtCore.Qt.CaseInsensitive)

        pos = 0
        while True:
            pos = regex.indexIn(doc_text, pos)
            if pos == -1:
                break

            cursor.setPosition(pos)
            cursor.movePosition(
                QtGui.QTextCursor.Right,
                QtGui.QTextCursor.KeepAnchor,
                len(text),
            )
            cursor.mergeCharFormat(highlight_fmt)

            self._help_matches.append(pos)
            pos += len(text)

        # Update match counter
        count = len(self._help_matches)
        if count == 0:
            self.help_match_label.setText("No matches found")
        elif count == 1:
            self.help_match_label.setText("1 match found")
        else:
            self.help_match_label.setText(f"{count} matches found")

        # Jump to first match
        if self._help_matches:
            self._help_match_index = 0
            self._help_jump_to_match()
        else:
            self._help_match_index = -1
            self.help_position_label.setText("")

    def _help_jump_to_match(self):
        if not self._help_matches:
            return

        editor = self._help_get_active_editor()
        pos = self._help_matches[self._help_match_index]

        cursor = editor.textCursor()
        cursor.setPosition(pos)
        cursor.movePosition(
            QtGui.QTextCursor.Right,
            QtGui.QTextCursor.KeepAnchor,
            len(self.help_search.text().strip()),
        )
        editor.setTextCursor(cursor)
        editor.ensureCursorVisible()

        # Update "Match X of Y"
        pos_idx = self._help_match_index + 1
        total = len(self._help_matches)
        self.help_position_label.setText(f"Match {pos_idx} of {total}")

    def _help_search_next(self):
        if not self._help_matches:
            return

        self._help_match_index += 1
        if self._help_match_index >= len(self._help_matches):
            self._help_match_index = 0

        self._help_jump_to_match()

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

        # Remove background formatting
            cursor.beginEditBlock()
            fmt = QtGui.QTextCharFormat()
            fmt.setBackground(QtCore.Qt.transparent)
            cursor.select(QtGui.QTextCursor.Document)
            cursor.setCharFormat(fmt)
            cursor.endEditBlock()

        # IMPORTANT: clear the active selection (white highlight)
            cursor.clearSelection()
            col.setTextCursor(cursor)


    def reset_page(self):
        """Clear everything when leaving the Help page."""
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
