# help_page.py
from PyQt5 import QtWidgets, QtGui, QtCore
from app.help_text import HELP_COL1, HELP_COL2, HELP_COL3


# ---------------------------------------------------------
# Premium Draggable On‑Screen Keyboard for Help Page
# ---------------------------------------------------------
class HelpPageOSK(QtWidgets.QFrame):
    keyPressed = QtCore.pyqtSignal(str)   # emits characters to parent

    def __init__(self, parent=None):
        super().__init__(parent)

        # -------------------------------
        # Window style
        # -------------------------------
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E;
                border-radius: 10px;
            }
            QPushButton {
                background-color: #2A2A2A;
                color: #E0E0E0;
                border: 1px solid #444;
                border-radius: 8px;
                font-size: 16px;
                padding: 6px;
            }
            QPushButton:pressed {
                background-color: #3A3A3A;
            }
        """)

        # Soft drop shadow
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(QtGui.QColor(0, 0, 0, 180))
        self.setGraphicsEffect(shadow)

        # -------------------------------
        # Draggable state
        # -------------------------------
        self._drag_active = False
        self._drag_pos = QtCore.QPoint()

        # -------------------------------
        # Layout
        # -------------------------------
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        layout.setAlignment(QtCore.Qt.AlignCenter)

        # Key rows
        row1 = "Q W E R T Y U I O P".split()
        row2 = "A S D F G H J K L".split()
        row3 = ["Shift", "Z", "X", "C", "V", "B", "N", "M", "Back"]
        row4 = ["Space", "Enter"]

        layout.addLayout(self._make_row(row1))
        layout.addLayout(self._make_row(row2))
        layout.addLayout(self._make_row(row3))
        layout.addLayout(self._make_row(row4, big_space=True))

        # Shift state
        self.shift_on = False

        # Default size
        self.setFixedHeight(260)
        self.setFixedWidth(700)

    # ---------------------------------------------------------
    # Create a row of keys
    # ---------------------------------------------------------
    def _make_row(self, keys, big_space=False):
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(8)

        for key in keys:
            btn = QtWidgets.QPushButton(key)
            btn.setFixedHeight(48)

            if key == "Space":
                btn.setFixedWidth(300)
            elif key == "Enter":
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1DB954;
                        color: black;
                        border-radius: 8px;
                        font-weight: bold;
                    }
                    QPushButton:pressed {
                        background-color: #17a74a;
                    }
                """)
                btn.setFixedWidth(120)
            else:
                btn.setFixedWidth(48)

            btn.clicked.connect(lambda _, k=key: self._handle_key(k))
            row.addWidget(btn)

        return row

    # ---------------------------------------------------------
    # Key handling
    # ---------------------------------------------------------
    def _handle_key(self, key):
        if key == "Back":
            self.keyPressed.emit("BACKSPACE")
            return

        if key == "Enter":
            self.keyPressed.emit("ENTER")
            return

        if key == "Space":
            self.keyPressed.emit(" ")
            return

        if key == "Shift":
            self.shift_on = not self.shift_on
            return

        # Normal character
        char = key.upper() if self.shift_on else key.lower()
        self.keyPressed.emit(char)

    # ---------------------------------------------------------
    # Draggable behavior
    # ---------------------------------------------------------
    def mousePressEvent(self, event):
        self._drag_active = True
        self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_active:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_active = False
        event.accept()

