<<<<<<< HEAD
from PyQt5 import QtWidgets, QtCore
import os

class DialogsMixin:
    # ------------------------------
    # LOGIN DIALOG
    # ------------------------------
    def _open_login_dialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Admin Login")
        layout = QtWidgets.QVBoxLayout(dialog)

        label = QtWidgets.QLabel("Enter Admin Password:")
        pwd_edit = QtWidgets.QLineEdit()
        pwd_edit.setEchoMode(QtWidgets.QLineEdit.Password)

        layout.addWidget(label)
        layout.addWidget(pwd_edit)

        btn_row = QtWidgets.QHBoxLayout()
        btn_ok = QtWidgets.QPushButton("Login")
        btn_cancel = QtWidgets.QPushButton("Cancel")
        btn_row.addStretch()
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

        def do_login():
            pwd = pwd_edit.text().strip()
            if self.password_manager.verify_password(pwd):
                self.is_admin = True
                self.login_button.setText("Admin")
                QtWidgets.QMessageBox.information(dialog, "Success", "Logged in as admin.")
                dialog.accept()
            else:
                QtWidgets.QMessageBox.warning(dialog, "Error", "Incorrect password.")

        btn_ok.clicked.connect(do_login)
        btn_cancel.clicked.connect(dialog.reject)

        dialog.exec_()

    # ------------------------------
    # CHANGE PASSWORD
    # ------------------------------
    def _open_change_password_dialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Change Admin Password")
        layout = QtWidgets.QVBoxLayout(dialog)

        old_label = QtWidgets.QLabel("Old Password:")
        old_edit = QtWidgets.QLineEdit()
        old_edit.setEchoMode(QtWidgets.QLineEdit.Password)

        new_label = QtWidgets.QLabel("New Password:")
        new_edit = QtWidgets.QLineEdit()
        new_edit.setEchoMode(QtWidgets.QLineEdit.Password)

        confirm_label = QtWidgets.QLabel("Confirm New Password:")
        confirm_edit = QtWidgets.QLineEdit()
        confirm_edit.setEchoMode(QtWidgets.QLineEdit.Password)

        layout.addWidget(old_label)
        layout.addWidget(old_edit)
        layout.addWidget(new_label)
        layout.addWidget(new_edit)
        layout.addWidget(confirm_label)
        layout.addWidget(confirm_edit)

        btn_row = QtWidgets.QHBoxLayout()
        btn_ok = QtWidgets.QPushButton("Change")
        btn_cancel = QtWidgets.QPushButton("Cancel")
        btn_row.addStretch()
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

        def do_change():
            old_pwd = old_edit.text().strip()
            new_pwd = new_edit.text().strip()
            confirm_pwd = confirm_edit.text().strip()

            if new_pwd != confirm_pwd:
                QtWidgets.QMessageBox.warning(dialog, "Error", "New passwords do not match.")
                return

            if not self.password_manager.change_password(old_pwd, new_pwd):
                QtWidgets.QMessageBox.warning(dialog, "Error", "Old password is incorrect.")
                return

            QtWidgets.QMessageBox.information(dialog, "Success", "Password changed successfully.")
            dialog.accept()

        btn_ok.clicked.connect(do_change)
        btn_cancel.clicked.connect(dialog.reject)

        dialog.exec_()

    # ------------------------------
    # EDIT METADATA
    # ------------------------------
    def _open_edit_metadata_dialog(self):
        rows_idx = sorted({i.row() for i in self.library_list.selectedIndexes()})
        if not rows_idx:
            QtWidgets.QMessageBox.information(self, "Edit Metadata", "Select a single track to edit.")
            return
        if len(rows_idx) > 1:
            QtWidgets.QMessageBox.information(self, "Edit Metadata", "Please select only one track.")
            return

        row = rows_idx[0]
        id_item = self.library_list.item(row, 4)
        if not id_item:
            return

        media_id = int(id_item.text())
        db_row = self.db.get_media_by_id(media_id)
        if not db_row:
            return

        _, path, title, artist, album, duration, is_video = db_row

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Edit Metadata")
        layout = QtWidgets.QVBoxLayout(dialog)

        title_label = QtWidgets.QLabel("Title:")
        title_edit = QtWidgets.QLineEdit(title or "")
        artist_label = QtWidgets.QLabel("Artist:")
        artist_edit = QtWidgets.QLineEdit(artist or "")
        album_label = QtWidgets.QLabel("Album:")
        album_edit = QtWidgets.QLineEdit(album or "")

        layout.addWidget(title_label)
        layout.addWidget(title_edit)
        layout.addWidget(artist_label)
        layout.addWidget(artist_edit)
        layout.addWidget(album_label)
        layout.addWidget(album_edit)

        btn_row = QtWidgets.QHBoxLayout()
        btn_ok = QtWidgets.QPushButton("Save")
        btn_cancel = QtWidgets.QPushButton("Cancel")
        btn_row.addStretch()
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

        def do_save():
            new_title = title_edit.text().strip()
            new_artist = artist_edit.text().strip()
            new_album = album_edit.text().strip()

            try:
                conn = self.db.conn
                cur = conn.cursor()
                cur.execute(
                    "UPDATE media SET title = ?, artist = ?, album = ? WHERE id = ?",
                    (new_title, new_artist, new_album, media_id),
                )
                conn.commit()
            except Exception as e:
                QtWidgets.QMessageBox.warning(dialog, "Error", f"Could not update metadata:\n{e}")
                return

            self._load_library()
            self._load_recently_played()
            dialog.accept()

        btn_ok.clicked.connect(do_save)
        btn_cancel.clicked.connect(dialog.reject)

        dialog.exec_()

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
            list_widget.addItem(f"{title or 'Unknown'} — {artist or ''} ({os.path.basename(path)})")
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
                list_widget.addItem(f"{title or 'Unknown'} — {artist or ''} ({os.path.basename(path)})")

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
=======
from PyQt5 import QtWidgets, QtCore
import os

