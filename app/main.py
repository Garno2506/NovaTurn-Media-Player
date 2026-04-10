import sys
import os
import random
import platform
import webbrowser
import subprocess
import shutil
import time
import json
import csv
import hashlib
import hmac
import ctypes
from pathlib import Path

# ============================================================
#   UNIVERSAL RESOURCE LOADER — FINAL, FROZEN VERSION
# ============================================================

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        # Running in PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in dev mode
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# ============================================================
#   VLC BOOTSTRAP — FINAL, STABLE, PYINSTALLER-SAFE
#   WARNING DO NOT MOVE OR ALTER ANYTHING TO DO WITH VLC IN THIS SCRIPT IT WILL BRAKE THE APP
# ============================================================

def get_vlc_folder():
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "vlc"
    return Path(__file__).resolve().parent / "vlc"

vlc_folder = get_vlc_folder()
plugins_folder = vlc_folder / "plugins"

# Tell python-vlc EXACTLY where libvlc.dll is
os.environ["PYTHON_VLC_LIB_PATH"] = str(vlc_folder / "libvlc.dll")

# Tell VLC where its plugins are
os.environ["VLC_PLUGIN_PATH"] = str(plugins_folder)

# Ensure Windows can load VLC DLLs
try:
    os.add_dll_directory(str(vlc_folder))
except Exception:
    os.environ["PATH"] = str(vlc_folder) + os.pathsep + os.environ.get("PATH", "")

import vlc

# ============================================================
#  END VLC BOOTSTRAP
#  DO NOT MOVE OR ALTER ANYTHING TO DO WITH VLC IN THIS SCRIPT IT WILL BRAKE THE APP
# ============================================================

# Lazy VLC loader — safe, does NOT move or alter bootstrap
_vlc = None

def get_vlc():
    global _vlc
    if _vlc is None:
        import vlc
        _vlc = vlc
    return _vlc



from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtChart import (
    QChart,
    QChartView,
    QPieSeries,
    QBarSeries,
    QBarSet,
    QBarCategoryAxis,
    QValueAxis,
)
from mutagen import File as MutagenFile
import requests

from app.db import MediaDatabase, format_duration, is_video_file
from app.helpers import enable_windows_blur, load_album_art, add_to_recently_played
from app.password_manager import PasswordManager
from app.ui.widgets import VideoWidget, EqualizerWidget
from app.ui.stylesheet_mixin import StylesMixin
from app.ui.dialogs import DialogsMixin
from app.ui.osk import MiniKeyboard
from PyQt5 import QtWidgets, QtGui, QtCore
from app.ui.osk_final import MiniKeyboard


# ------------------------------------------------------------
# Pill-style delegate for "All Artists"
# ------------------------------------------------------------
class PillDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter, option, index):
        if index.data(QtCore.Qt.UserRole) == "pill":
            rect = option.rect.adjusted(4, 4, -4, -4)

            # Hover
            if option.state & QtWidgets.QStyle.State_MouseOver:
                color = QtGui.QColor("#3A3A3A")
            else:
                color = QtGui.QColor("#2A2A2A")

            # Pressed / selected
            if option.state & QtWidgets.QStyle.State_Selected:
                color = QtGui.QColor("#1DB954")

            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setBrush(color)
            painter.setPen(QtGui.QColor("#3A3A3A"))
            painter.drawRoundedRect(rect, 10, 10)

        super().paint(painter, option, index)

# Windows-only COM support placeholder (no longer used for CD)
if platform.system() == "Windows":
    try:
        import win32com.client  # kept only if you use it elsewhere later
    except ImportError:
        win32com = None
else:
    win32com = None


# ============================================================
#   MEDIAPLAYER INIT + GLOBAL PATCHES (UPDATED)
# ============================================================

class MediaPlayer(DialogsMixin, StylesMixin, QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            QtCore.Qt.Window
            | QtCore.Qt.WindowMinimizeButtonHint
            | QtCore.Qt.WindowMaximizeButtonHint
            | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowTitle("NovaTurn Media Player. By Michael Garnett")
        self.resize(1280, 760)

        # VLC
        # DO NOT MOVE OR ALTER ANYTHING TO DO WITH VLC IN THIS SCRIPT IT WILL BRAKE THE APP
        self.instance = None
        self.player = None
        self._pre_mute_volume = 40

        # DB + password
        self.db = MediaDatabase()
        self.password_manager = PasswordManager()

        # Playback state
        self.ensure_vlc()
        self.current_playlist = []
        self.current_index = -1
        self.is_shuffle = False
        self.is_repeat = False
        self.user_is_seeking = False

        # Queue
        self.user_queue = []

        # Sidebar
        self._sidebar_expanded = True
        self._sidebar_anim = None

        # Time mode
        self.show_remaining = True

        # Admin
        self.is_admin = False

        # Auto-radio
        self.last_active_time = time.time()
        self.auto_radio_enabled = True

        # Mute state
        self.is_muted = False
        self.youtube_muted = False

        # YouTube auto-pause
        self.youtube_active = False

        # 5-second gap
        self.gap_active = False
        self.gap_start_time = 0.0

        # Trash / undo
        self.trash = []
        self.last_deleted_batch = []

        # Artist filter
        self.current_artist_filter = None

        # Build UI first
        self._build_ui()
        self._apply_stylesheet()
        self._create_protected_menu()

        # Load data AFTER UI exists
        self._load_library()
        self._load_recently_played()

        # VLC events
        # DO NOT MOVE OR ALTER ANYTHING TO DO WITH VLC IN THIS SCRIPT IT WILL BRAKE THE APP
        self._attach_vlc_events()

        # Timers
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start()

        self.eq_timer = QtCore.QTimer(self)
        self.eq_timer.setInterval(80)
        self.eq_timer.timeout.connect(self._update_equalizer)
        self.eq_timer.start()

        # Connect signals LAST
        self._connect_signals()
        self.position_slider.installEventFilter(self)
        self.search_edit.installEventFilter(self)
        self.youtube_search.installEventFilter(self)

    # ------------------------------------------------------------
    # Attach VLC events
    # DO NOT MOVE OR ALTER ANYTHING TO DO WITH VLC IN THIS SCRIPT IT WILL BRAKE THE APP
    # ------------------------------------------------------------
    def _attach_vlc_events(self):
        em = self.player.event_manager()
        em.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end_reached)

    def _on_end_reached(self, event):
        # Start 5-second gap before next track
        self.gap_active = True
        self.gap_start_time = time.time()

    def ensure_vlc(self):
        if self.instance is None:
            vlc = get_vlc()
            self.instance = vlc.Instance("--aout=directsound")
            self.player = self.instance.media_player_new()
            self.player.audio_set_volume(self._pre_mute_volume)




