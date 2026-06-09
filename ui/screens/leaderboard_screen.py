from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from client.api_client import APIClient
from ui.styles import LEADERBOARD_STYLE


class _VisibilityWorker(QThread):
    error = pyqtSignal(str)

    def __init__(self, api, visible: bool):
        super().__init__()
        self.api = api
        self.visible = visible

    def run(self):
        try:
            self.api.set_leaderboard_visibility(self.visible)
        except Exception as e:
            self.error.emit(str(e))


class _LeaderboardLoadWorker(QThread):
    finished = pyqtSignal(dict, object)  # data, visibility (None if not fetched)
    error = pyqtSignal(str)

    def __init__(self, api, year_level, search, page, page_size, fetch_visibility=False):
        super().__init__()
        self.api = api
        self.year_level = year_level
        self.search = search
        self.page = page
        self.page_size = page_size
        self.fetch_visibility = fetch_visibility

    def run(self):
        try:
            visibility = None
            if self.fetch_visibility:
                try:
                    visibility = self.api.get_leaderboard_visibility()
                except Exception:
                    pass
            data = self.api.get_leaderboard(
                year_level=self.year_level,
                search=self.search,
                page=self.page,
                page_size=self.page_size,
            )
            self.finished.emit(data, visibility)
        except Exception as e:
            self.error.emit(str(e))


