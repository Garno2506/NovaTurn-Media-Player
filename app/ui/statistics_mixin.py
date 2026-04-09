<<<<<<< HEAD
# app/ui/statistics_mixin.py
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtChart import (
    QChart,
    QChartView,
    QPieSeries,
    QBarSeries,
    QBarSet,
    QBarCategoryAxis,
    QValueAxis,
)


class StatisticsMixin:
    """
    Provides statistics page functionality.
    """

    def _load_statistics_page(self):
        self._generate_statistics()
        self.set_page(3)

    def _generate_statistics(self):
        """Builds charts + lists for the Statistics page."""
        # Clear existing layout
        if self.stats_layout:
            while self.stats_layout.count():
                child = self.stats_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            self.stats_scroll_area.setWidget(None)

        # Create new widget for stats
        stats_widget = QtWidgets.QWidget()
        stats_layout = QtWidgets.QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(20, 20, 20, 20)
        stats_layout.setSpacing(20)

        # Title
        title = QtWidgets.QLabel("Library Statistics")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        stats_layout.addWidget(title)

        # Get data
        rows = self.db.get_all_media("")
        total_tracks = len(rows)
        total_duration = sum(r[5] for r in rows if r[5])
        video_count = sum(1 for r in rows if r[6])
        audio_count = total_tracks - video_count

        # Summary stats
        summary = QtWidgets.QHBoxLayout()
        summary.setSpacing(20)

        def stat_box(label, value):
            box = QtWidgets.QFrame()
            box.setStyleSheet("""
                QFrame {
                    background-color: #2A2A2A;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
            layout = QtWidgets.QVBoxLayout(box)
            lbl = QtWidgets.QLabel(label)
            lbl.setStyleSheet("color: #B3B3B3; font-size: 12px;")
            val = QtWidgets.QLabel(str(value))
            val.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
            layout.addWidget(lbl)
            layout.addWidget(val)
            return box

        summary.addWidget(stat_box("Total Tracks", total_tracks))
        summary.addWidget(stat_box("Total Duration", f"{total_duration // 3600}h {(total_duration % 3600) // 60}m"))
        summary.addWidget(stat_box("Audio Files", audio_count))
        summary.addWidget(stat_box("Video Files", video_count))
        summary.addStretch()

        stats_layout.addLayout(summary)

        # Charts
        charts_layout = QtWidgets.QHBoxLayout()
        charts_layout.setSpacing(20)

        # Pie chart for audio vs video
        pie_series = QPieSeries()
        if audio_count > 0:
            pie_series.append("Audio", audio_count)
        if video_count > 0:
            pie_series.append("Video", video_count)

        pie_chart = QChart()
        pie_chart.addSeries(pie_series)
        pie_chart.setTitle("Audio vs Video")
        pie_chart.setTitleBrush(QtWidgets.QColor("white"))
        pie_chart.legend().setLabelColor(QtWidgets.QColor("white"))
        pie_chart.setBackgroundBrush(QtWidgets.QColor("#121212"))

        pie_view = QChartView(pie_chart)
        pie_view.setFixedSize(300, 300)
        charts_layout.addWidget(pie_view)

        # Bar chart for top artists
        from collections import Counter
        artists = [r[3] for r in rows if r[3]]
        top_artists = Counter(artists).most_common(10)

        bar_set = QBarSet("Tracks")
        categories = []
        for artist, count in top_artists:
            categories.append(artist or "Unknown")
            bar_set.append(count)

        bar_series = QBarSeries()
        bar_series.append(bar_set)

        bar_chart = QChart()
        bar_chart.addSeries(bar_series)
        bar_chart.setTitle("Top Artists")
        bar_chart.setTitleBrush(QtWidgets.QColor("white"))

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsColor(QtWidgets.QColor("white"))
        bar_chart.addAxis(axis_x, QtCore.Qt.AlignBottom)
        bar_series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%d")
        axis_y.setLabelsColor(QtWidgets.QColor("white"))
        bar_chart.addAxis(axis_y, QtCore.Qt.AlignLeft)
        bar_series.attachAxis(axis_y)

        bar_chart.setBackgroundBrush(QtWidgets.QColor("#121212"))
        bar_chart.legend().setLabelColor(QtWidgets.QColor("white"))

        bar_view = QChartView(bar_chart)
        bar_view.setFixedSize(500, 300)
        charts_layout.addWidget(bar_view)

        charts_layout.addStretch()
        stats_layout.addLayout(charts_layout)

        # Recently played list
        recent_title = QtWidgets.QLabel("Recently Played")
        recent_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-top: 20px;")
        stats_layout.addWidget(recent_title)

        recent_list = QtWidgets.QTableWidget()
        recent_list.setColumnCount(4)
        recent_list.setHorizontalHeaderLabels(["Title", "Artist", "Album", "Played At"])
        recent_list.setStyleSheet("""
            QTableWidget {
                background-color: #1A1A1A;
                color: white;
                gridline-color: #333;
            }
            QHeaderView::section {
                background-color: #2A2A2A;
                color: white;
                padding: 5px;
                border: none;
            }
        """)
        recent_list.horizontalHeader().setStretchLastSection(True)

        # Mock data for recently played (replace with real data)
        recent_data = [
            ("Song 1", "Artist 1", "Album 1", "2023-10-01 10:00"),
            ("Song 2", "Artist 2", "Album 2", "2023-10-01 09:00"),
        ]
        recent_list.setRowCount(len(recent_data))
        for i, (title, artist, album, played_at) in enumerate(recent_data):
            recent_list.setItem(i, 0, QtWidgets.QTableWidgetItem(title))
            recent_list.setItem(i, 1, QtWidgets.QTableWidgetItem(artist))
            recent_list.setItem(i, 2, QtWidgets.QTableWidgetItem(album))
            recent_list.setItem(i, 3, QtWidgets.QTableWidgetItem(played_at))

        stats_layout.addWidget(recent_list)

        stats_layout.addStretch()

        self.stats_scroll_area.setWidget(stats_widget)
        self.stats_scroll_area.setWidgetResizable(True)
=======
# app/ui/statistics_mixin.py
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtChart import (
    QChart,
    QChartView,
    QPieSeries,
    QBarSeries,
    QBarSet,
    QBarCategoryAxis,
    QValueAxis,
)


class StatisticsMixin:
    """
    Provides statistics page functionality.
    """

    def _load_statistics_page(self):
        self._generate_statistics()
        self.set_page(3)

    def _generate_statistics(self):
        """Builds charts + lists for the Statistics page."""
        # Clear existing layout
        if self.stats_layout:
            while self.stats_layout.count():
                child = self.stats_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            self.stats_scroll_area.setWidget(None)

        # Create new widget for stats
        stats_widget = QtWidgets.QWidget()
        stats_layout = QtWidgets.QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(20, 20, 20, 20)
        stats_layout.setSpacing(20)

        # Title
        title = QtWidgets.QLabel("Library Statistics")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        stats_layout.addWidget(title)

        # Get data
        rows = self.db.get_all_media("")
        total_tracks = len(rows)
        total_duration = sum(r[5] for r in rows if r[5])
        video_count = sum(1 for r in rows if r[6])
        audio_count = total_tracks - video_count

        # Summary stats
        summary = QtWidgets.QHBoxLayout()
        summary.setSpacing(20)

        def stat_box(label, value):
            box = QtWidgets.QFrame()
            box.setStyleSheet("""
                QFrame {
                    background-color: #2A2A2A;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
            layout = QtWidgets.QVBoxLayout(box)
            lbl = QtWidgets.QLabel(label)
            lbl.setStyleSheet("color: #B3B3B3; font-size: 12px;")
            val = QtWidgets.QLabel(str(value))
            val.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
            layout.addWidget(lbl)
            layout.addWidget(val)
            return box

        summary.addWidget(stat_box("Total Tracks", total_tracks))
        summary.addWidget(stat_box("Total Duration", f"{total_duration // 3600}h {(total_duration % 3600) // 60}m"))
        summary.addWidget(stat_box("Audio Files", audio_count))
        summary.addWidget(stat_box("Video Files", video_count))
        summary.addStretch()

        stats_layout.addLayout(summary)

        # Charts
        charts_layout = QtWidgets.QHBoxLayout()
        charts_layout.setSpacing(20)

        # Pie chart for audio vs video
        pie_series = QPieSeries()
        if audio_count > 0:
            pie_series.append("Audio", audio_count)
        if video_count > 0:
            pie_series.append("Video", video_count)

        pie_chart = QChart()
        pie_chart.addSeries(pie_series)
        pie_chart.setTitle("Audio vs Video")
        pie_chart.setTitleBrush(QtWidgets.QColor("white"))
        pie_chart.legend().setLabelColor(QtWidgets.QColor("white"))
        pie_chart.setBackgroundBrush(QtWidgets.QColor("#121212"))

        pie_view = QChartView(pie_chart)
        pie_view.setFixedSize(300, 300)
        charts_layout.addWidget(pie_view)

        # Bar chart for top artists
        from collections import Counter
        artists = [r[3] for r in rows if r[3]]
        top_artists = Counter(artists).most_common(10)

        bar_set = QBarSet("Tracks")
        categories = []
        for artist, count in top_artists:
            categories.append(artist or "Unknown")
            bar_set.append(count)

        bar_series = QBarSeries()
        bar_series.append(bar_set)

        bar_chart = QChart()
        bar_chart.addSeries(bar_series)
        bar_chart.setTitle("Top Artists")
        bar_chart.setTitleBrush(QtWidgets.QColor("white"))

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsColor(QtWidgets.QColor("white"))
        bar_chart.addAxis(axis_x, QtCore.Qt.AlignBottom)
        bar_series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setLabelFormat("%d")
        axis_y.setLabelsColor(QtWidgets.QColor("white"))
        bar_chart.addAxis(axis_y, QtCore.Qt.AlignLeft)
        bar_series.attachAxis(axis_y)

        bar_chart.setBackgroundBrush(QtWidgets.QColor("#121212"))
        bar_chart.legend().setLabelColor(QtWidgets.QColor("white"))

        bar_view = QChartView(bar_chart)
        bar_view.setFixedSize(500, 300)
        charts_layout.addWidget(bar_view)

        charts_layout.addStretch()
        stats_layout.addLayout(charts_layout)

        # Recently played list
        recent_title = QtWidgets.QLabel("Recently Played")
        recent_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-top: 20px;")
        stats_layout.addWidget(recent_title)

        recent_list = QtWidgets.QTableWidget()
        recent_list.setColumnCount(4)
        recent_list.setHorizontalHeaderLabels(["Title", "Artist", "Album", "Played At"])
        recent_list.setStyleSheet("""
            QTableWidget {
                background-color: #1A1A1A;
                color: white;
                gridline-color: #333;
            }
            QHeaderView::section {
                background-color: #2A2A2A;
                color: white;
                padding: 5px;
                border: none;
            }
        """)
        recent_list.horizontalHeader().setStretchLastSection(True)

        # Mock data for recently played (replace with real data)
        recent_data = [
            ("Song 1", "Artist 1", "Album 1", "2023-10-01 10:00"),
            ("Song 2", "Artist 2", "Album 2", "2023-10-01 09:00"),
        ]
        recent_list.setRowCount(len(recent_data))
        for i, (title, artist, album, played_at) in enumerate(recent_data):
            recent_list.setItem(i, 0, QtWidgets.QTableWidgetItem(title))
            recent_list.setItem(i, 1, QtWidgets.QTableWidgetItem(artist))
            recent_list.setItem(i, 2, QtWidgets.QTableWidgetItem(album))
            recent_list.setItem(i, 3, QtWidgets.QTableWidgetItem(played_at))

        stats_layout.addWidget(recent_list)

        stats_layout.addStretch()

        self.stats_scroll_area.setWidget(stats_widget)
        self.stats_scroll_area.setWidgetResizable(True)
>>>>>>> be9547aaccb1857afa059ff99cc82f20dba6ff7b
        self.stats_layout.addWidget(self.stats_scroll_area)