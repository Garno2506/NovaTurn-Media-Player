import json
import os
from PyQt5 import QtWidgets, QtCore, QtGui

# NovaTurn Black + Green Theme
ACCENT = "#1DB954"
ACCENT_SOFT = "#32E06F"
BG_DARK = "#101010"
BG_PANEL = "#181818"
TEXT_MAIN = "#FFFFFF"
TEXT_SUBTLE = "#C0C0C0"


class EqCurveWidget(QtWidgets.QWidget):
    """Smooth EQ curve with gradient fill and grid."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.gains = [0] * 10
        self._ready = False
        self.setMinimumHeight(140)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        QtCore.QTimer.singleShot(0, self._enable_painting)

    def _enable_painting(self):
        self._ready = True
        self.update()

    def set_gains(self, gains):
        self.gains = gains[:]
        self.update()

    def paintEvent(self, event):
        if not self._ready:
            return

        rect = self.rect().adjusted(12, 12, -12, -12)
        if rect.width() < 5 or rect.height() < 5:
            return

        super().paintEvent(event)

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        # Background
        painter.fillRect(rect, QtGui.QColor(BG_PANEL))

        # Border
        pen = QtGui.QPen(QtGui.QColor(ACCENT))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 8, 8)

        # Midline (0 dB)
        mid_y = rect.center().y()
        grid_pen = QtGui.QPen(QtGui.QColor("#333333"))
        grid_pen.setStyle(QtCore.Qt.DashLine)
        painter.setPen(grid_pen)
        painter.drawLine(rect.left(), mid_y, rect.right(), mid_y)

        # Gains
        if not self.gains or len(self.gains) < 2:
            return

        points = []
        for i, g in enumerate(self.gains):
            x = rect.left() + (rect.width() * i) / (len(self.gains) - 1)
            norm = (g + 12) / 24.0
            y = rect.bottom() - norm * rect.height()
            points.append(QtCore.QPointF(x, y))

        if len(points) < 3:
            return

        # Smooth spline
        path = QtGui.QPainterPath()
        path.moveTo(points[0])

        for i in range(1, len(points) - 1):
            p0 = points[i - 1]
            p1 = points[i]
            p2 = points[i + 1]
            c1 = QtCore.QPointF((p0.x() + p1.x()) / 2.0, p0.y())
            c2 = QtCore.QPointF((p1.x() + p2.x()) / 2.0, p2.y())
            path.cubicTo(c1, c2, p2)

        # Fill under curve
        if rect.height() <= 0:
            return

        fill_path = QtGui.QPainterPath(path)
        fill_path.lineTo(points[-1].x(), rect.bottom())
        fill_path.lineTo(points[0].x(), rect.bottom())
        fill_path.closeSubpath()

        gradient = QtGui.QLinearGradient(rect.left(), rect.top(), rect.left(), rect.bottom())
        gradient.setColorAt(0.0, QtGui.QColor(ACCENT_SOFT + "88"))
        gradient.setColorAt(1.0, QtGui.QColor(ACCENT + "00"))
        painter.fillPath(fill_path, gradient)

        # Stroke
        curve_pen = QtGui.QPen(QtGui.QColor(ACCENT_SOFT))
        curve_pen.setWidth(2)
        painter.setPen(curve_pen)
        painter.drawPath(path)


class LedMeter(QtWidgets.QWidget):
    """Vertical LED meter with peak-hold indicator and glow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.level = 0.0
        self.peak = 0.0

        # Match slider groove width
        self.setMinimumWidth(4)
        self.setMaximumWidth(4)
        self.setMinimumHeight(80)

    def set_levels(self, level, peak):
        self.level = max(0.0, min(1.0, float(level)))
        self.peak = max(0.0, min(1.0, float(peak)))
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        rect = self.rect()
        h = rect.height()

        # Background
        painter.fillRect(rect, QtGui.QColor("#202020"))

        # LED bar
        led_height = int(h * self.level)
        if led_height > 0:
            if self.level < 0.33:
                color = QtGui.QColor("#1DB954")
            elif self.level < 0.66:
                color = QtGui.QColor("#E6C229")
            else:
                color = QtGui.QColor("#FF3B30")

            bar_rect = QtCore.QRect(rect.left(), rect.bottom() - led_height, rect.width(), led_height)
            painter.fillRect(bar_rect, color)

        # Peak marker position
        peak_y = rect.bottom() - int(h * self.peak)

        # --- GLOW EFFECT ---
        glow_strength = int(12 * self.peak)  # stronger glow at higher peaks
        if glow_strength > 0:
            glow_color = QtGui.QColor(255, 255, 255, 80)  # soft white glow
            glow_pen = QtGui.QPen(glow_color)
            glow_pen.setWidth(glow_strength)
            painter.setPen(glow_pen)
            painter.drawLine(rect.center().x(), peak_y, rect.center().x(), peak_y)

        # Peak marker (solid white)
        peak_rect = QtCore.QRect(rect.left(), peak_y - 2, rect.width(), 3)
        painter.fillRect(peak_rect, QtGui.QColor("#FFFFFF"))