class LeaderboardScreen(QWidget):
    PAGE_SIZE = 2

    def __init__(self, router):
        super().__init__()
        self.router = router
        self.api = APIClient()
        self._current_page = 1
        self._selected_year: int | None = None
        self._worker: _LeaderboardLoadWorker | None = None
        self._vis_worker: _VisibilityWorker | None = None
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(350)
        self._search_timer.timeout.connect(self._on_search_commit)
        self.setStyleSheet(LEADERBOARD_STYLE)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 20, 40, 20)
        root.setSpacing(16)

        header = QHBoxLayout()
        left_header = QVBoxLayout()

        back_btn = QPushButton("← Back to Dashboard")
        back_btn.setObjectName("LeaderActionButton")
        back_btn.setFixedWidth(180)
        back_btn.clicked.connect(lambda: self.router.navigate("dashboard"))
        left_header.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        titles = QVBoxLayout()
        title = QLabel("Leaderboard")
        title.setObjectName("HeaderTitle")
        titles.addWidget(title)
        left_header.addLayout(titles)

        header.addLayout(left_header)
        header.addStretch()

        self.visibility_toggle = QCheckBox("Visible")
        self.visibility_toggle.setObjectName("VisibilityToggle")
        self.visibility_toggle.toggled.connect(self._on_visibility_changed)
        header.addWidget(self.visibility_toggle)

        root.addLayout(header)

        self.filter_label = QLabel("")
        self.filter_label.setObjectName("HeaderSubtitle")
        root.addWidget(self.filter_label)

        controls = QHBoxLayout()
        controls.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Search student by name...")
        self.search_input.setFixedWidth(260)
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_input.returnPressed.connect(self._on_search_commit)
        controls.addWidget(self.search_input)

        year_lbl = QLabel("Academic year:")
        year_lbl.setObjectName("HeaderSubtitle")
        controls.addWidget(year_lbl)

        self.year_selector = QComboBox()
        self.year_selector.setObjectName("YearSelector")
        self.year_selector.currentIndexChanged.connect(self._on_year_changed)
        controls.addWidget(self.year_selector)

        controls.addStretch()
        root.addLayout(controls)

        self.podium_layout = QHBoxLayout()
        self.podium_layout.setSpacing(16)
        root.addLayout(self.podium_layout)

        self.table_panel = QFrame()
        self.table_panel.setObjectName("LeaderboardPanel")
        panel_layout = QVBoxLayout(self.table_panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        headers = QHBoxLayout()
        headers.setContentsMargins(12, 0, 8, 0)
        headers.setSpacing(0)

        rank_h = QLabel("Rank")
        rank_h.setObjectName("TableHeaderRank")
        rank_h.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        headers.addWidget(rank_h, 1)

        student_h = QLabel("STUDENT")
        student_h.setObjectName("TableHeader")
        student_h.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        headers.addWidget(student_h, 5)

        media_h = QLabel("AVERAGE")
        media_h.setObjectName("TableHeader")
        media_h.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        headers.addWidget(media_h, 2)

        credite_h = QLabel("CREDITS")
        credite_h.setObjectName("TableHeader")
        credite_h.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        headers.addWidget(credite_h, 2)

        panel_layout.addLayout(headers)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setMinimumHeight(160)
        self.list_host = QWidget()
        self.list_layout = QVBoxLayout(self.list_host)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(0)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.list_host)
        panel_layout.addWidget(self.scroll)

        self.table_empty_label = QLabel("No other students below the top 3.")
        self.table_empty_label.setObjectName("HeaderSubtitle")
        self.table_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table_empty_label.hide()
        panel_layout.addWidget(self.table_empty_label)

        pagination = QHBoxLayout()
        pagination.setContentsMargins(0, 8, 0, 4)
        self.prev_btn = QPushButton("← Previous")
        self.prev_btn.setObjectName("NavButton")
        self.prev_btn.clicked.connect(self._prev_page)
        self.page_label = QLabel("")
        self.page_label.setObjectName("HeaderSubtitle")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_btn = QPushButton("Next →")
        self.next_btn.setObjectName("NavButton")
        self.next_btn.clicked.connect(self._next_page)
        pagination.addWidget(self.prev_btn)
        pagination.addStretch()
        pagination.addWidget(self.page_label)
        pagination.addStretch()
        pagination.addWidget(self.next_btn)
        panel_layout.addLayout(pagination)

        root.addWidget(self.table_panel, stretch=1)

        self.empty_label = QLabel(
            "No classmates found for the selected university, major, and year."
        )
        self.empty_label.setObjectName("HeaderSubtitle")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.hide()
        root.addWidget(self.empty_label)

        self.empty_action_btn = QPushButton("Back to leaderboard")
        self.empty_action_btn.setObjectName("LeaderActionButton")
        self.empty_action_btn.setFixedWidth(180)
        self.empty_action_btn.clicked.connect(self._reset_leaderboard_view)
        self.empty_action_btn.hide()
        root.addWidget(self.empty_action_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def on_screen_shown(self):
        self.api = APIClient()
        self._current_page = 1
        self._selected_year = None
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        self._load_leaderboard(reset_year=True, fetch_visibility=True)

    def _on_visibility_changed(self, checked: bool):
        self._vis_worker = _VisibilityWorker(self.api, checked)
        self._vis_worker.error.connect(lambda e: print(f"Failed to update visibility: {e}"))
        self._vis_worker.start()

    def _on_search_changed(self):
        self._search_timer.start()

    def _on_search_commit(self):
        self._current_page = 1
        self._load_leaderboard()

    def _reset_leaderboard_view(self):
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        self._current_page = 1
        self._load_leaderboard()

    def _on_year_changed(self):
        if self.year_selector.currentData() is None:
            return
        self._selected_year = int(self.year_selector.currentData())
        self._current_page = 1
        self._load_leaderboard()

    def _prev_page(self):
        if self._current_page > 1:
            self._current_page -= 1
            self._load_leaderboard()

    def _next_page(self):
        self._current_page += 1
        self._load_leaderboard()

    def _load_leaderboard(self, reset_year: bool = False, fetch_visibility: bool = False):
        if self._worker and self._worker.isRunning():
            try:
                self._worker.finished.disconnect()
                self._worker.error.disconnect()
            except Exception:
                pass

        self._worker = _LeaderboardLoadWorker(
            self.api,
            year_level=self._selected_year,
            search=self.search_input.text().strip() or None,
            page=self._current_page,
            page_size=self.PAGE_SIZE,
            fetch_visibility=fetch_visibility,
        )
        self._worker.finished.connect(
            lambda data, vis: self._on_load_finished(data, vis, reset_year, fetch_visibility)
        )
        self._worker.error.connect(self._on_load_error)
        self._worker.start()

    def _on_load_finished(self, data: dict, visibility, reset_year: bool, had_visibility: bool):
        if had_visibility and visibility is not None:
            self.visibility_toggle.blockSignals(True)
            self.visibility_toggle.setChecked(visibility)
            self.visibility_toggle.blockSignals(False)

        if reset_year or self._selected_year is None:
            self._selected_year = data.get("filter_year_level") or data.get(
                "current_user_year_level", 1
            )

        self._populate_year_selector(data, reset_year)

        uni = data.get("filter_university") or "—"
        major = data.get("filter_major") or "—"
        year = data.get("filter_year_level") or "—"
        total = data.get("total", 0)
        self.filter_label.setText(f"{uni} · {major} · Year {year} · {total} students")

        podium = data.get("podium", [])
        entries = data.get("entries", [])
        self._clear_layout(self.podium_layout)
        self._clear_layout(self.list_layout)

        if not podium and not entries:
            self.table_panel.hide()
            self.empty_label.show()
            self.empty_action_btn.show()
            return

        self.table_panel.show()
        self.empty_label.hide()
        self.empty_action_btn.hide()

        for entry in podium:
            self.podium_layout.addWidget(self._make_podium_card(entry), stretch=1)
        for _ in range(max(0, 3 - len(podium))):
            self.podium_layout.addStretch()

        if entries:
            self.scroll.show()
            self.table_empty_label.hide()
            for entry in entries:
                self.list_layout.addWidget(self._make_row(entry))
            self.list_host.adjustSize()
        else:
            self._clear_layout(self.list_layout)
            self.scroll.hide()
            self.table_empty_label.show()

        total_pages = data.get("total_pages", 0)
        page = data.get("page", 1)
        self._current_page = page
        self.page_label.setText(
            f"Page {page} of {max(total_pages, 1)}" if total_pages else "Page 1"
        )
        self.prev_btn.setEnabled(page > 1)
        self.next_btn.setEnabled(total_pages > 0 and page < total_pages)

    def _on_load_error(self, error_msg: str):
        print(f"Leaderboard error: {error_msg}")

    def _populate_year_selector(self, data: dict, reset: bool):
        levels = data.get("available_year_levels") or [1]
        current = data.get("filter_year_level") or levels[0]

        self.year_selector.blockSignals(True)
        self.year_selector.clear()
        for level in levels:
            self.year_selector.addItem(f"Year {level}", level)
        idx = self.year_selector.findData(current)
        if idx >= 0:
            self.year_selector.setCurrentIndex(idx)
        self._selected_year = current
        self.year_selector.blockSignals(False)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _make_podium_card(self, entry: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("StatCard")
        is_me = entry.get("is_current_user", False)
        card.setProperty("is_me", is_me)
        card.style().unpolish(card)
        card.style().polish(card)

        lay = QVBoxLayout(card)
        lay.setSpacing(6)

        rank_icons = {1: "👑", 2: "🥈", 3: "🥉"}
        rank = QLabel(rank_icons.get(entry["rank"], str(entry["rank"])))
        rank.setObjectName("CardTitle")
        rank.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(rank)

        initial = (entry["display_name"] or "?")[0].upper()
        avatar = QLabel(initial)
        avatar.setObjectName("PodiumAvatar")
        avatar.setFixedSize(48, 48)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignHCenter)

        name_text = entry["display_name"]
        if is_me:
            name_text += " (You)"
        name = QLabel(name_text)
        name.setStyleSheet("font-weight: bold; font-size: 14px;")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(name)

        uni = QLabel(entry["university_name"])
        uni.setObjectName("CardSub")
        uni.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(uni)

        avg = QLabel(f"{entry['weighted_avg']:.2f}")
        avg.setObjectName("CardValue")
        avg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(avg)

        cr = QLabel(f"{entry['credits']} credits")
        cr.setObjectName("CardSub")
        cr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(cr)

        return card

    def _make_row(self, entry: dict) -> QFrame:
        row = QFrame()
        row.setObjectName("LeaderRow")
        row.setMinimumHeight(52)
        is_me = entry.get("is_current_user", False)
        row.setProperty("is_me", is_me)
        row.style().unpolish(row)
        row.style().polish(row)

        grid = QHBoxLayout(row)
        grid.setContentsMargins(12, 0, 8, 0)
        grid.setSpacing(0)

        rank_lbl = QLabel(str(entry["rank"]))
        rank_lbl.setObjectName("RankCell")
        rank_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        student_col = QVBoxLayout()
        student_col.setSpacing(2)
        name_text = entry["display_name"]
        if is_me:
            name_text += " (You)"
        name = QLabel(name_text)
        name.setStyleSheet("font-weight: bold;")
        meta = QLabel(f"{entry['university_name']} · Year {entry['year_level']}")
        meta.setObjectName("CardSub")
        student_col.addWidget(name)
        student_col.addWidget(meta)

        avg = QLabel(f"{entry['weighted_avg']:.2f}")
        avg.setObjectName("RowAvgMe" if is_me else "RowAvg")
        avg.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        credits = QLabel(f"{entry['credits']} credits")
        credits.setObjectName("CardSub")
        credits.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        grid.addWidget(rank_lbl, 1)
        grid.addLayout(student_col, 5)
        grid.addWidget(avg, 2)
        grid.addWidget(credits, 2)
        return row