# ---------------------------------------------------------
# Custom QLineEdit (OSK-friendly)
# ---------------------------------------------------------
class OSKLineEdit(QtWidgets.QLineEdit):
    enterPressed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self.setAttribute(QtCore.Qt.WA_InputMethodEnabled, True)
        self.setAttribute(QtCore.Qt.WA_AcceptTouchEvents, True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def mousePressEvent(self, event):
        QtCore.QTimer.singleShot(0, self._open_osk)
        super().mousePressEvent(event)

    def _open_osk(self):
        try:
            import comtypes.client
            tip = comtypes.client.CreateObject("TextInputPanel.TextInputPanel")
            hwnd = int(self.window().winId())
            tip.AttachedEditWindow = hwnd
            tip.Show()
            return
        except Exception:
            pass

        try:
            QtCore.QProcess.startDetached(
                r"C:\Program Files\Common Files\Microsoft Shared\ink\TabTip.exe"
            )
        except Exception:
            pass

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            self.enterPressed.emit()
        super().keyPressEvent(event)


# ---------------------------------------------------------
# Help Page
# ---------------------------------------------------------
class HelpPage(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(QtCore.Qt.WA_InputMethodEnabled, True)
        self.setAttribute(QtCore.Qt.WA_AcceptTouchEvents, True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.current_column = 0
        self._help_matches = []
        self._help_match_index = -1

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(20)

        # ---------------------------------------------------------
        # Title
        # ---------------------------------------------------------
        title = QtWidgets.QLabel("Help & Instructions")
        title.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        main_layout.addWidget(title)

        # ---------------------------------------------------------
        # Row 1 — Search bar
        # ---------------------------------------------------------
        self.help_search = OSKLineEdit()
        self.help_search.setPlaceholderText("Search help text… (Enter = next match)")
        main_layout.addWidget(self.help_search)

        # ---------------------------------------------------------
        # Row — Open Keyboard + Clear (tight, left‑aligned)
        # ---------------------------------------------------------
        # ---------------------------------------------------------
        # Row — Open Keyboard + Clear (tight, left‑aligned)
        # ---------------------------------------------------------
        # ---------------------------------------------------------
        # Row — Open Keyboard + Clear (tight, left‑aligned)
        # ---------------------------------------------------------
        # ---------------------------------------------------------
        # Row — Open Keyboard + Clear (manual control)
        # ---------------------------------------------------------
        button_container = QtWidgets.QWidget()
        button_container.setFixedWidth(260)   # <<< YOU CAN CHANGE THIS
        button_row = QtWidgets.QHBoxLayout(button_container)
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(6)

        self.osk_button = QtWidgets.QPushButton("Open Keyboard")
        self.osk_button.setFixedHeight(36)
        self.osk_button.clicked.connect(self._toggle_osk)

        self.help_clear_btn = QtWidgets.QPushButton("Clear")
        self.help_clear_btn.setFixedHeight(32)

        button_row.addWidget(self.osk_button)
        button_row.addWidget(self.help_clear_btn)

        # Add the container to the main layout (LEFT aligned)
        main_layout.addWidget(button_container, alignment=QtCore.Qt.AlignLeft)





        # ---------------------------------------------------------
        # Row 4 — Match counters
        # ---------------------------------------------------------
        self.help_match_label = QtWidgets.QLabel("0 matches")
        self.help_match_label.setStyleSheet("color: #888; font-size: 12px;")
        main_layout.addWidget(self.help_match_label)

        self.help_position_label = QtWidgets.QLabel("")
        self.help_position_label.setStyleSheet("color: #888; font-size: 12px;")
        main_layout.addWidget(self.help_position_label)

        # ---------------------------------------------------------
        # Row 5 — Radio buttons centered above columns
        # ---------------------------------------------------------
        rb_row = QtWidgets.QHBoxLayout()
        rb_row.setSpacing(40)

        rb_row.addStretch()

        self.rb_col1 = QtWidgets.QRadioButton("Search Column 1")
        self.rb_col2 = QtWidgets.QRadioButton("Search Column 2")
        self.rb_col3 = QtWidgets.QRadioButton("Search Column 3")
        self.rb_col1.setChecked(True)

        for rb in (self.rb_col1, self.rb_col2, self.rb_col3):
            rb.setStyleSheet("color: white; font-size: 12px;")
            rb.setFocusPolicy(QtCore.Qt.NoFocus)

        rb_row.addWidget(self.rb_col1)
        rb_row.addStretch()
        rb_row.addWidget(self.rb_col2)
        rb_row.addStretch()
        rb_row.addWidget(self.rb_col3)
        rb_row.addStretch()

        main_layout.addLayout(rb_row)

        # ---------------------------------------------------------
        # Row 6 — Three columns
        # ---------------------------------------------------------
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

        main_layout.addLayout(columns)
        main_layout.addStretch()

        # ---------------------------------------------------------
        # Signals
        # ---------------------------------------------------------
        self.help_search.textChanged.connect(self._run_search)
        self.help_search.enterPressed.connect(self._next_match)
        self.help_clear_btn.clicked.connect(self._clear_search)

        self.rb_col1.toggled.connect(lambda c: c and self._switch_column(0))
        self.rb_col2.toggled.connect(lambda c: c and self._switch_column(1))
        self.rb_col3.toggled.connect(lambda c: c and self._switch_column(2))
                # ---------------------------------------------------------
        # Premium Help Page OSK (initially hidden)
        # ---------------------------------------------------------
        self.help_osk = HelpPageOSK(self)
        self.help_osk.hide()
        self.help_osk.keyPressed.connect(self._handle_osk_key)



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
    # Search engine
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
            # Jump to the first match
            self._jump_to_match(0)

            # -------------------------------------------------
            # ⭐ FIX: sync index with the match we actually land on
            # -------------------------------------------------
            cursor_pos = column.textCursor().position()
            for i, pos in enumerate(self._help_matches):
                if pos == cursor_pos:
                    self._help_match_index = i
                    break
            # -------------------------------------------------

        else:
            # No matches found
            self._help_match_index = -1
            self.help_position_label.setText("")
            return

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
        cursor.select(QtGui.QTextCursor.WordUnderCursor)

        column.setTextCursor(cursor)
        column.ensureCursorVisible()

        # IMPORTANT FIX:
        # Sync internal index with the match we actually jumped to
        self._help_match_index = index

        # Update match counter
        pos_idx = index + 1
        total = len(self._help_matches)
        self.help_position_label.setText(f"Match {pos_idx} of {total}")

        # Ensure Enter works immediately
        column.setFocus()
        QtWidgets.QApplication.processEvents()



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

    # ---------------------------------------------------------
    # Toggle OSK visibility + glowing button ring
    # ---------------------------------------------------------
    def _toggle_osk(self):
        if self.help_osk.isVisible():
            self.help_osk.hide()
            # OSK OFF style
            self.osk_button.setStyleSheet("""
                QPushButton {
                    border: 2px solid #444;
                    border-radius: 6px;
                    color: white;
                    background-color: #222;
                }
                QPushButton:pressed {
                    background-color: #333;
                }
            """)
        else:
            # Position at bottom center
            parent_rect = self.rect()
            osk_width = self.help_osk.width()
            osk_height = self.help_osk.height()
            x = (parent_rect.width() - osk_width) // 2
            y = parent_rect.height() - osk_height - 20
            self.help_osk.move(self.mapToGlobal(QtCore.QPoint(x, y)))

            self.help_osk.show()
            self.help_osk.raise_()

            # OSK ON style (green ring)
            self.osk_button.setStyleSheet("""
                QPushButton {
                    border: 2px solid #1DB954;
                    border-radius: 6px;
                    color: white;
                    background-color: #222;
                }
                QPushButton:pressed {
                    background-color: #333;
                }
            """)


    # ---------------------------------------------------------
    # Handle keys coming from HelpPageOSK
    # ---------------------------------------------------------
    def _handle_osk_key(self, key):
        edit = self.help_search

        if key == "BACKSPACE":
            cursor_pos = edit.cursorPosition()
            if cursor_pos > 0:
                text = edit.text()
                text = text[:cursor_pos - 1] + text[cursor_pos:]
                edit.setText(text)
                edit.setCursorPosition(cursor_pos - 1)
            return

        if key == "ENTER":
            self._next_match()
            return

        # Normal character
        cursor_pos = edit.cursorPosition()
        text = edit.text()
        text = text[:cursor_pos] + key + text[cursor_pos:]
        edit.setText(text)
        edit.setCursorPosition(cursor_pos + len(key))


    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.help_osk.isVisible():
            parent_rect = self.rect()
            osk_width = self.help_osk.width()
            osk_height = self.help_osk.height()
            x = (parent_rect.width() - osk_width) // 2
            y = parent_rect.height() - osk_height - 20
            self.help_osk.move(self.mapToGlobal(QtCore.QPoint(x, y)))