class DialogsMixin:
    # ------------------------------
    # LOGIN DIALOG
    # ------------------------------
    def _open_login_dialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Admin Login")
        layout = QtWidgets.QVBoxLayout(dialog)

        label = QtWidgets.QLabel("Enter Admin Password:")
        pwd_edit = QtWidgets.QLineEdit()
        pwd_edit.setEchoMode(QtWidgets.QLineEdit.Password)

        layout.addWidget(label)
        layout.addWidget(pwd_edit)

        btn_row = QtWidgets.QHBoxLayout()
        btn_ok = QtWidgets.QPushButton("Login")
        btn_cancel = QtWidgets.QPushButton("Cancel")
        btn_row.addStretch()
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

        def do_login():
            pwd = pwd_edit.text().strip()
            if self.password_manager.verify_password(pwd):
                self.is_admin = True
                self.login_button.setText("Admin")
                QtWidgets.QMessageBox.information(dialog, "Success", "Logged in as admin.")
                dialog.accept()
            else:
                QtWidgets.QMessageBox.warning(dialog, "Error", "Incorrect password.")

        btn_ok.clicked.connect(do_login)
        btn_cancel.clicked.connect(dialog.reject)

        dialog.exec_()

    # ------------------------------
    # CHANGE PASSWORD
    # ------------------------------
    def _open_change_password_dialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Change Admin Password")
        layout = QtWidgets.QVBoxLayout(dialog)

        old_label = QtWidgets.QLabel("Old Password:")
        old_edit = QtWidgets.QLineEdit()
        old_edit.setEchoMode(QtWidgets.QLineEdit.Password)

        new_label = QtWidgets.QLabel("New Password:")
        new_edit = QtWidgets.QLineEdit()
        new_edit.setEchoMode(QtWidgets.QLineEdit.Password)

        confirm_label = QtWidgets.QLabel("Confirm New Password:")
        confirm_edit = QtWidgets.QLineEdit()
        confirm_edit.setEchoMode(QtWidgets.QLineEdit.Password)

        layout.addWidget(old_label)
        layout.addWidget(old_edit)
        layout.addWidget(new_label)
        layout.addWidget(new_edit)
        layout.addWidget(confirm_label)
        layout.addWidget(confirm_edit)

        btn_row = QtWidgets.QHBoxLayout()
        btn_ok = QtWidgets.QPushButton("Change")
        btn_cancel = QtWidgets.QPushButton("Cancel")
        btn_row.addStretch()
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

        def do_change():
            old_pwd = old_edit.text().strip()
            new_pwd = new_edit.text().strip()
            confirm_pwd = confirm_edit.text().strip()

            if new_pwd != confirm_pwd:
                QtWidgets.QMessageBox.warning(dialog, "Error", "New passwords do not match.")
                return

            if not self.password_manager.change_password(old_pwd, new_pwd):
                QtWidgets.QMessageBox.warning(dialog, "Error", "Old password is incorrect.")
                return

            QtWidgets.QMessageBox.information(dialog, "Success", "Password changed successfully.")
            dialog.accept()

        btn_ok.clicked.connect(do_change)
        btn_cancel.clicked.connect(dialog.reject)

        dialog.exec_()

    # ------------------------------
    # EDIT METADATA
    # ------------------------------
    def _open_edit_metadata_dialog(self):
        rows_idx = sorted({i.row() for i in self.library_list.selectedIndexes()})
        if not rows_idx:
            QtWidgets.QMessageBox.information(self, "Edit Metadata", "Select a single track to edit.")
            return
        if len(rows_idx) > 1:
            QtWidgets.QMessageBox.information(self, "Edit Metadata", "Please select only one track.")
            return

        row = rows_idx[0]
        id_item = self.library_list.item(row, 4)
        if not id_item:
            return

        media_id = int(id_item.text())
        db_row = self.db.get_media_by_id(media_id)
        if not db_row:
            return

        _, path, title, artist, album, duration, is_video = db_row

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Edit Metadata")
        layout = QtWidgets.QVBoxLayout(dialog)

        title_label = QtWidgets.QLabel("Title:")
        title_edit = QtWidgets.QLineEdit(title or "")
        artist_label = QtWidgets.QLabel("Artist:")
        artist_edit = QtWidgets.QLineEdit(artist or "")
        album_label = QtWidgets.QLabel("Album:")
        album_edit = QtWidgets.QLineEdit(album or "")

        layout.addWidget(title_label)
        layout.addWidget(title_edit)
        layout.addWidget(artist_label)
        layout.addWidget(artist_edit)
        layout.addWidget(album_label)
        layout.addWidget(album_edit)

        btn_row = QtWidgets.QHBoxLayout()
        btn_ok = QtWidgets.QPushButton("Save")
        btn_cancel = QtWidgets.QPushButton("Cancel")
        btn_row.addStretch()
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

        def do_save():
            new_title = title_edit.text().strip()
            new_artist = artist_edit.text().strip()
            new_album = album_edit.text().strip()

            try:
                conn = self.db.conn
                cur = conn.cursor()
                cur.execute(
                    "UPDATE media SET title = ?, artist = ?, album = ? WHERE id = ?",
                    (new_title, new_artist, new_album, media_id),
                )
                conn.commit()
            except Exception as e:
                QtWidgets.QMessageBox.warning(dialog, "Error", f"Could not update metadata:\n{e}")
                return

            self._load_library()
            self._load_recently_played()
            dialog.accept()

        btn_ok.clicked.connect(do_save)
        btn_cancel.clicked.connect(dialog.reject)

        dialog.exec_()

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
            list_widget.addItem(f"{title or 'Unknown'} — {artist or ''} ({os.path.basename(path)})")
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
                list_widget.addItem(f"{title or 'Unknown'} — {artist or ''} ({os.path.basename(path)})")

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
>>>>>>> be9547aaccb1857afa059ff99cc82f20dba6ff7b