class GraphicEqualizer(QtWidgets.QWidget):
    """NovaTurn 10-band EQ with VLC shaping and state persistence."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.Window)   # <-- FIXES AUTO-CLOSE

        self.led_meters = []   # LED bars for each slider
        self.peak_levels = [0.0] * 10

        self.setWindowTitle("NovaTurn Graphic Equalizer")
        self.setMinimumSize(980, 520)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.setStyleSheet(f"background-color: {BG_DARK}; color: {TEXT_MAIN};")

        self.frequencies = ["31", "62", "125", "250", "500", "1k", "2k", "4k", "8k", "16k"]
        self.sliders = []
        self._slider_timers = {}
        self.vlc_player = None
        self.vlc_eq = None

        # Presets
        self.built_in_presets = {
            "Flat": [0] * 10,
            "Rock": [3, 5, 4, 1, -1, -1, 2, 4, 5, 4],
            "Jazz": [2, 3, 2, 0, 0, 1, 2, 3, 3, 2],
            "Classical": [0, 1, 2, 3, 2, 1, 0, -1, -2, -3],
            "Vocal Boost": [-2, -1, 1, 3, 4, 4, 3, 1, -1, -2],
        }
        self.user_presets = {}
        base_dir = os.path.dirname(__file__)
        self.presets_file = os.path.join(base_dir, "eq_presets.json")
        self.state_file = os.path.join(base_dir, "eq_state.json")

        # A/B
        self._ab_stored_gains = [0] * 10

        # Options
        self.auto_gain_enabled = False
        self.limiter_enabled = True
        self.boost_amount = 3  # dB

        self._build_ui()
        self._load_user_presets()
        self._load_state()
        self._update_curve()
        self._apply_to_vlc()

        # LED animation timer
        self.led_timer = QtCore.QTimer(self)
        self.led_timer.timeout.connect(self._update_leds)
        self.led_timer.start(40)  # 25 FPS

        self._fade_in()

    # ------------------------------
    # VLC Integration
    # ------------------------------
    def set_vlc_player(self, player):
        """Attach VLC player and create a VLC equalizer instance."""
        self.vlc_player = player

        try:
            import vlc
            self.vlc_eq = vlc.AudioEqualizer()
        except Exception:
            self.vlc_eq = None
            return

        self._apply_to_vlc()

    def _apply_to_vlc(self):
        """Apply slider gains (with auto-gain/limiter) to VLC equalizer."""
        if self.vlc_player is None:
            return
        if self.vlc_eq is None:
            return

        try:
            is_playing = bool(self.vlc_player.is_playing())
        except Exception:
            is_playing = False

        if not is_playing:
            return

        gains = self._get_gains()

        if self.limiter_enabled:
            gains = [max(-12, min(12, g)) for g in gains]

        if self.auto_gain_enabled:
            max_gain = max(gains)
            if max_gain > 0:
                offset = max_gain / 2.0
                gains = [g - offset for g in gains]

        for i, g in enumerate(gains):
            try:
                self.vlc_eq.set_amp_at_index(float(g), i)
            except Exception:
                pass

        try:
            self.vlc_player.set_equalizer(self.vlc_eq)
        except Exception:
            return

        try:
            if not self.vlc_player.is_playing():
                self.vlc_player.play()
        except Exception:
            pass

    # ------------------------------
    # UI BUILD
    # ------------------------------
    def _build_ui(self):
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        frame = QtWidgets.QFrame()
        frame.setObjectName("eqFrame")
        frame.setStyleSheet(f"""
            QFrame#eqFrame {{
                background-color: {BG_PANEL};
                border: 2px solid {ACCENT};
                border-radius: 6px;
            }}
        """)
        outer.addWidget(frame)

        main = QtWidgets.QVBoxLayout(frame)
        main.setContentsMargins(16, 16, 16, 16)

        # Curve
        self.curve_widget = EqCurveWidget(frame)
        main.addWidget(self.curve_widget)

        # Middle section
        mid = QtWidgets.QHBoxLayout()
        mid.setSpacing(25)

        # Sliders
        sliders_layout = QtWidgets.QHBoxLayout()
        sliders_layout.setSpacing(20)

        for freq in self.frequencies:
            vbox = QtWidgets.QVBoxLayout()
            vbox.setSpacing(8)

            label = QtWidgets.QLabel(freq + " Hz")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 13px;")
            vbox.addWidget(label)

            hbox = QtWidgets.QHBoxLayout()
            hbox.setSpacing(4)

            slider = QtWidgets.QSlider(QtCore.Qt.Vertical)
            slider.setRange(-12, 12)
            slider.setValue(0)
            slider.setTickPosition(QtWidgets.QSlider.TicksBothSides)
            slider.setTickInterval(3)
            slider.setFixedHeight(260)
            slider.setStyleSheet(self._slider_style(True))
            slider.valueChanged.connect(self._on_slider_changed)
            slider.setToolTip("0 dB")

            self.sliders.append(slider)
            hbox.addWidget(slider)

            led = LedMeter()
            self.led_meters.append(led)
            hbox.addWidget(led)

            vbox.addLayout(hbox)
            sliders_layout.addLayout(vbox)

        mid.addLayout(sliders_layout)

        # Right panel
        right = QtWidgets.QVBoxLayout()
        right.setSpacing(10)

        # dB scale
        for text in ["+12 dB", "0 dB", "-12 dB"]:
            lbl = QtWidgets.QLabel(text)
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {TEXT_SUBTLE}; font-size: 13px;")
            right.addWidget(lbl)

        right.addSpacing(6)

        # Presets
        preset_box = QtWidgets.QGroupBox("Presets")
        preset_box.setStyleSheet(f"""
            QGroupBox {{
                color: {TEXT_MAIN};
                border: 1px solid #444444;
                border-radius: 4px;
                background-color: {BG_DARK};
            }}
        """)
        preset_layout = QtWidgets.QVBoxLayout(preset_box)

        self.preset_combo = QtWidgets.QComboBox()
        self.preset_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {BG_PANEL};
                color: {TEXT_MAIN};
                border: 1px solid #555555;
                padding: 2px 6px;
            }}
        """)
        self._refresh_preset_combo()

        btn_apply = QtWidgets.QPushButton("Apply Preset")
        btn_apply.setStyleSheet(self._button_style())
        btn_apply.clicked.connect(self._apply_selected_preset)

        btn_save = QtWidgets.QPushButton("Save Current as Preset")
        btn_save.setStyleSheet(self._button_style())
        btn_save.clicked.connect(self._save_current_as_preset)

        btn_delete = QtWidgets.QPushButton("Delete User Preset")
        btn_delete.setStyleSheet(self._button_style())
        btn_delete.clicked.connect(self._delete_selected_user_preset)

        preset_layout.addWidget(self.preset_combo)
        preset_layout.addWidget(btn_apply)
        preset_layout.addWidget(btn_save)
        preset_layout.addWidget(btn_delete)

        right.addWidget(preset_box)

        # Options row: Auto-gain, Limiter, Boost
        options_row = QtWidgets.QHBoxLayout()

        self.chk_auto_gain = QtWidgets.QCheckBox("Auto-gain")
        self.chk_auto_gain.setStyleSheet(f"color: {TEXT_SUBTLE};")
        self.chk_auto_gain.toggled.connect(self._on_auto_gain_toggled)
        options_row.addWidget(self.chk_auto_gain)

        self.chk_limiter = QtWidgets.QCheckBox("Limiter")
        self.chk_limiter.setChecked(True)
        self.chk_limiter.setStyleSheet(f"color: {TEXT_SUBTLE};")
        self.chk_limiter.toggled.connect(self._on_limiter_toggled)
        options_row.addWidget(self.chk_limiter)

        btn_boost_minus = QtWidgets.QPushButton(f"Boost -{self.boost_amount} dB")
        btn_boost_minus.setStyleSheet(self._button_style())
        btn_boost_minus.clicked.connect(self._on_boost_minus_clicked)
        options_row.addWidget(btn_boost_minus)

        btn_boost = QtWidgets.QPushButton(f"Boost +{self.boost_amount} dB")
        btn_boost.setStyleSheet(self._button_style())
        btn_boost.clicked.connect(self._on_boost_clicked)
        options_row.addWidget(btn_boost)

        right.addLayout(options_row)

        # A/B
        self.ab_button = QtWidgets.QPushButton("A/B: Bypass OFF")
        self.ab_button.setCheckable(True)
        self.ab_button.setStyleSheet(self._button_style())
        self.ab_button.toggled.connect(self._toggle_ab)
        right.addWidget(self.ab_button)

        # Reset
        reset_btn = QtWidgets.QPushButton("Reset (Flat)")
        reset_btn.setStyleSheet(self._button_style())
        reset_btn.clicked.connect(self.reset_sliders)
        right.addWidget(reset_btn)

        right.addStretch()
        mid.addLayout(right)

        main.addLayout(mid)

    # ------------------------------
    # Styles
    # ------------------------------
    def _slider_style(self, normal):
        color = ACCENT if normal else ACCENT_SOFT
        return f"""
        QSlider::groove:vertical {{
            background: #333333;
            width: 4px;
            border-radius: 2px;
        }}
        QSlider::handle:vertical {{
            background: {color};
            border: 1px solid #0F7A3A;
            width: 12px;
            height: 22px;
            margin: -6px;
            border-radius: 4px;
        }}
        QSlider::sub-page:vertical {{
            background: {ACCENT};
        }}
        """

    def _button_style(self):
        return f"""
        QPushButton {{
            background-color: {BG_PANEL};
            border: 1px solid {ACCENT};
            color: {TEXT_MAIN};
            padding: 4px 8px;
        }}
        QPushButton:hover {{
            background-color: #262626;
        }}
        QPushButton:checked {{
            background-color: #202820;
        }}
        """

    # ------------------------------
    # Slider Logic
    # ------------------------------
    def _on_slider_changed(self, value):
        slider = self.sender()
        if slider is None:
            return

        if -1 <= value <= 1 and value != 0:
            slider.blockSignals(True)
            slider.setValue(0)
            slider.blockSignals(False)
            value = 0

        slider.setToolTip(f"{value:+d} dB")

        slider.setStyleSheet(self._slider_style(False))
        if slider not in self._slider_timers:
            timer = QtCore.QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda s=slider: s.setStyleSheet(self._slider_style(True)))
            self._slider_timers[slider] = timer
        self._slider_timers[slider].start(180)

        self._update_curve()
        self._apply_to_vlc()

    def _get_gains(self):
        return [s.value() for s in self.sliders]

    def _set_gains(self, gains):
        for s, g in zip(self.sliders, gains):
            s.blockSignals(True)
            s.setValue(int(g))
            s.setToolTip(f"{int(g):+d} dB")
            s.blockSignals(False)

        self._update_curve()
        self._apply_to_vlc()

    def _update_curve(self):
        self.curve_widget.set_gains(self._get_gains())

    def _update_leds(self):
        gains = self._get_gains()

        for i, g in enumerate(gains):
            level = (g + 12) / 24.0

            # Peak logic
            if level > self.peak_levels[i]:
                # Fast attack
                self.peak_levels[i] = level
            else:
                # Slow decay
                self.peak_levels[i] = max(0.0, self.peak_levels[i] - 0.01)

            # Update LED widget
            if i < len(self.led_meters):
                self.led_meters[i].set_levels(level, self.peak_levels[i])


    # ------------------------------
    # Reset
    # ------------------------------
    def reset_sliders(self):
        self._set_gains([0] * len(self.sliders))

    # ------------------------------
    # Presets
    # ------------------------------
    def _refresh_preset_combo(self):
        if not hasattr(self, "preset_combo"):
            return

        current = self.preset_combo.currentText()
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()

        for name in sorted(self.built_in_presets.keys()):
            self.preset_combo.addItem(f"★ {name}")

        if self.user_presets:
            self.preset_combo.insertSeparator(self.preset_combo.count())
            for name in sorted(self.user_presets.keys()):
                self.preset_combo.addItem(f"● {name}")

        self.preset_combo.blockSignals(False)

        if current:
            idx = self.preset_combo.findText(current)
            if idx >= 0:
                self.preset_combo.setCurrentIndex(idx)

    def _decode_preset_name(self, text):
        if text.startswith("★ "):
            return text[2:], "built_in"
        if text.startswith("● "):
            return text[2:], "user"
        return text, "unknown"

    def _apply_selected_preset(self):
        text = self.preset_combo.currentText()
        name, kind = self._decode_preset_name(text)

        if kind == "built_in":
            gains = self.built_in_presets.get(name)
        else:
            gains = self.user_presets.get(name)

        if gains:
            self._set_gains(gains)

    def _save_current_as_preset(self):
        gains = self._get_gains()
        name, ok = QtWidgets.QInputDialog.getText(self, "Save Preset", "Preset name:")
        if not ok or not name.strip():
            return

        name = name.strip()
        if name in self.built_in_presets:
            QtWidgets.QMessageBox.warning(self, "Cannot Overwrite", "Built-in presets cannot be overwritten.")
            return

        self.user_presets[name] = gains
        self._save_user_presets()
        self._refresh_preset_combo()

    def _delete_selected_user_preset(self):
        text = self.preset_combo.currentText()
        name, kind = self._decode_preset_name(text)

        if kind != "user":
            return

        if name in self.user_presets:
            reply = QtWidgets.QMessageBox.question(
                self, "Delete Preset", f"Delete user preset '{name}'?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                del self.user_presets[name]
                self._save_user_presets()
                self._refresh_preset_combo()

    def _load_user_presets(self):
        if not os.path.exists(self.presets_file):
            return
        try:
            with open(self.presets_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.user_presets = {
                    k: v for k, v in data.items()
                    if isinstance(v, list) and len(v) == 10
                }
        except Exception:
            self.user_presets = {}
        self._refresh_preset_combo()

    def _save_user_presets(self):
        try:
            with open(self.presets_file, "w", encoding="utf-8") as f:
                json.dump(self.user_presets, f, indent=2)
        except Exception:
            pass

    # ------------------------------
    # Options: Auto-gain, Limiter, Boost
    # ------------------------------
    def _on_auto_gain_toggled(self, checked):
        self.auto_gain_enabled = checked
        self._apply_to_vlc()
        self._save_state()

    def _on_limiter_toggled(self, checked):
        self.limiter_enabled = checked
        self._apply_to_vlc()
        self._save_state()

    def _on_boost_clicked(self):
        gains = [max(-12, min(12, g + self.boost_amount)) for g in self._get_gains()]
        self._set_gains(gains)
        self._save_state()

    def _on_boost_minus_clicked(self):
        gains = [max(-12, min(12, g - self.boost_amount)) for g in self._get_gains()]
        self._set_gains(gains)
        self._save_state()

    # ------------------------------
    # A/B
    # ------------------------------
    def _toggle_ab(self, checked):
        if checked:
            self._ab_stored_gains = self._get_gains()
            self._set_gains([0] * len(self.sliders))
            self.ab_button.setText("A/B: Bypass ON")
        else:
            self._set_gains(self._ab_stored_gains)
            self.ab_button.setText("A/B: Bypass OFF")
        self._save_state()

    # ------------------------------
    # State Persistence
    # ------------------------------
    def _load_state(self):
        if not os.path.exists(self.state_file):
            return
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return

        gains = data.get("gains")
        if isinstance(gains, list) and len(gains) == len(self.sliders):
            self._set_gains(gains)

        self.auto_gain_enabled = bool(data.get("auto_gain", False))
        self.limiter_enabled = bool(data.get("limiter", True))

        self.chk_auto_gain.blockSignals(True)
        self.chk_auto_gain.setChecked(self.auto_gain_enabled)
        self.chk_auto_gain.blockSignals(False)

        self.chk_limiter.blockSignals(True)
        self.chk_limiter.setChecked(self.limiter_enabled)
        self.chk_limiter.blockSignals(False)

    def _save_state(self):
        data = {
            "gains": self._get_gains(),
            "auto_gain": self.auto_gain_enabled,
            "limiter": self.limiter_enabled,
        }
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def closeEvent(self, event):
        try:
            if self.vlc_player is not None:
                self.vlc_player.set_equalizer(None)
        except Exception:
            pass
        super().closeEvent(event)

    # ------------------------------
    # Fade-in Animation
    # ------------------------------
    def _fade_in(self):
        effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        effect.setOpacity(0.0)

        anim = QtCore.QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(220)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
        anim.start()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = GraphicEqualizer()
    w.show()
    sys.exit(app.exec_())



