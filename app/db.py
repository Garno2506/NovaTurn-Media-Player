<<<<<<< HEAD
import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime


# ------------------------------------------------------------
# Resolve %APPDATA%\NovaTurn
# ------------------------------------------------------------
def appdata_folder() -> Path:
    folder = Path(os.getenv("APPDATA")) / "NovaTurn"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def db_path() -> Path:
    """Return the full path to the persistent media database."""
    return appdata_folder() / "media_library.db"


# ------------------------------------------------------------
# Utility helpers (needed by main.py)
# ------------------------------------------------------------
def format_duration(seconds: int) -> str:
    if seconds is None or seconds <= 0:
        return "0:00"
    m = seconds // 60
    s = seconds % 60
    return f"{m}:{s:02d}"


def is_video_file(path: str) -> bool:
    ext = Path(path).suffix.lower()
    return ext in {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"}


# ------------------------------------------------------------
# MediaDatabase — main SQLite interface
# ------------------------------------------------------------
class MediaDatabase:
    def __init__(self):
        self.db_file = db_path()

        # Ensure the DB file exists
        if not self.db_file.exists():
            open(self.db_file, "a").close()

        # Connect
        self.conn = sqlite3.connect(self.db_file)
        self._create_tables()

    # --------------------------------------------------------
    # Table creation
    # --------------------------------------------------------
    def _create_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE,
                title TEXT,
                artist TEXT,
                album TEXT,
                duration INTEGER,
                is_video INTEGER
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS recently_played (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_id INTEGER,
                played_at TEXT,
                FOREIGN KEY(media_id) REFERENCES media(id)
            )
        """)

        self.conn.commit()

    # --------------------------------------------------------
    # Insert / Remove media
    # --------------------------------------------------------
    def add_media(self, path, title, artist, album, duration, is_video):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO media (path, title, artist, album, duration, is_video)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (path, title, artist, album, duration, 1 if is_video else 0))
        self.conn.commit()

    def remove_media(self, media_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM media WHERE id = ?", (media_id,))
        self.conn.commit()

    def clear_all_media(self):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM media")
        cur.execute("DELETE FROM recently_played")
        self.conn.commit()

    # --------------------------------------------------------
    # Metadata editing
    # --------------------------------------------------------
    def update_metadata(self, media_id, title, artist, album):
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE media
            SET title = ?, artist = ?, album = ?
            WHERE id = ?
        """, (title, artist, album, media_id))
        self.conn.commit()

    # --------------------------------------------------------
    # Fetching media
    # --------------------------------------------------------
    def get_media_by_id(self, media_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, path, title, artist, album, duration, is_video
            FROM media
            WHERE id = ?
        """, (media_id,))
        return cur.fetchone()

    def get_all_media(self, search=""):
        cur = self.conn.cursor()

        if search:
            like = f"%{search.lower()}%"
            cur.execute("""
                SELECT id, path, title, artist, album, duration, is_video
                FROM media
                WHERE LOWER(title) LIKE ?
                   OR LOWER(artist) LIKE ?
                   OR LOWER(album) LIKE ?
                   OR LOWER(path) LIKE ?
                ORDER BY artist, album, title
            """, (like, like, like, like))
        else:
            cur.execute("""
                SELECT id, path, title, artist, album, duration, is_video
                FROM media
                ORDER BY artist, album, title
            """)

        return cur.fetchall()

    # --------------------------------------------------------
    # Recently played
    # --------------------------------------------------------
    def add_recently_played(self, media_id):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO recently_played (media_id, played_at)
            VALUES (?, ?)
        """, (media_id, datetime.utcnow().isoformat()))
        self.conn.commit()

    def get_recently_played(self, limit=6):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT media.id, media.path, media.title, media.artist, media.album,
                   media.duration, media.is_video
            FROM recently_played
            JOIN media ON media.id = recently_played.media_id
            ORDER BY recently_played.played_at DESC
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()

        # Filter out missing files to prevent popups
        valid = [row for row in rows if Path(row[1]).exists()]
        return valid

