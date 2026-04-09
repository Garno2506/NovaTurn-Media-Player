<<<<<<< HEAD
from PyQt5 import QtWidgets

class StylesMixin:
    def _apply_stylesheet(self):
        self.setStyleSheet(
            """
            QFrame, QLabel, QPushButton, QLineEdit, QTableWidget, QListWidget,
            QSlider, QProgressBar {
                background-color: #121212;
                color: #FFFFFF;
                font-family: Segoe UI, sans-serif;
            }

            #sidebar {
                background-color: #000000;
                border-right: 1px solid #202020;
            }
            #toggleSidebar {
                background-color: #181818;
                border-radius: 4px;
                color: #B3B3B3;
                border: 1px solid #333;
                font-size: 14px;
            }
            #toggleSidebar:hover {
                background-color: #262626;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: #B3B3B3;
                padding: 6px 10px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1A1A1A;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #1DB954;
                color: #000000;
            }
            #pillButton {
                background-color: #181818;
                border-radius: 4px;
                border: 1px solid #333;
                padding: 4px 10px;
                color: #B3B3B3;
                font-size: 13px;
            }
            #pillButton:hover {
                border-color: #1DB954;
                color: #FFFFFF;
            }
            QLineEdit {
                background-color: #2A2A2A;
                border-radius: 4px;
                padding: 6px 14px;
                color: #FFFFFF;
                border: 1px solid #3A3A3A;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #1DB954;
            }
            QTableWidget {
                background-color: #121212;
                alternate-background-color: #181818;
                color: #FFFFFF;
                gridline-color: #222222;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #181818;
                color: #B3B3B3;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #1DB954;
                color: #000000;
            }
            QListWidget {
                background-color: #121212;
                border: 1px solid #333;
                color: #FFFFFF;
                font-size: 13px;
            }
            QListWidget::item:selected {
                background-color: #1DB954;
                color: #000000;
            }
            QSlider::groove:horizontal {
                height: 1px;
                background: #1a1a1a;
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #00F0FF;
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #00F0FF;
                border-radius: 5px;
            }
            QProgressBar {
                background-color: #1A1A1A;
                border-radius: 8px;
                border: 8px solid #333;
            }
            QProgressBar::chunk {
                background-color: #00F0FF;
                border-radius: 8px;
            }
            #videoWidget {
                background-color: #000000;
                border: 2px solid #D0D0D0;
                border-radius: 6px;
            }
            #recentCard {
                background-color: #181818;
                border-radius: 8px;
                border: 1px solid #333;
            }
            #recentCard:hover {
                border: 1px solid #1DB954;
            }

            /* ------------------------------------------------------------
               Artist Tree Styling
               ------------------------------------------------------------ */
            #artistTree {
                background-color: #121212;
                border: 1px solid #333;
                font-size: 14px;
                color: #FFFFFF;
            }
            #artistTree::item {
                height: 26px;
                padding-left: 6px;
            }
            #artistTree::item:selected {
                background-color: #1DB954;
                color: #000000;
            }
            #artistTree::item:hover {
                background-color: #1A1A1A;
            }

            /* ------------------------------------------------------------
               Pill-style top item ("All Artists")
               ------------------------------------------------------------ */
            #artistTree::item:first {
                background-color: #2A2A2A;
                border: 1px solid #3A3A3A;
                border-radius: 10px;
                padding: 6px 10px;
                margin: 4px;
                color: #FFFFFF;
            }
            #artistTree::item:first:hover {
                background-color: #3A3A3A;
            }
            #artistTree::item:first:selected {
                background-color: #1DB954;
                color: #000000;
            }

            """
        )

        # ------------------------------------------------------------
        # ComboBox styling (search filter)
        # ------------------------------------------------------------
        self.search_filter.setStyleSheet(
            """
            QComboBox {
                font-size: 14px;
                background-color: #181818;
                color: #FFFFFF;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QComboBox QAbstractItemView {
                font-size: 14px;
                background-color: #181818;
                color: #FFFFFF;
                selection-background-color: #1DB954;
                selection-color: #000000;
            }
            """
        )