# ============================================================
#  CHUNK B — FULL UI BUILD + STYLESHEET (FINAL FIXED VERSION)
# ============================================================

    def toggle_sidebar(self):
        if self._sidebar_anim and self._sidebar_anim.state() == QtCore.QAbstractAnimation.Running:
            return

        self._sidebar_anim = QtCore.QPropertyAnimation(self.sidebar, b"maximumWidth")
        self._sidebar_anim.setDuration(250)

        if self._sidebar_expanded:
            self._sidebar_anim.setStartValue(self.sidebar.width())
            self._sidebar_anim.setEndValue(0)
            self._sidebar_expanded = False
        else:
            self._sidebar_anim.setStartValue(self.sidebar.width())
            self._sidebar_anim.setEndValue(220)
            self._sidebar_expanded = True

        self._sidebar_anim.start()

    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        root = QtWidgets.QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---------------- Sidebar ----------------
        self.sidebar = QtWidgets.QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setMinimumWidth(0)
        self.sidebar.setMaximumWidth(220)

        sidebar_layout = QtWidgets.QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(12)

        logo = QtWidgets.QLabel("NovaTurn")
        logo.setStyleSheet("color: gold; font-size: 20px; font-weight: bold;")
        top_row = QtWidgets.QHBoxLayout()
        top_row.addWidget(logo)
        top_row.addStretch()
        sidebar_layout.addLayout(top_row)
        sidebar_layout.addSpacing(10)

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
        root.addWidget(self.sidebar)

        # ---------------- Stacked pages ----------------
        self.stacked = QtWidgets.QStackedWidget()
        root.addWidget(self.stacked, 1)

        # ---------------- Home page ----------------
        self.page_home = QtWidgets.QWidget()
        home_layout = QtWidgets.QVBoxLayout(self.page_home)
        home_layout.setContentsMargins(32, 32, 32, 32)
        home_layout.setSpacing(24)

        home_title = QtWidgets.QLabel("Welcome back")
        home_title.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        home_layout.addWidget(home_title)

        recent_label = QtWidgets.QLabel("Recently Played")
        recent_label.setStyleSheet("color: #B3B3B3; font-size: 16px;")
        home_layout.addWidget(recent_label)

        self.recent_grid = QtWidgets.QGridLayout()
        self.recent_grid.setSpacing(16)
        home_layout.addLayout(self.recent_grid)

        self.recent_cards = []
        for i in range(12):
            frame = QtWidgets.QFrame()
            frame.setObjectName("recentCard")
            frame.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            frame.setMinimumSize(180, 100)

            v = QtWidgets.QVBoxLayout(frame)
            v.setContentsMargins(12, 12, 12, 12)
            v.setSpacing(6)

            title = QtWidgets.QLabel("—")
            title.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 14px;")

            subtitle = QtWidgets.QLabel("")
            subtitle.setStyleSheet("color: #B3B3B3; font-size: 12px;")
            subtitle.setWordWrap(True)

            v.addWidget(title)
            v.addWidget(subtitle)
            v.addStretch()

            row = i // 4
            col = i % 4
            self.recent_grid.addWidget(frame, row, col)

            self.recent_cards.append(
                {"frame": frame, "title": title, "subtitle": subtitle, "media_id": None}
            )

        home_layout.addStretch()
        self.stacked.addWidget(self.page_home)

        # ---------------- Library page ----------------
        self.page_library = QtWidgets.QWidget()
        library_layout = QtWidgets.QVBoxLayout(self.page_library)
        library_layout.setContentsMargins(20, 20, 20, 20)
        library_layout.setSpacing(12)

        # ---------------- TOP BAR ----------------
        top_bar = QtWidgets.QHBoxLayout()
        library_layout.addLayout(top_bar)

        # Toggle button
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

        # Search Library — EXACT width of left pane
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Search in library…")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setFixedHeight(34)
        self.search_edit.setFixedWidth(175)
        top_bar.addWidget(self.search_edit)

        # Dropdown — same height as search bars
        self.search_filter = QtWidgets.QComboBox()
        self.search_filter.addItems(["All", "Audio Only", "Video Only"])
        self.search_filter.setFixedHeight(34)
        self.search_filter.setFixedWidth(120)
        top_bar.addWidget(self.search_filter)

        top_bar.addSpacing(10)

        # ---------------- YouTube search (icon inside, shifted right) ----------------
        youtube_container = QtWidgets.QWidget()
        yt_layout = QtWidgets.QHBoxLayout(youtube_container)
        yt_layout.setContentsMargins(0, 0, 0, 0)
        yt_layout.setSpacing(4)

        self.youtube_search = QtWidgets.QLineEdit()
        self.youtube_search.setPlaceholderText("Search YouTube…")
        self.youtube_search.setFixedHeight(34)
        self.youtube_search.setFixedWidth(362)

        # Create themed search icon
        search_icon = QtGui.QIcon()
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
            self._yt_highlight_icon = highlight_icon

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

        # store for eventFilter
        self._yt_highlight_icon = highlight_icon

        # we will handle hover in eventFilter
        self.youtube_search.installEventFilter(self)

        # Clicking the icon triggers the search
        action.triggered.connect(lambda: self.on_youtube_search_clicked())

        yt_layout.addWidget(self.youtube_search)

        # Shift the whole YouTube search area RIGHT by ~12mm (≈62px)
        yt_layout.addSpacing(62)

        top_bar.addWidget(youtube_container)
        # End Of YouTube Search Bar

        top_bar.addStretch()

        self.menu_button = QtWidgets.QPushButton("Library ▾")
        self.menu_button.setFixedHeight(34)
        top_bar.addWidget(self.menu_button)

        self.login_button = QtWidgets.QPushButton("Login")
        self.login_button.setFixedHeight(34)
        top_bar.addWidget(self.login_button)

        # ---------------- MIDDLE LAYOUT + SPLITTER ----------------
        middle_layout = QtWidgets.QHBoxLayout()
        library_layout.addLayout(middle_layout, 1)

        splitter = QtWidgets.QSplitter()
        splitter.setOrientation(QtCore.Qt.Horizontal)
        middle_layout.addWidget(splitter)

        # Left artist pane
        self.artist_tree = QtWidgets.QTreeWidget()
        self.artist_tree.setObjectName("artistTree")
        self.artist_tree.setHeaderHidden(True)
        self.artist_tree.setFixedWidth(220)
        self.artist_tree.setMouseTracking(True)
        self.artist_tree.setItemDelegate(PillDelegate(self.artist_tree))
        splitter.addWidget(self.artist_tree)

        # Add "All Artists" pill button
        self.artist_tree.clear()
        all_item = QtWidgets.QTreeWidgetItem(["All Artists"])
        font = all_item.font(0)
        font.setPointSize(12)
        font.setBold(True)
        all_item.setFont(0, font)
        all_item.setData(0, QtCore.Qt.UserRole, "pill")
        self.artist_tree.addTopLevelItem(all_item)

        # ---------------- RIGHT SIDE ----------------
        right_container = QtWidgets.QWidget()
        right_container_layout = QtWidgets.QHBoxLayout(right_container)
        right_container_layout.setContentsMargins(0, 0, 0, 0)
        right_container_layout.setSpacing(8)
        splitter.addWidget(right_container)

        # Library table
        self.library_list = QtWidgets.QTableWidget()
        self.library_list.setColumnCount(5)
        self.library_list.setHorizontalHeaderLabels(
            ["Title", "Artist", "Album", "Duration", "ID"]
        )
        self.library_list.verticalHeader().setVisible(False)
        self.library_list.setAlternatingRowColors(True)
        self.library_list.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.library_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.library_list.setColumnWidth(0, 240)
        self.library_list.setColumnWidth(1, 180)
        self.library_list.setColumnWidth(2, 180)
        self.library_list.setColumnWidth(3, 80)
        self.library_list.setColumnHidden(4, True)
        right_container_layout.addWidget(self.library_list, 2)

        # Right info panel
        right_layout = QtWidgets.QVBoxLayout()
        right_layout.setSpacing(16)
        right_container_layout.addLayout(right_layout, 3)

        self.video_widget = VideoWidget()
        self.video_widget.setMinimumHeight(320)
        right_layout.addWidget(self.video_widget, 4)

        info_container = QtWidgets.QHBoxLayout()
        right_layout.addLayout(info_container)

        self.album_art_label = QtWidgets.QLabel()
        self.album_art_label.setFixedSize(120, 120)
        self.album_art_label.setAlignment(QtCore.Qt.AlignCenter)
        self.album_art_label.setStyleSheet(
            "background-color: #181818; border-radius: 8px; border: 1px solid #333;"
        )
        info_container.addWidget(self.album_art_label)

        info_text = QtWidgets.QVBoxLayout()
        info_container.addLayout(info_text)

        self.title_label = QtWidgets.QLabel("Title")
        self.artist_label = QtWidgets.QLabel("Artist")
        self.album_label = QtWidgets.QLabel("Album")
        for lbl in (self.title_label, self.artist_label, self.album_label):
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: #FFFFFF; font-size: 14px;")

        info_text.addWidget(self.title_label)
        info_text.addWidget(self.artist_label)
        info_text.addWidget(self.album_label)
        info_text.addStretch()

        queue_label = QtWidgets.QLabel("Queue")
        queue_label.setStyleSheet("color: #B3B3B3; font-size: 14px;")
        right_layout.addWidget(queue_label)

        self.queue_list = QtWidgets.QListWidget()
        self.queue_list.setFixedHeight(130)
        right_layout.addWidget(self.queue_list)

        # ---------------- BOTTOM CONTROLS ----------------
        bottom_layout = QtWidgets.QVBoxLayout()
        bottom_layout.setSpacing(12)
        library_layout.addLayout(bottom_layout)

        progress_row = QtWidgets.QHBoxLayout()
        bottom_layout.addLayout(progress_row)

        self.time_label_start = QtWidgets.QLabel("0:00")
        self.time_label_end = QtWidgets.QLabel("0:00")
        self.time_label_start.setStyleSheet("color: #B3B3B3;")
        self.time_label_end.setStyleSheet("color: #B3B3B3;")

        self.position_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.position_slider.setRange(0, 1000)

        self.time_mode_button = QtWidgets.QPushButton("REM")
        self.time_mode_button.setFixedWidth(50)

        progress_row.addWidget(self.time_label_start)
        progress_row.addWidget(self.position_slider, 1)
        progress_row.addWidget(self.time_label_end)
        progress_row.addWidget(self.time_mode_button)

        self.position_bar = QtWidgets.QProgressBar()
        self.position_bar.setRange(0, 1000)
        self.position_bar.setTextVisible(False)
        self.position_bar.setFixedHeight(4)
        self.position_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2A2A2A;
                border-radius: 2px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #00F0FF;
                border-radius: 2px;
            }
        """)
        progress_bar_row = QtWidgets.QHBoxLayout()
        bottom_layout.addLayout(progress_bar_row)
        progress_bar_row.addWidget(self.position_bar)

        def control(text, tooltip):
            btn = QtWidgets.QPushButton(text)
            btn.setToolTip(tooltip)
            btn.setFixedSize(110, 40)
            btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            btn.setObjectName("pillButton")
            return btn

        self.btn_prev = control("Back", "Previous")
        self.btn_play = control("Play", "Play")
        self.btn_pause = control("Pause", "Pause")
        self.btn_stop = control("Stop", "Stop")
        self.btn_next = control("Next", "Next")

        self.btn_shuffle = control("Shuffle Off", "Shuffle")
        self.btn_mute = control("Mute", "Mute")
        self.btn_repeat = control("Repeat Off", "Repeat")

        controls_row = QtWidgets.QHBoxLayout()
        controls_row.addStretch()
        controls_row.addWidget(self.btn_prev)
        controls_row.addWidget(self.btn_play)
        controls_row.addWidget(self.btn_pause)
        controls_row.addWidget(self.btn_stop)
        controls_row.addWidget(self.btn_next)
        controls_row.addSpacing(20)
        controls_row.addWidget(self.btn_shuffle)
        controls_row.addWidget(self.btn_mute)
        controls_row.addWidget(self.btn_repeat)
        controls_row.addStretch()
        bottom_layout.addLayout(controls_row)

        volume_row = QtWidgets.QHBoxLayout()
        bottom_layout.addLayout(volume_row)

        self.volume_label = QtWidgets.QLabel("Volume: 40%")
        self.volume_label.setStyleSheet("color: #B3B3B3;")

        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(40)
        self.volume_slider.setFixedWidth(200)

        self.eq_widget = EqualizerWidget()
        self.eq_widget.setMinimumWidth(160)

        volume_row.addStretch()
        volume_row.addWidget(self.volume_label)
        volume_row.addWidget(self.volume_slider)
        volume_row.addWidget(QtWidgets.QLabel("Output level:"))
        volume_row.addWidget(self.eq_widget)
        volume_row.addStretch()

        # Add Library page to stack
        self.stacked.addWidget(self.page_library)

        # ============================================================
        #  CHUNK C ALL OSK RELATED CODE
        # ============================================================

        # ------------- OSK MINI KEYBOARD (FLOATING) THIS CANNOT BE MOVED----------------
        #-------------- ALL OTHER RELATED OSK FEATURES LINES 1798 TO 1921 UNLES MORE CODE ADDED----------
        self.keyboard = MiniKeyboard(self.page_library)
        self.keyboard.setFixedHeight(260)   # NEW — ensures keyboard is visible
        self.keyboard.setFixedWidth(self.page_library.width())

        self.keyboard.hide()
        self.keyboard.setParent(self.page_library)
        self.keyboard.raise_()
        self.keyboard.keyPressed.connect(self._handle_virtual_key)

        # ---------------- Now Playing page ----------------
        self.page_now_playing = QtWidgets.QWidget()
        np_layout = QtWidgets.QVBoxLayout(self.page_now_playing)
        np_layout.setContentsMargins(40, 40, 40, 40)
        np_layout.setSpacing(20)

        self.big_art_label = QtWidgets.QLabel()
        self.big_art_label.setFixedSize(300, 300)
        self.big_art_label.setAlignment(QtCore.Qt.AlignCenter)
        self.big_art_label.setStyleSheet(
            "background-color: #181818; border-radius: 8px; border: 1px solid #333;"
        )
        np_layout.addWidget(self.big_art_label, alignment=QtCore.Qt.AlignCenter)

        self.np_title = QtWidgets.QLabel("Title")
        self.np_artist = QtWidgets.QLabel("Artist")
        self.np_album = QtWidgets.QLabel("Album")
        for lbl in (self.np_title, self.np_artist, self.np_album):
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.setStyleSheet("color: white; font-size: 18px;")
        np_layout.addWidget(self.np_title)
        np_layout.addWidget(self.np_artist)
        np_layout.addWidget(self.np_album)

        np_layout.addStretch()
        self.stacked.addWidget(self.page_now_playing)

        # ---------------- Statistics page ----------------
        self.page_stats = QtWidgets.QWidget()
        stats_layout = QtWidgets.QHBoxLayout(self.page_stats)
        stats_layout.setContentsMargins(40, 40, 40, 40)
        stats_layout.setSpacing(20)

        self.stats_left = QtWidgets.QVBoxLayout()
        stats_layout.addLayout(self.stats_left, 2)

        self.chart_audio_video = QChartView()
        self.chart_top_artists = QChartView()

        self.stats_left.addWidget(self.chart_audio_video)
        self.stats_left.addWidget(self.chart_top_artists)

        self.stats_right = QtWidgets.QVBoxLayout()
        stats_layout.addLayout(self.stats_right, 1)

        self.stats_totals = QtWidgets.QLabel("Totals")
        self.stats_totals.setStyleSheet(
            "color: white; font-size: 18px; font-weight: bold;"
        )
        self.stats_right.addWidget(self.stats_totals)

        self.stats_list_tracks = QtWidgets.QListWidget()
        self.stats_list_artists = QtWidgets.QListWidget()

        self.stats_right.addWidget(QtWidgets.QLabel("Top Tracks"))
        self.stats_right.addWidget(self.stats_list_tracks)

        self.stats_right.addWidget(QtWidgets.QLabel("Top Artists"))
        self.stats_right.addWidget(self.stats_list_artists)

        self.stats_right.addStretch()

        self.stacked.addWidget(self.page_stats)

    # ============================================================
    #         MENU + SIGNAL CONNECTIONS (UPDATED + FIXED)
    # ============================================================

    def _create_protected_menu(self):
        """Creates the Library dropdown menu (no CD items anymore)."""
        self.library_menu = QtWidgets.QMenu(self)

        act_add_files = self.library_menu.addAction("Add Files…")
        act_add_folders = self.library_menu.addAction("Add Folders…")
        self.library_menu.addSeparator()

        act_delete_selected = self.library_menu.addAction("Delete Selected")
        act_delete_all = self.library_menu.addAction("Delete ALL Media")
        act_undo_delete = self.library_menu.addAction("Undo Last Delete")
        act_open_trash = self.library_menu.addAction("Open Trash Bin")
        self.library_menu.addSeparator()

        act_export = self.library_menu.addAction("Export Library to CSV")
        act_import = self.library_menu.addAction("Import Library from CSV")
        self.library_menu.addSeparator()

        act_edit_metadata = self.library_menu.addAction("Edit Metadata…")
        act_change_password = self.library_menu.addAction("Change Admin Password")

        # Store actions
        self.act_add_files = act_add_files
        self.act_add_folders = act_add_folders
        self.act_delete_selected = act_delete_selected
        self.act_delete_all = act_delete_all
        self.act_undo_delete = act_undo_delete
        self.act_open_trash = act_open_trash
        self.act_export = act_export
        self.act_import = act_import
        self.act_edit_metadata = act_edit_metadata
        self.act_change_password = act_change_password

    def _connect_signals(self):
        """Connects all UI signals."""

        # Sidebar navigation
        self.btn_nav_home.clicked.connect(lambda: self.set_page(0))
        self.btn_nav_library.clicked.connect(lambda: self.set_page(1))
        self.btn_nav_now_playing.clicked.connect(lambda: self.set_page(2))
        self.btn_nav_stats.clicked.connect(lambda: self._load_statistics_page())

        # Toggle sidebar
        self.btn_toggle_sidebar.clicked.connect(self.toggle_sidebar)

        # Library menu (admin only)
        self.menu_button.clicked.connect(self._show_library_menu)

        self.act_add_files.triggered.connect(self.add_files_to_db)
        self.act_add_folders.triggered.connect(self.add_folders_to_db)
        self.act_delete_selected.triggered.connect(self.remove_selected_from_db)
        self.act_delete_all.triggered.connect(self.delete_all_media)
        self.act_undo_delete.triggered.connect(self.undo_last_delete)
        self.act_open_trash.triggered.connect(self.open_trash_bin)
        self.act_export.triggered.connect(self.export_library_to_csv)
        self.act_import.triggered.connect(self.import_library_from_csv)
        self.act_edit_metadata.triggered.connect(self._open_edit_metadata_dialog)
        self.act_change_password.triggered.connect(self._open_change_password_dialog)

        # Login
        self.login_button.clicked.connect(self._open_login_dialog)

        # Library interactions
        self.library_list.cellDoubleClicked.connect(self.on_library_double_click)
        self.library_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.library_list.customContextMenuRequested.connect(self._library_context_menu)

        # Artist tree click -> filter by artist
        self.artist_tree.itemClicked.connect(self._on_artist_tree_clicked)

        # Queue interactions
        self.queue_list.itemDoubleClicked.connect(self.on_queue_double_click)
        self.queue_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.queue_list.customContextMenuRequested.connect(self.on_queue_context_menu)

        # Search filter (live search + clear artist filter when cleared)
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        self.search_filter.currentIndexChanged.connect(self._load_library)

        # Playback controls
        self.btn_play.clicked.connect(self._user_play_current)
        self.btn_pause.clicked.connect(self._user_pause)
        self.btn_stop.clicked.connect(self._user_stop)
        self.btn_next.clicked.connect(self._user_next_track)
        self.btn_prev.clicked.connect(self._user_prev_track)

        self.btn_shuffle.clicked.connect(self.toggle_shuffle)
        self.btn_repeat.clicked.connect(self.toggle_repeat)
        self.btn_mute.clicked.connect(self.toggle_mute)

        # Seek bar
        self.position_slider.sliderPressed.connect(self.on_seek_pressed)
        self.position_slider.sliderReleased.connect(self.on_seek_released)
        self.position_slider.valueChanged.connect(self.on_seek_moved)

        # Volume
        self.volume_slider.valueChanged.connect(self.on_volume_changed)

        # Time mode
        self.time_mode_button.clicked.connect(self.toggle_time_mode)

        # Event filters
        self.position_slider.installEventFilter(self)
        self.search_edit.installEventFilter(self)
        self.youtube_search.installEventFilter(self)

    # ------------------------------------------------------------
    # ADMIN-ONLY LIBRARY MENU
    # ------------------------------------------------------------
    def _show_library_menu(self):
        if not self.is_admin:
            QtWidgets.QMessageBox.warning(
                self,
                "Admin Required",
                "You must log in as admin to use the Library menu.",
            )
            return

        self.library_menu.exec_(
            self.menu_button.mapToGlobal(
                QtCore.QPoint(0, self.menu_button.height())
            )
        )

    # ------------------------------------------------------------
    # SEARCH TEXT HANDLER (live + reset artist filter when cleared)
    # ------------------------------------------------------------
    def _on_search_text_changed(self, text: str):
        if not text.strip():
            # When search is cleared, also clear artist filter
            self.current_artist_filter = None
        self._load_library()

    # ------------------------------------------------------------
    # Context menu for library list
    # ------------------------------------------------------------
    def _library_context_menu(self, pos):
        row = self.library_list.row(self.library_list.itemAt(pos))
        if row < 0:
            return

        menu = QtWidgets.QMenu(self)
        act_add_to_queue = menu.addAction("Add to Queue")

        action = menu.exec_(self.library_list.mapToGlobal(pos))
        if action == act_add_to_queue:
            id_item = self.library_list.item(row, 4)
            if id_item:
                media_id = int(id_item.text())
                self.user_queue.append(media_id)
                self._refresh_queue()

    # ------------------------------------------------------------
    # Artist tree click handler (filter library by artist)
    # ------------------------------------------------------------
    def _on_artist_tree_clicked(self, item: QtWidgets.QTreeWidgetItem, column: int):
        artist_name = item.text(0).strip()
        if artist_name == "All Artists":
            self.current_artist_filter = None
        else:
            self.current_artist_filter = artist_name
        self._load_library()

    # ------------------------------------------------------------
    # Load statistics page
    # ------------------------------------------------------------
    def _load_statistics_page(self):
        self._generate_statistics()
        self.set_page(3)

# ============================================================
#  CHUNK D — PLAYBACK ENGINE + QUEUE + VOLUME + EQ + IMPORT
#           + TRASH / UNDO / EXPORT / IMPORT (FULL + FIXED)
# ============================================================

    # ------------------------------------------------------------
    # HELPER: PARSE VIDEO FILENAME INTO TITLE / ARTIST
    # ------------------------------------------------------------
    def _parse_video_filename(self, path: str, title: str, artist: str):
        if artist and artist.strip():
            return title, artist

        name = os.path.basename(path)
        lower = name.lower()
        idx = lower.find("video.mp4")
        if idx != -1:
            name = name[: idx + len("video.mp4")]

        if name.lower().endswith(".mp4"):
            core = name[:-4]
        else:
            core, _ = os.path.splitext(name)

        core = core.strip()
        artist_guess = ""
        title_guess = core

        if " - " in core:
            parts = core.split(" - ", 1)
            artist_guess = parts[0].strip()
            title_guess = parts[1].strip()
        else:
            parts = core.split(" ", 1)
            if len(parts) == 2:
                artist_guess = parts[0].strip()
                title_guess = parts[1].strip()

        if not artist_guess:
            artist_guess = ""
        if not title_guess:
            title_guess = title or core

        return title_guess, artist_guess

    # ------------------------------------------------------------
    # DOUBLE CLICK PLAY
    # ------------------------------------------------------------
    def on_library_double_click(self, row: int, column: int):
        id_item = self.library_list.item(row, 4)
        if not id_item:
            return
        media_id = int(id_item.text())
        self.auto_radio_enabled = False
        self.play_media_id(media_id)
        self._mark_user_active()

    # ------------------------------------------------------------
    # YOUTUBE AUTO-PAUSE / RESUME
    # ------------------------------------------------------------
    def on_youtube_search_clicked(self):
        query = self.youtube_search.text().strip()
        if not query:
            return

        if self.player.get_state() == vlc.State.Playing:
            self.youtube_active = True
            self.player.pause()

        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        webbrowser.open(url)

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.ActivationChange:
            if self.isActiveWindow() and self.youtube_active:
                self.youtube_active = False
                if self.player.get_state() == vlc.State.Paused:
                    self.player.play()
        super().changeEvent(event)

    # ------------------------------------------------------------
    # USER PLAYBACK ACTIONS
    # ------------------------------------------------------------
    def _user_play_current(self):
        self.auto_radio_enabled = False

        if self.is_shuffle and (self.current_index < 0 or self.current_index >= len(self.current_playlist)):
            rows = self.db.get_all_media("")
            if rows:
                media_id = random.choice([r[0] for r in rows])
                self.play_media_id(media_id)
                return

        self.play_current()
        self._mark_user_active()

    def _user_pause(self):
        self.pause()
        self._mark_user_active()

    def _user_stop(self):
        self.stop()
        self._mark_user_active()

    def _user_next_track(self):
        self.auto_radio_enabled = False
        self.gap_active = False
        self.next_track()
        self._mark_user_active()

    def _user_prev_track(self):
        self.auto_radio_enabled = False
        self.gap_active = False
        self.prev_track()
        self._mark_user_active()

    def _mark_user_active(self):
        self.last_active_time = time.time()

    # ------------------------------------------------------------
    # PLAY MEDIA
    # ------------------------------------------------------------
    def play_media_id(self, media_id: int):
        row = self.db.get_media_by_id(media_id)
        if not row:
            return

        media_id, path, title, artist, album, duration, is_video = row

        if not os.path.exists(path):
            QtWidgets.QMessageBox.warning(self, "Missing File", f"File not found:\n{path}")
            return

        media = self.instance.media_new(path)
        self.player.set_media(media)
        self.player.set_hwnd(self.video_widget.get_handle())
        self.player.play()

        if self.is_muted:
            self.player.audio_set_volume(0)
        else:
            self.player.audio_set_volume(self.volume_slider.value())

        safe_title = title or ""
        safe_artist = artist or ""
        safe_album = album or ""

        self.title_label.setText(safe_title)
        self.artist_label.setText(safe_artist)
        self.album_label.setText(safe_album)

        self.np_title.setText(safe_title)
        self.np_artist.setText(safe_artist)
        self.np_album.setText(safe_album)

        self.time_label_start.setText("0:00")
        self.time_label_end.setText("0:00")

        load_album_art(self.album_art_label, self.title_label, self.artist_label, path)

        pix = self.album_art_label.pixmap()
        if pix:
            big = pix.scaled(
                self.big_art_label.size(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
            self.big_art_label.setPixmap(big)
        else:
            self.big_art_label.clear()

        add_to_recently_played(self.db, media_id)
        self._load_recently_played()

        rows = self.db.get_all_media(self.search_edit.text().strip())
        filtered = []

        filter_mode = self.search_filter.currentText()
        for r in rows:
            if filter_mode == "Audio Only" and r[6] is True:
                continue
            if filter_mode == "Video Only" and r[6] is False:
                continue
            if self.current_artist_filter and (r[3] or "").strip() != self.current_artist_filter:
                continue
            filtered.append(r)

        self.current_playlist = [r[0] for r in filtered]

        if media_id in self.current_playlist:
            self.current_index = self.current_playlist.index(media_id)
        else:
            self.current_playlist = [media_id]
            self.current_index = 0

        self.last_active_time = time.time()
        self.gap_active = False

    def play_current(self):
        if (self.current_index < 0 or self.current_index >= len(self.current_playlist)) and self.user_queue:
            media_id = self.user_queue.pop(0)
            self._refresh_queue()
            self.play_media_id(media_id)
            return

        if 0 <= self.current_index < len(self.current_playlist):
            self.play_media_id(self.current_playlist[self.current_index])

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()

    # ------------------------------------------------------------
    # NEXT / PREVIOUS TRACK
    # ------------------------------------------------------------
    def next_track(self):
        if self.user_queue:
            media_id = self.user_queue.pop(0)
            self._refresh_queue()
            self.play_media_id(media_id)
            return

        if self.is_repeat and not self.is_shuffle:
            self.play_current()
            return

        if self.is_shuffle:
            rows = self.db.get_all_media("")
            if not rows:
                return
            media_id = random.choice([r[0] for r in rows])
            self.play_media_id(media_id)
            return

        if not self.current_playlist:
            return

        if self.current_index + 1 < len(self.current_playlist):
            self.current_index += 1
        else:
            return

        self.play_current()

    def prev_track(self):
        if not self.current_playlist:
            return

        if self.is_shuffle:
            rows = self.db.get_all_media("")
            if not rows:
                return
            media_id = random.choice([r[0] for r in rows])
            self.play_media_id(media_id)
            return

        if self.current_index - 1 >= 0:
            self.current_index -= 1
        else:
            if self.is_repeat:
                self.current_index = len(self.current_playlist) - 1
            else:
                self.current_index = 0

        self.play_current()

    # ------------------------------------------------------------
    # QUEUE
    # ------------------------------------------------------------
    def _refresh_queue(self):
        self.queue_list.clear()
        for media_id in self.user_queue:
            row = self.db.get_media_by_id(media_id)
            if row:
                _, _, title, artist, *_ = row
                self.queue_list.addItem(f"{title or 'Unknown'} — {artist or ''}")

    def on_queue_double_click(self, item: QtWidgets.QListWidgetItem):
        index = self.queue_list.row(item)
        if 0 <= index < len(self.user_queue):
            media_id = self.user_queue.pop(index)
            self._refresh_queue()
            self.auto_radio_enabled = False
            self.play_media_id(media_id)
            self._mark_user_active()

    def on_queue_context_menu(self, pos: QtCore.QPoint):
        row = self.queue_list.row(self.queue_list.itemAt(pos))
        if row < 0:
            return

        menu = QtWidgets.QMenu(self)
        act_remove = menu.addAction("Remove From Queue")

        action = menu.exec_(self.queue_list.mapToGlobal(pos))
        if action == act_remove and 0 <= row < len(self.user_queue):
            self.user_queue.pop(row)
            self._refresh_queue()

    # ------------------------------------------------------------
    # TOGGLES
    # ------------------------------------------------------------
    def toggle_shuffle(self):
        self.is_shuffle = not self.is_shuffle

        if self.is_shuffle:
            self.is_repeat = False
            self.btn_repeat.setText("Repeat Off")

        self.btn_shuffle.setText("Shuffle On" if self.is_shuffle else "Shuffle Off")

    def toggle_repeat(self):
        self.is_repeat = not self.is_repeat

        if self.is_repeat:
            self.is_shuffle = False
            self.btn_shuffle.setText("Shuffle Off")

        self.btn_repeat.setText("Repeat On" if self.is_repeat else "Repeat Off")

    def toggle_mute(self):
        if not self.is_muted:
            self._pre_mute_volume = self.volume_slider.value()
            self.is_muted = True
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(0)
            self.volume_slider.blockSignals(False)
            self.player.audio_set_volume(0)
            self.volume_label.setText("Volume: 0%")
            self.btn_mute.setText("Unmute")
        else:
            self.is_muted = False
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(self._pre_mute_volume)
            self.volume_slider.blockSignals(False)
            self.player.audio_set_volume(self._pre_mute_volume)
            self.volume_label.setText(f"Volume: {self._pre_mute_volume}%")
            self.btn_mute.setText("Mute")

        self._mark_user_active()

    # ------------------------------------------------------------
    # SEEK + VOLUME
    # ------------------------------------------------------------
    def on_seek_pressed(self):
        self.user_is_seeking = True
        self._mark_user_active()

    def on_seek_released(self):
        self.user_is_seeking = False
        pos = self.position_slider.value() / 1000
        self.player.set_position(pos)
        self._mark_user_active()

    def on_seek_moved(self, value: int):
        if self.user_is_seeking:
            self.player.set_position(value / 1000)

    def on_volume_changed(self, value: int):
        if self.is_muted:
            self.is_muted = False
            self.btn_mute.setText("Mute")

        self.player.audio_set_volume(value)
        self.volume_label.setText(f"Volume: {value}%")
        self._mark_user_active()

    def toggle_time_mode(self):
        self.show_remaining = not self.show_remaining
        self.time_mode_button.setText("Rem" if self.show_remaining else "Total")
        self._mark_user_active()

    # ------------------------------------------------------------
    # UI UPDATE LOOP (WITH VLC END-OF-TRACK FIX)
    #DO NOT MOVE OR ALTER ANYTHING TO DO WITH VLC IN THIS SCRIPT IT WILL BRAKE THE APP
    # ------------------------------------------------------------
    def update_ui(self):
        if not self.player:
            return

        # --- Fallback for VLC not firing EndReached (video/audio end bug) ---
        try:
            length_ms = self.player.get_length()
            if length_ms > 0:
                pos = self.player.get_position()

                # VLC bug: video often gets stuck at 0.99+ and never fires EndReached
                if pos >= 0.995 and not self.gap_active:
                    self.gap_active = True
                    self.gap_start_time = time.time()
        except:
            pass

        # --- Original UI update logic ---
        # --- DO NOT MOVE OR ALTER ANYTHING TO DO WITH VLC IN THIS SCRIPT IT WILL BRAKE THE APP
        length_ms = self.player.get_length()
        state = self.player.get_state()

        if length_ms > 0:
            length = length_ms // 1000
            pos = self.player.get_position()
            cur = int(pos * length)

            self.time_label_start.setText(format_duration(cur))

            if self.show_remaining:
                self.time_label_end.setText(f"-{format_duration(max(0, length - cur))}")
            else:
                self.time_label_end.setText(format_duration(length))

            if not self.user_is_seeking:
                self.position_slider.setValue(int(pos * 1000))

            self.position_bar.setValue(int(pos * 1000))
        else:
            self.time_label_start.setText("0:00")
            self.time_label_end.setText("0:00")
            self.position_slider.setValue(0)
            self.position_bar.setValue(0)

        # --- 5‑second gap logic ---
        if self.gap_active and time.time() - self.gap_start_time >= 5:
            self.gap_active = False
            self.next_track()

        # --- Auto‑radio logic ---
        if state not in (vlc.State.Playing, vlc.State.Paused):
            if self.auto_radio_enabled and time.time() - self.last_active_time > 15:
                self._play_random_track()

    def _play_random_track(self):
        rows = self.db.get_all_media("")
        if rows:
            media_id = random.choice([r[0] for r in rows])
            self.play_media_id(media_id)

    # ------------------------------------------------------------
    # EQUALIZER (volume-reactive)
    # DO NOT MOVE OR ALTER ANYTHING TO DO WITH VLC IN THIS SCRIPT IT WILL BRAKE THE APP
    # ------------------------------------------------------------
    def _update_equalizer(self):
        if self.player.get_state() == vlc.State.Playing:
            vol = self.player.audio_get_volume()
            if vol is None:
                vol = self.volume_slider.value()
            intensity = max(0.1, min(1.0, (vol or 0) / 100.0))
            levels = [random.random() * intensity for _ in range(self.eq_widget.bars)]
            self.eq_widget.set_levels(levels)
        else:
            self.eq_widget.clear_levels()

    # ============================================================
    #         CHUNK E
    # ============================================================

    # ------------------------------------------------------------
    # LOAD LIBRARY (SEARCH + FILTER + ARTIST TREE)
    # ------------------------------------------------------------
    def _load_library(self):
        search = self.search_edit.text().strip()
        filter_mode = self.search_filter.currentText()

        rows = self.db.get_all_media(search)
        filtered = []

        for r in rows:
            media_id, path, title, artist, album, duration, is_video = r

            if is_video and (not artist or not artist.strip()):
                parsed_title, parsed_artist = self._parse_video_filename(path, title or "", artist or "")
                if parsed_artist:
                    artist = parsed_artist
                if parsed_title:
                    title = parsed_title

            if filter_mode == "Audio Only" and is_video:
                continue
            if filter_mode == "Video Only" and not is_video:
                continue
            if self.current_artist_filter and (artist or "").strip() != self.current_artist_filter:
                continue
            filtered.append((media_id, path, title, artist, album, duration, is_video))

            self.artist_tree.clear()

            all_item = QtWidgets.QTreeWidgetItem(["All Artists"])

            font = all_item.font(0)
            font.setPointSize(12)   # ← make it bigger
            font.setBold(True)      # optional, but looks great for a top-level button
            all_item.setFont(0, font)

            self.artist_tree.addTopLevelItem(all_item)


        artists = set()
        for _, path, title, artist, _, _, is_video in filtered:
            if is_video and (not artist or not artist.strip()):
                _, parsed_artist = self._parse_video_filename(path, title or "", artist or "")
                artist_name = (parsed_artist or "Unknown Artist").strip()
            else:
                artist_name = (artist or "Unknown Artist").strip()
            artists.add(artist_name)

        for artist_name in sorted(artists):
            artist_item = QtWidgets.QTreeWidgetItem([artist_name])
            self.artist_tree.addTopLevelItem(artist_item)

        self.artist_tree.expandAll()

        self.library_list.setRowCount(len(filtered))

        for row_index, row in enumerate(filtered):
            media_id, path, title, artist, album, duration, is_video = row

            self.library_list.setItem(row_index, 0, QtWidgets.QTableWidgetItem(title or ""))
            self.library_list.setItem(row_index, 1, QtWidgets.QTableWidgetItem(artist or ""))
            self.library_list.setItem(row_index, 2, QtWidgets.QTableWidgetItem(album or ""))
            self.library_list.setItem(row_index, 3, QtWidgets.QTableWidgetItem(format_duration(duration)))
            self.library_list.setItem(row_index, 4, QtWidgets.QTableWidgetItem(str(media_id)))

        self.library_list.resizeRowsToContents()

    # ------------------------------------------------------------
    # IMPORT / DELETE / TRASH / UNDO / EXPORT / IMPORT
    # ------------------------------------------------------------
    def add_files_to_db(self):
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Add Media Files",
            "",
            "Media Files (*.mp3 *.wav *.flac *.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm)",
        )
        for path in paths:
            self._import_media(path)

        self._load_library()

    def add_folders_to_db(self):
        dialog = QtWidgets.QFileDialog(self, "Select Folder(s)")
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)

        list_view = dialog.findChild(QtWidgets.QListView, "listView")
        if list_view:
            list_view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        tree_view = dialog.findChild(QtWidgets.QTreeView)
        if tree_view:
            tree_view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        folders = dialog.selectedFiles()
        for folder in folders:
            if not os.path.isdir(folder):
                continue

            for f in os.listdir(folder):
                full = os.path.join(folder, f)
                if os.path.isfile(full):
                    if is_video_file(full) or f.lower().endswith(
                        (".mp3", ".wav", ".flac")
                    ):
                        self._import_media(full)

        self._load_library()

    # ------------------------------------------------------------
    # LOAD RECENTLY PLAYED (HOME PAGE)
    # ------------------------------------------------------------
    def _load_recently_played(self):
        rows = self.db.get_recently_played(limit=12)

        for card in self.recent_cards:
            card["title"].setText("—")
            card["subtitle"].setText("")
            card["media_id"] = None

        for i, row in enumerate(rows):
            if i >= len(self.recent_cards):
                break

            media_id, path, title, artist, album, duration, is_video = row

            safe_title = title or "Unknown Title"
            safe_artist = artist or "Unknown Artist"

            self.recent_cards[i]["title"].setText(safe_title)
            self.recent_cards[i]["subtitle"].setText(safe_artist)
            self.recent_cards[i]["media_id"] = media_id

            frame = self.recent_cards[i]["frame"]
            frame.mousePressEvent = lambda e, mid=media_id: self.play_media_id(mid)

        self._load_library()

    # ------------------------------------------------------------
    # TRACK EXISTS CHECK
    # ------------------------------------------------------------
    def _track_exists(self, title: str, artist: str) -> bool:
        rows = self.db.get_all_media("")
        for row in rows:
            _, _, t, a, _, _, _ = row
            if (t or "").strip().lower() == (title or "").strip().lower() and (
                a or ""
            ).strip().lower() == (artist or "").strip().lower():
                return True
        return False

    # ------------------------------------------------------------
    # IMPORT MEDIA FILE
    # ------------------------------------------------------------
    def _import_media(self, path: str):
        title = os.path.basename(path)
        artist = ""
        album = ""
        duration = 0

        try:
            audio = MutagenFile(path)
            if audio is not None:
                if getattr(audio, "info", None) and getattr(audio.info, "length", None):
                    duration = int(audio.info.length)

                tags = getattr(audio, "tags", None)
                if tags:
                    t = tags.get("TIT2") or tags.get("TITLE")
                    a = tags.get("TPE1") or tags.get("ARTIST")
                    al = tags.get("TALB") or tags.get("ALBUM")

                    if t:
                        title = str(t)
                    if a:
                        artist = str(a)
                    if al:
                        album = str(al)
        except Exception:
            pass

        if is_video_file(path):
            title, artist = self._parse_video_filename(path, title, artist)

        if self._track_exists(title, artist):
            return

        self.db.add_media(path, title, artist, album, duration, is_video_file(path))

    # ------------------------------------------------------------
    # COLLECT ROWS BY ID
    # ------------------------------------------------------------
    def _collect_rows_by_ids(self, media_ids):
        rows = []
        for mid in media_ids:
            row = self.db.get_media_by_id(mid)
            if row:
                rows.append(row)
        return rows

    # ------------------------------------------------------------
    # REMOVE SELECTED FROM DB
    # ------------------------------------------------------------
    def remove_selected_from_db(self):
        rows_idx = sorted(
            {i.row() for i in self.library_list.selectedIndexes()}, reverse=True
        )
        if not rows_idx:
            return

        confirm = QtWidgets.QMessageBox.question(
            self,
            "Remove Selected",
            f"Remove {len(rows_idx)} selected item(s) from the library?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if confirm != QtWidgets.QMessageBox.Yes:
            return

        media_ids = []
        for row in rows_idx:
            id_item = self.library_list.item(row, 4)
            if id_item:
                media_ids.append(int(id_item.text()))

        deleted_rows = self._collect_rows_by_ids(media_ids)
        self.last_deleted_batch = deleted_rows
        self.trash.extend(deleted_rows)

        for mid in media_ids:
            self.db.remove_media(mid)

        self._load_library()

    # ------------------------------------------------------------
    # DELETE ALL MEDIA
    # ------------------------------------------------------------
    def delete_all_media(self):
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Delete ALL Media",
            "This will move ALL tracks to Trash and clear the library.\nAre you sure?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if confirm != QtWidgets.QMessageBox.Yes:
            return

        rows = self.db.get_all_media("")
        self.last_deleted_batch = rows
        self.trash.extend(rows)

        self.db.clear_all_media()
        self._load_library()
        self._load_recently_played()

    # ------------------------------------------------------------
    # UNDO LAST DELETE
    # ------------------------------------------------------------
    def undo_last_delete(self):
        if not self.last_deleted_batch:
            QtWidgets.QMessageBox.information(
                self, "Undo Delete", "There is no delete operation to undo."
            )
            return

        for row in self.last_deleted_batch:
            media_id, path, title, artist, album, duration, is_video = row
            if not os.path.exists(path):
                continue
            if self._track_exists(title, artist):
                continue
            self.db.add_media(path, title, artist, album, duration, is_video)

        self.last_deleted_batch = []
        self._load_library()
        self._load_recently_played()

    # ------------------------------------------------------------
    # EXPORT LIBRARY TO CSV
    # ------------------------------------------------------------
    def export_library_to_csv(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Library to CSV",
            "",
            "CSV Files (*.csv)",
        )
        if not path:
            return

        rows = self.db.get_all_media("")
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "path", "title", "artist", "album", "duration", "is_video"])
                for row in rows:
                    writer.writerow(row)
            QtWidgets.QMessageBox.information(self, "Export", "Library exported successfully.")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Export Error", f"Could not export library:\n{e}")

    # ------------------------------------------------------------
    # IMPORT LIBRARY FROM CSV
    # ------------------------------------------------------------
    def import_library_from_csv(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Import Library from CSV",
            "",
            "CSV Files (*.csv)",
        )
        if not path:
            return

        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    media_path = row.get("path", "")
                    title = row.get("title", "")
                    artist = row.get("artist", "")
                    album = row.get("album", "")
                    duration = int(row.get("duration", "0") or 0)
                    is_video = row.get("is_video", "0") in ("1", "True", "true")

                    if not os.path.exists(media_path):
                        continue
                    if self._track_exists(title, artist):
                        continue
                    self.db.add_media(media_path, title, artist, album, duration, is_video)

            self._load_library()
            self._load_recently_played()
            QtWidgets.QMessageBox.information(self, "Import", "Library imported successfully.")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Import Error", f"Could not import library:\n{e}")


    # ============================================================
    #  CHUNK F STATISTICS PAGE + NAVIGATION + MAIN()
    # ============================================================

    # ------------------------------------------------------------
    # STATISTICS PAGE GENERATION
    # ------------------------------------------------------------
    def _generate_statistics(self):
        """Builds charts + lists for the Statistics page."""

        rows = self.db.get_all_media("")
        if not rows:
            # Clear charts if library empty
            self.chart_audio_video.setChart(QChart())
            self.chart_top_artists.setChart(QChart())
            self.stats_totals.setText("No media in library.")
            self.stats_list_tracks.clear()
            self.stats_list_artists.clear()
            return

        # --------------------------------------------------------
        # TOTALS
        # --------------------------------------------------------
        total_tracks = len(rows)
        total_audio = sum(1 for r in rows if not r[6])
        total_video = sum(1 for r in rows if r[6])
        total_duration = sum(r[5] for r in rows)

        hours = total_duration // 3600
        minutes = (total_duration % 3600) // 60

        self.stats_totals.setText(
            f"Total Tracks: {total_tracks}\n"
            f"Audio: {total_audio}\n"
            f"Video: {total_video}\n"
            f"Total Duration: {hours}h {minutes}m"
        )

        # --------------------------------------------------------
        # PIE CHART — AUDIO VS VIDEO
        # --------------------------------------------------------
        pie = QPieSeries()
        pie.append("Audio", total_audio)
        pie.append("Video", total_video)

        chart1 = QChart()
        chart1.addSeries(pie)
        chart1.setTitle("Audio vs Video")
        chart1.legend().setVisible(True)
        chart1.legend().setAlignment(QtCore.Qt.AlignBottom)

        self.chart_audio_video.setChart(chart1)
        self.chart_audio_video.setRenderHint(QtGui.QPainter.Antialiasing)

        # --------------------------------------------------------
        # TOP ARTISTS (COUNT)
        # --------------------------------------------------------
        artist_count = {}
        for _, _, _, artist, *_ in rows:
            if artist:
                artist_count[artist] = artist_count.get(artist, 0) + 1

        top_artists = sorted(artist_count.items(), key=lambda x: x[1], reverse=True)[:10]

        bar_set = QBarSet("Tracks")
        categories = []

        for artist, count in top_artists:
            bar_set.append(count)
            categories.append(artist)

        bar_series = QBarSeries()
        bar_series.append(bar_set)

        chart2 = QChart()
        chart2.addSeries(bar_series)
        chart2.setTitle("Top 10 Artists (by track count)")
        chart2.setAnimationOptions(QChart.SeriesAnimations)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart2.addAxis(axis_x, QtCore.Qt.AlignBottom)
        bar_series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, max([c for _, c in top_artists]) if top_artists else 1)
        chart2.addAxis(axis_y, QtCore.Qt.AlignLeft)
        bar_series.attachAxis(axis_y)

        self.chart_top_artists.setChart(chart2)
        self.chart_top_artists.setRenderHint(QtGui.QPainter.Antialiasing)

        # --------------------------------------------------------
        # TOP TRACKS (BY TITLE FREQUENCY)
        # --------------------------------------------------------
        title_count = {}
        for _, _, title, *_ in rows:
            if title:
                title_count[title] = title_count.get(title, 0) + 1

        top_tracks = sorted(title_count.items(), key=lambda x: x[1], reverse=True)[:10]

        self.stats_list_tracks.clear()
        for title, count in top_tracks:
            self.stats_list_tracks.addItem(f"{title} — {count} entries")

        # --------------------------------------------------------
        # TOP ARTISTS LIST
        # --------------------------------------------------------
        self.stats_list_artists.clear()
        for artist, count in top_artists:
            self.stats_list_artists.addItem(f"{artist} — {count} tracks")

    # ============================================================
    #  OSK VIRTUAL KEYBOARD HELPERS
    #  OSK MINI KEYBOARD FLOATING IS ON LINE 644 BUT MAY MOVE AS MORE CODE ADDED
    # ============================================================
    def _show_keyboard(self):
        if not hasattr(self, "keyboard"):
            return
        self.keyboard.show()
        self.keyboard.raise_()
        self.resizeEvent(None)
        self.keyboard.installEventFilter(self)

    def _hide_keyboard(self):
        self.keyboard.hide()
        self._kb_target = None

    def _handle_virtual_key(self, key):

        # ------------------------------------------------------------
        # ENTER KEY
        # ------------------------------------------------------------
        if key == "\r":
            # If OSK was typing into Library Search
            if self._kb_target is self.search_edit:
                self.search_edit.clear()
                self._hide_keyboard()
                return

            # If OSK was typing into YouTube Search
            if self._kb_target is self.youtube_search:
                text = self.youtube_search.text()
                self._hide_keyboard()

                if text.strip():
                    self.on_youtube_search_clicked()

                self.youtube_search.clear()
                return

            return  # safety fallback

        # ------------------------------------------------------------
        # BACKSPACE
        # ------------------------------------------------------------
        if key == "\b":
            target = getattr(self, "_kb_target", None)
            if target is None:
                return

            cursor = target.cursorPosition()
            text = target.text()
            if cursor > 0:
                text = text[:cursor - 1] + text[cursor:]
                target.setText(text)
                target.setCursorPosition(cursor - 1)
            return

        # ------------------------------------------------------------
        # NORMAL CHARACTER INPUT WITH SMART‑CASE
        # ------------------------------------------------------------
        target = getattr(self, "_kb_target", None)
        if target is None:
            return

        cursor = target.cursorPosition()
        text = target.text()

        # OSK always sends uppercase letters; we decide case here
        ch = key
        if ch.isalpha():
            if cursor == 0 or (cursor > 0 and text[cursor - 1] == " "):
                ch = ch.upper()
            else:
                ch = ch.lower()

        # Insert the character at the cursor
        new_text = text[:cursor] + ch + text[cursor:]
        target.setText(new_text)
        target.setCursorPosition(cursor + 1)
        target.setFocus()




    # ------------------------------------------------------------
    # NAVIGATION HELPER
    # ------------------------------------------------------------
    def set_page(self, index: int):
        self.stacked.setCurrentIndex(index)

    # ------------------------------------------------------------
    # OSK EVENT FILTER (SLIDER PREVIEW + OSK + YOUTUBE HOVER + ENTER)
    # ------------------------------------------------------------
    def eventFilter(self, obj, event):

        # SAFETY GUARD: if UI not fully built yet, ignore events
        if not hasattr(self, "search_edit"):
            return False
        if not hasattr(self, "youtube_search"):
            return False
        if not hasattr(self, "position_slider"):
            return False

        # SAFETY GUARD: ignore null objects
        if obj is None:
            return False

        # ------------------------------------------------------------
        # OSK OPENS WHEN YOUTUBE SEARCH GETS FOCUS
        # ------------------------------------------------------------
        if obj is self.youtube_search and event.type() == QtCore.QEvent.FocusIn:
            self._kb_target = self.youtube_search
            self._show_keyboard()

        # ------------------------------------------------------------
        # PHYSICAL KEYBOARD ENTER HANDLING (YOUTUBE + LIBRARY)
        # ------------------------------------------------------------
        if event.type() == QtCore.QEvent.KeyPress and event.key() in (
            QtCore.Qt.Key_Return,
            QtCore.Qt.Key_Enter,
        ):

            # Library search Enter
            if self._kb_target is self.search_edit:
                self.search_edit.clear()
                self._hide_keyboard()
                return True

            # YouTube search Enter
            if self._kb_target is self.youtube_search:
                text = self.youtube_search.text()
                self._hide_keyboard()

                # IMPORTANT: run YouTube search BEFORE clearing
                if text.strip():
                    self.on_youtube_search_clicked()

                self.youtube_search.clear()
                self.youtube_search.clearFocus()

                return True

        # ------------------------------------------------------------
        # OSK OPENS OSK WHEN SEARCH LIBRARY GETS FOCUS
        # ------------------------------------------------------------
        if obj is self.search_edit and event.type() == QtCore.QEvent.FocusIn:
            self._kb_target = self.search_edit
            self._show_keyboard()

        # ------------------------------------------------------------
        # YOUTUBE SEARCH HOVER ICON
        # ------------------------------------------------------------
        if obj is self.youtube_search and hasattr(self, "_yt_highlight_icon"):
            if event.type() == QtCore.QEvent.Enter:
                self._yt_highlight_icon(True)
            elif event.type() == QtCore.QEvent.Leave:
                self._yt_highlight_icon(False)

        # ------------------------------------------------------------
        # SLIDER HOVER PREVIEW
        # ------------------------------------------------------------
        if obj is self.position_slider and event.type() == QtCore.QEvent.MouseMove:
            length_ms = self.player.get_length()
            if length_ms > 0:
                length = length_ms // 1000
                slider_rect = self.position_slider.rect()

                x = event.pos().x()
                ratio = x / max(1, slider_rect.width())
                ratio = min(max(ratio, 0.0), 1.0)

                preview_sec = int(length * ratio)

                QtWidgets.QToolTip.showText(
                    self.position_slider.mapToGlobal(event.pos()),
                    format_duration(preview_sec),
                    self.position_slider,
                )

        return super().eventFilter(obj, event)

    # ------------------------------------------------------------
    # RESIZE EVENT (KEEP KEYBOARD AT BOTTOM OF LIBRARY)
    # ------------------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)

        if hasattr(self, "keyboard") and not self.keyboard.isHidden():

        # Only auto-position the keyboard the FIRST time
            if not getattr(self.keyboard, "auto_positioned", False):

                w = self.page_library.width()
                h = self.keyboard.height()

                x = (self.page_library.width() - w) // 2
                y = self.page_library.height() - h - 450

                self.keyboard.setGeometry(x, y, w, h)

            # Mark as positioned so we NEVER reposition again
                self.keyboard.auto_positioned = True




# ============================================================
#  MAIN ENTRY POINT
# ============================================================

def main():
    app = QtWidgets.QApplication(sys.argv)
    player = MediaPlayer()

    # Blur disabled so native title bar and buttons stay fully visible
    # try:
    #     hwnd = int(player.winId())
    #     enable_windows_blur(hwnd)
    # except Exception as e:
    #     print("Blur not available:", e)

    player.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()


