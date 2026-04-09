<<<<<<< HEAD
from PyQt5 import QtWidgets, QtCore
import os
import csv
from mutagen import File as MutagenFile
from app.db import is_video_file

class LibraryManagementMixin:
        # ------------------------------
    # CHECK IF TRACK ALREADY EXISTS
    # ------------------------------
    def _track_exists(self, title: str, artist: str) -> bool:
        rows = self.db.get_all_media("")
        for row in rows:
            _, _, t, a, _, _, _ = row
            if (t or "").strip().lower() == (title or "").strip().lower() and (
                a or ""
            ).strip().lower() == (artist or "").strip().lower():
                return True
        return False

    # ------------------------------
    # COLLECT ROWS BY ID
    # ------------------------------
    def _collect_rows_by_ids(self, media_ids):
        rows = []
        for mid in media_ids:
            row = self.db.get_media_by_id(mid)
            if row:
                rows.append(row)
        return rows

    # ------------------------------
    # PARSE VIDEO FILENAME
    # ------------------------------
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

    # ------------------------------
    # ADD FILES
    # ------------------------------
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

    # ------------------------------
    # ADD FOLDERS
    # ------------------------------
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

    # ------------------------------
    # IMPORT MEDIA FILE
    # ------------------------------
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

    # ------------------------------
    # DELETE SELECTED
    # ------------------------------
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

    # ------------------------------
    # DELETE ALL MEDIA
    # ------------------------------
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

    # ------------------------------
    # UNDO LAST DELETE
    # ------------------------------
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

    # ------------------------------
    # TRASH BIN
    # ------------------------------
    def open_trash_bin(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Trash Bin")
        layout = QtWidgets.QVBoxLayout(dialog)

        list_widget = QtWidgets.QListWidget()
        for row in self.trash:
            media_id, path, title, artist, album, duration, is_video = row
            list_widget.addItem(
                f"{title or 'Unknown'} — {artist or ''} ({os.path.basename(path)})"
            )
        layout.addWidget(list_widget)

        btn_row = QtWidgets.QHBoxLayout()
        btn_restore = QtWidgets.QPushButton("Restore Selected")
        btn_restore_all = QtWidgets.QPushButton("Restore All")
        btn_empty = QtWidgets.QPushButton("Empty Trash")
        btn_close = QtWidgets.QPushButton("Close")

        btn_row.addStretch()
        btn_row.addWidget(btn_restore)
        btn_row.addWidget(btn_restore_all)
        btn_row.addWidget(btn_empty)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        def do_restore_selected():
            selected = list_widget.selectedIndexes()
            if not selected:
                return
            indices = sorted({i.row() for i in selected}, reverse=True)
            for idx in indices:
                if 0 <= idx < len(self.trash):
                    media_id, path, title, artist, album, duration, is_video = self.trash[idx]
                    if os.path.exists(path) and not self._track_exists(title, artist):
                        self.db.add_media(path, title, artist, album, duration, is_video)
                        del self.trash[idx]
            self._load_library()
            self._load_recently_played()
            list_widget.clear()
            for row in self.trash:
                _, path, title, artist, album, duration, is_video = row
                list_widget.addItem(
                    f"{title or 'Unknown'} — {artist or ''} ({os.path.basename(path)})"
                )

        def do_restore_all():
            restore_list = list(self.trash)
            for row in restore_list:
                media_id, path, title, artist, album, duration, is_video = row
                if os.path.exists(path) and not self._track_exists(title, artist):
                    self.db.add_media(path, title, artist, album, duration, is_video)
            self.trash.clear()
            self._load_library()
            self._load_recently_played()
            list_widget.clear()

        def do_empty():
            confirm = QtWidgets.QMessageBox.question(
                dialog,
                "Empty Trash",
                "Permanently clear all items from Trash?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if confirm == QtWidgets.QMessageBox.Yes:
                self.trash.clear()
                self.last_deleted_batch = []
                list_widget.clear()

        btn_restore.clicked.connect(do_restore_selected)
        btn_restore_all.clicked.connect(do_restore_all)
        btn_empty.clicked.connect(do_empty)
        btn_close.clicked.connect(dialog.close)

        dialog.exec_()

    # ------------------------------
    # EXPORT LIBRARY TO CSV
    # ------------------------------
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

    # ------------------------------
    # IMPORT LIBRARY FROM CSV
    # ------------------------------
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
=======
from PyQt5 import QtWidgets, QtCore
import os
import csv
from mutagen import File as MutagenFile
from app.db import is_video_file

class LibraryManagementMixin:
        # ------------------------------
    # CHECK IF TRACK ALREADY EXISTS
    # ------------------------------
    def _track_exists(self, title: str, artist: str) -> bool:
        rows = self.db.get_all_media("")
        for row in rows:
            _, _, t, a, _, _, _ = row
            if (t or "").strip().lower() == (title or "").strip().lower() and (
                a or ""
            ).strip().lower() == (artist or "").strip().lower():
                return True
        return False

    # ------------------------------
    # COLLECT ROWS BY ID
    # ------------------------------
    def _collect_rows_by_ids(self, media_ids):
        rows = []
        for mid in media_ids:
            row = self.db.get_media_by_id(mid)
            if row:
                rows.append(row)
        return rows

    # ------------------------------
    # PARSE VIDEO FILENAME
    # ------------------------------
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

    # ------------------------------
    # ADD FILES
    # ------------------------------
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

    # ------------------------------
    # ADD FOLDERS
    # ------------------------------
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

    # ------------------------------
    # IMPORT MEDIA FILE
    # ------------------------------
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

    # ------------------------------
    # DELETE SELECTED
    # ------------------------------
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

    # ------------------------------
    # DELETE ALL MEDIA
    # ------------------------------
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

    # ------------------------------
    # UNDO LAST DELETE
    # ------------------------------
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

    # ------------------------------
    # TRASH BIN
    # ------------------------------
    def open_trash_bin(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Trash Bin")
        layout = QtWidgets.QVBoxLayout(dialog)

        list_widget = QtWidgets.QListWidget()
        for row in self.trash:
            media_id, path, title, artist, album, duration, is_video = row
            list_widget.addItem(
                f"{title or 'Unknown'} — {artist or ''} ({os.path.basename(path)})"
            )
        layout.addWidget(list_widget)

        btn_row = QtWidgets.QHBoxLayout()
        btn_restore = QtWidgets.QPushButton("Restore Selected")
        btn_restore_all = QtWidgets.QPushButton("Restore All")
        btn_empty = QtWidgets.QPushButton("Empty Trash")
        btn_close = QtWidgets.QPushButton("Close")

        btn_row.addStretch()
        btn_row.addWidget(btn_restore)
        btn_row.addWidget(btn_restore_all)
        btn_row.addWidget(btn_empty)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        def do_restore_selected():
            selected = list_widget.selectedIndexes()
            if not selected:
                return
            indices = sorted({i.row() for i in selected}, reverse=True)
            for idx in indices:
                if 0 <= idx < len(self.trash):
                    media_id, path, title, artist, album, duration, is_video = self.trash[idx]
                    if os.path.exists(path) and not self._track_exists(title, artist):
                        self.db.add_media(path, title, artist, album, duration, is_video)
                        del self.trash[idx]
            self._load_library()
            self._load_recently_played()
            list_widget.clear()
            for row in self.trash:
                _, path, title, artist, album, duration, is_video = row
                list_widget.addItem(
                    f"{title or 'Unknown'} — {artist or ''} ({os.path.basename(path)})"
                )

        def do_restore_all():
            restore_list = list(self.trash)
            for row in restore_list:
                media_id, path, title, artist, album, duration, is_video = row
                if os.path.exists(path) and not self._track_exists(title, artist):
                    self.db.add_media(path, title, artist, album, duration, is_video)
            self.trash.clear()
            self._load_library()
            self._load_recently_played()
            list_widget.clear()

        def do_empty():
            confirm = QtWidgets.QMessageBox.question(
                dialog,
                "Empty Trash",
                "Permanently clear all items from Trash?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if confirm == QtWidgets.QMessageBox.Yes:
                self.trash.clear()
                self.last_deleted_batch = []
                list_widget.clear()

        btn_restore.clicked.connect(do_restore_selected)
        btn_restore_all.clicked.connect(do_restore_all)
        btn_empty.clicked.connect(do_empty)
        btn_close.clicked.connect(dialog.close)

        dialog.exec_()

    # ------------------------------
    # EXPORT LIBRARY TO CSV
    # ------------------------------
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

    # ------------------------------
    # IMPORT LIBRARY FROM CSV
    # ------------------------------
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
>>>>>>> be9547aaccb1857afa059ff99cc82f20dba6ff7b