=======
from PyQt5 import QtWidgets

class StylesMixin:
    def _apply_stylesheet(self):
        self.setStyleSheet(
            """
            QFrame, QLabel, QPushButton, QLineEdit, QTableWidget, QListWidget,
            QSlider, QProgressBar {
                background-color: #121212;
                color: #FFFFFF;
                font-family: Segoe UI, sans-serif;
            }

            #sidebar {
                background-color: #000000;
                border-right: 1px solid #202020;
            }
            #toggleSidebar {
                background-color: #181818;
                border-radius: 4px;
                color: #B3B3B3;
                border: 1px solid #333;
                font-size: 14px;
            }
            #toggleSidebar:hover {
                background-color: #262626;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: #B3B3B3;
                padding: 6px 10px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1A1A1A;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #1DB954;
                color: #000000;
            }
            #pillButton {
                background-color: #181818;
                border-radius: 4px;
                border: 1px solid #333;
                padding: 4px 10px;
                color: #B3B3B3;
                font-size: 13px;
            }
            #pillButton:hover {
                border-color: #1DB954;
                color: #FFFFFF;
            }
            QLineEdit {
                background-color: #2A2A2A;
                border-radius: 4px;
                padding: 6px 14px;
                color: #FFFFFF;
                border: 1px solid #3A3A3A;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #1DB954;
            }
            QTableWidget {
                background-color: #121212;
                alternate-background-color: #181818;
                color: #FFFFFF;
                gridline-color: #222222;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #181818;
                color: #B3B3B3;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #1DB954;
                color: #000000;
            }
            QListWidget {
                background-color: #121212;
                border: 1px solid #333;
                color: #FFFFFF;
                font-size: 13px;
            }
            QListWidget::item:selected {
                background-color: #1DB954;
                color: #000000;
            }
            QSlider::groove:horizontal {
                height: 1px;
                background: #1a1a1a;
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #00F0FF;
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #00F0FF;
                border-radius: 5px;
            }
            QProgressBar {
                background-color: #1A1A1A;
                border-radius: 8px;
                border: 8px solid #333;
            }
            QProgressBar::chunk {
                background-color: #00F0FF;
                border-radius: 8px;
            }
            #videoWidget {
                background-color: #000000;
                border: 2px solid #D0D0D0;
                border-radius: 6px;
            }
            #recentCard {
                background-color: #181818;
                border-radius: 8px;
                border: 1px solid #333;
            }
            #recentCard:hover {
                border: 1px solid #1DB954;
            }

            /* ------------------------------------------------------------
               Artist Tree Styling
               ------------------------------------------------------------ */
            #artistTree {
                background-color: #121212;
                border: 1px solid #333;
                font-size: 14px;
                color: #FFFFFF;
            }
            #artistTree::item {
                height: 26px;
                padding-left: 6px;
            }
            #artistTree::item:selected {
                background-color: #1DB954;
                color: #000000;
            }
            #artistTree::item:hover {
                background-color: #1A1A1A;
            }

            /* ------------------------------------------------------------
               Pill-style top item ("All Artists")
               ------------------------------------------------------------ */
            #artistTree::item:first {
                background-color: #2A2A2A;
                border: 1px solid #3A3A3A;
                border-radius: 10px;
                padding: 6px 10px;
                margin: 4px;
                color: #FFFFFF;
            }
            #artistTree::item:first:hover {
                background-color: #3A3A3A;
            }
            #artistTree::item:first:selected {
                background-color: #1DB954;
                color: #000000;
            }

            """
        )

        # ------------------------------------------------------------
        # ComboBox styling (search filter)
        # ------------------------------------------------------------
        self.search_filter.setStyleSheet(
            """
            QComboBox {
                font-size: 14px;
                background-color: #181818;
                color: #FFFFFF;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QComboBox QAbstractItemView {
                font-size: 14px;
                background-color: #181818;
                color: #FFFFFF;
                selection-background-color: #1DB954;
                selection-color: #000000;
            }
            """
        )

>>>>>>> be9547aaccb1857afa059ff99cc82f20dba6ff7b