=======
import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime


# ------------------------------------------------------------
# Resolve %APPDATA%\NovaTurn
# ------------------------------------------------------------
def appdata_folder() -> Path:
    folder = Path(os.getenv("APPDATA")) / "NovaTurn"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def db_path() -> Path:
    """Return the full path to the persistent media database."""
    return appdata_folder() / "media_library.db"


# ------------------------------------------------------------
# Utility helpers (needed by main.py)
# ------------------------------------------------------------
def format_duration(seconds: int) -> str:
    if seconds is None or seconds <= 0:
        return "0:00"
    m = seconds // 60
    s = seconds % 60
    return f"{m}:{s:02d}"


def is_video_file(path: str) -> bool:
    ext = Path(path).suffix.lower()
    return ext in {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"}


# ------------------------------------------------------------
# MediaDatabase — main SQLite interface
# ------------------------------------------------------------
class MediaDatabase:
    def __init__(self):
        self.db_file = db_path()

        # Ensure the DB file exists
        if not self.db_file.exists():
            open(self.db_file, "a").close()

        # Connect
        self.conn = sqlite3.connect(self.db_file)
        self._create_tables()

    # --------------------------------------------------------
    # Table creation
    # --------------------------------------------------------
    def _create_tables(self):
        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE,
                title TEXT,
                artist TEXT,
                album TEXT,
                duration INTEGER,
                is_video INTEGER
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS recently_played (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_id INTEGER,
                played_at TEXT,
                FOREIGN KEY(media_id) REFERENCES media(id)
            )
        """)

        self.conn.commit()

    # --------------------------------------------------------
    # Insert / Remove media
    # --------------------------------------------------------
    def add_media(self, path, title, artist, album, duration, is_video):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO media (path, title, artist, album, duration, is_video)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (path, title, artist, album, duration, 1 if is_video else 0))
        self.conn.commit()

    def remove_media(self, media_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM media WHERE id = ?", (media_id,))
        self.conn.commit()

    def clear_all_media(self):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM media")
        cur.execute("DELETE FROM recently_played")
        self.conn.commit()

    # --------------------------------------------------------
    # Metadata editing
    # --------------------------------------------------------
    def update_metadata(self, media_id, title, artist, album):
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE media
            SET title = ?, artist = ?, album = ?
            WHERE id = ?
        """, (title, artist, album, media_id))
        self.conn.commit()

    # --------------------------------------------------------
    # Fetching media
    # --------------------------------------------------------
    def get_media_by_id(self, media_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, path, title, artist, album, duration, is_video
            FROM media
            WHERE id = ?
        """, (media_id,))
        return cur.fetchone()

    def get_all_media(self, search=""):
        cur = self.conn.cursor()

        if search:
            like = f"%{search.lower()}%"
            cur.execute("""
                SELECT id, path, title, artist, album, duration, is_video
                FROM media
                WHERE LOWER(title) LIKE ?
                   OR LOWER(artist) LIKE ?
                   OR LOWER(album) LIKE ?
                   OR LOWER(path) LIKE ?
                ORDER BY artist, album, title
            """, (like, like, like, like))
        else:
            cur.execute("""
                SELECT id, path, title, artist, album, duration, is_video
                FROM media
                ORDER BY artist, album, title
            """)

        return cur.fetchall()

    # --------------------------------------------------------
    # Recently played
    # --------------------------------------------------------
    def add_recently_played(self, media_id):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO recently_played (media_id, played_at)
            VALUES (?, ?)
        """, (media_id, datetime.utcnow().isoformat()))
        self.conn.commit()

    def get_recently_played(self, limit=6):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT media.id, media.path, media.title, media.artist, media.album,
                   media.duration, media.is_video
            FROM recently_played
            JOIN media ON media.id = recently_played.media_id
            ORDER BY recently_played.played_at DESC
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()

        # Filter out missing files to prevent popups
        valid = [row for row in rows if Path(row[1]).exists()]
        return valid

>>>>>>> be9547aaccb1857afa059ff99cc82f20dba6ff7b
