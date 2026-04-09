<<<<<<< HEAD
# app/playback.py
# Contains PlaybackMixin — all playback, queue, YouTube, seek, volume,
# equalizer, auto‑radio, and gap logic.

import os
import random
import time
import webbrowser

from PyQt5 import QtCore, QtWidgets
import vlc

from app.db import format_duration, is_video_file
from app.helpers import load_album_art, add_to_recently_played


class PlaybackMixin:
    """
    Mixin providing all playback, queue, YouTube, seek, volume,
    equalizer, auto‑radio, and gap logic.
    MediaPlayer inherits this alongside QMainWindow.
    """

    # ------------------------------------------------------------
    # PARSE VIDEO FILENAME
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
    # SEEK + VOLUME + TIME MODE
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
        self.time_mode_button.setText("REM" if self.show_remaining else "TOT")
        self._mark_user_active()

    # ------------------------------------------------------------
    # UI UPDATE LOOP + AUTO-RADIO + EQ
    # ------------------------------------------------------------
    def update_ui(self):
        if not self.player:
            return

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

        if self.gap_active and time.time() - self.gap_start_time >= 5:
            self.gap_active = False
            self.next_track()

        if state not in (vlc.State.Playing, vlc.State.Paused):
            if self.auto_radio_enabled and time.time() - self.last_active_time > 15:
                self._play_random_track()

    def _play_random_track(self):
        rows = self.db.get_all_media("")
        if rows:
            media_id = random.choice([r[0] for r in rows])
            self.play_media_id(media_id)

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


=======
# app/playback.py
# Contains PlaybackMixin — all playback, queue, YouTube, seek, volume,
# equalizer, auto‑radio, and gap logic.

import os
import random
import time
import webbrowser

from PyQt5 import QtCore, QtWidgets
import vlc

from app.db import format_duration, is_video_file
from app.helpers import load_album_art, add_to_recently_played


class PlaybackMixin:
    """
    Mixin providing all playback, queue, YouTube, seek, volume,
    equalizer, auto‑radio, and gap logic.
    MediaPlayer inherits this alongside QMainWindow.
    """

    # ------------------------------------------------------------
    # PARSE VIDEO FILENAME
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
    # SEEK + VOLUME + TIME MODE
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
        self.time_mode_button.setText("REM" if self.show_remaining else "TOT")
        self._mark_user_active()

    # ------------------------------------------------------------
    # UI UPDATE LOOP + AUTO-RADIO + EQ
    # ------------------------------------------------------------
    def update_ui(self):
        if not self.player:
            return

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

        if self.gap_active and time.time() - self.gap_start_time >= 5:
            self.gap_active = False
            self.next_track()

        if state not in (vlc.State.Playing, vlc.State.Paused):
            if self.auto_radio_enabled and time.time() - self.last_active_time > 15:
                self._play_random_track()

    def _play_random_track(self):
        rows = self.db.get_all_media("")
        if rows:
            media_id = random.choice([r[0] for r in rows])
            self.play_media_id(media_id)

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


>>>>>>> be9547aaccb1857afa059ff99cc82f20dba6ff7b
