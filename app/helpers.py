# helpers.py
import platform
import ctypes
from urllib.parse import quote
from pathlib import Path
import requests

from PyQt5 import QtCore, QtGui, QtWidgets

PASSWORD = "letmein"  # Change this if you want

# ---------------------------------------------------------
# WINDOWS BLUR (ACRYLIC-LIKE)
# ---------------------------------------------------------
def enable_windows_blur(hwnd: int):
    """
    Enables Windows 10/11 acrylic-like blur behind the window.
    Safe no-op on non-Windows systems.
    """
    if platform.system() != "Windows":
        return

    try:
        class ACCENTPOLICY(ctypes.Structure):
            _fields_ = [
                ("AccentState", ctypes.c_int),
                ("AccentFlags", ctypes.c_int),
                ("GradientColor", ctypes.c_int),
                ("AnimationId", ctypes.c_int),
            ]

        class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
            _fields_ = [
                ("Attribute", ctypes.c_int),
                ("Data", ctypes.c_void_p),
                ("SizeOfData", ctypes.c_size_t),
            ]

        accent = ACCENTPOLICY()
        accent.AccentState = 3  # ACCENT_ENABLE_BLURBEHIND
        accent.AccentFlags = 0
        accent.GradientColor = 0xCC181818  # ARGB
        accent.AnimationId = 0

        data = WINDOWCOMPOSITIONATTRIBDATA()
        data.Attribute = 19  # WCA_ACCENT_POLICY
        data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p)
        data.SizeOfData = ctypes.sizeof(accent)

        set_window_composition_attribute = ctypes.windll.user32.SetWindowCompositionAttribute
        set_window_composition_attribute(hwnd, ctypes.byref(data))

    except Exception as e:
        print("Blur not available:", e)

# ---------------------------------------------------------
# ALBUM ART LOADING (EMBEDDED + ONLINE LOOKUP)
# ---------------------------------------------------------
def load_album_art(label: QtWidgets.QLabel, title_label: QtWidgets.QLabel,
                   artist_label: QtWidgets.QLabel, path: str):
    """
    Loads album art into a QLabel.
    1. Try embedded MP3 ID3 APIC tag.
    2. Fallback to iTunes online lookup.
    """
    label.setPixmap(QtGui.QPixmap())
    label.setText("No Art")

    # Try embedded art
    try:
        ext = Path(path).suffix.lower()
        if ext == ".mp3":
            from mutagen.id3 import ID3, APIC
            audio = ID3(path)
            for tag in audio.values():
                if isinstance(tag, APIC):
                    pixmap = QtGui.QPixmap()
                    pixmap.loadFromData(tag.data)
                    pixmap = pixmap.scaled(
                        label.size(),
                        QtCore.Qt.KeepAspectRatio,
                        QtCore.Qt.SmoothTransformation,
                    )
                    label.setPixmap(pixmap)
                    label.setText("")
                    return
    except Exception as e:
        print("Embedded art error:", e)

    # Online lookup
    title = title_label.text().strip()
    artist = artist_label.text().strip()
    if not title and not artist:
        return

    query = quote(f"{artist} {title}".strip())
    url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=1"

    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("resultCount", 0) > 0:
                artwork_url = data["results"][0].get("artworkUrl100")
                if artwork_url:
                    artwork_url = artwork_url.replace("100x100bb", "600x600bb")
                    img_data = requests.get(artwork_url, timeout=5).content
                    pixmap = QtGui.QPixmap()
                    pixmap.loadFromData(img_data)
                    pixmap = pixmap.scaled(
                        label.size(),
                        QtCore.Qt.KeepAspectRatio,
                        QtCore.Qt.SmoothTransformation,
                    )
                    label.setPixmap(pixmap)
                    label.setText("")
                    return
    except Exception as e:
        print("Online artwork lookup failed:", e)

# ---------------------------------------------------------
# FLOATING MINI-PLAYER POSITIONING
# ---------------------------------------------------------
def position_floating_window(window: QtWidgets.QWidget):
    """
    Positions the floating mini-player in the bottom-right corner
    of the user's primary screen.
    """
    screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
    w = window.width()
    h = window.height()

    x = screen.right() - w - 20
    y = screen.bottom() - h - 20

    window.move(x, y)

def add_to_recently_played(db, media_id: int):
    """
    Wrapper for adding a media item to the recently played list.
    """
    try:
        db.add_recently_played(media_id)
    except Exception as e:
        print("Failed to add recently played:", e)



