from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QCheckBox, QPushButton, QGridLayout,
)
from PyQt6.QtCore import Qt
from client.api_client import APIClient
from ui.styles import LEADERBOARD_STYLE, FOREST_GREEN, SAGE_GREEN, MIDNIGHT, STONE_GREY

class LeaderboardScreen(QWidget):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.api = APIClient()
        self.setStyleSheet(LEADERBOARD_STYLE)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 24, 40, 24)
        root.setSpacing(20)

        # Header row: title + visibility
        header = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel("Clasament")
        title.setObjectName("PageTitle")
        sub = QLabel("Compară-te cu alți studenți")
        sub.setObjectName("PageSubtitle")
        titles.addWidget(title)
        titles.addWidget(sub)
        header.addLayout(titles)
        header.addStretch()

        self.visibility_toggle = QCheckBox("Vizibil")
        self.visibility_toggle.setObjectName("VisibilityToggle")
        self.visibility_toggle.toggled.connect(self._on_visibility_changed)
        header.addWidget(self.visibility_toggle)
        root.addLayout(header)

        filter_lbl = QLabel("")
        filter_lbl.setObjectName("PageSubtitle")
        self.filter_label = filter_lbl
        root.addWidget(filter_lbl)

        self.podium_layout = QHBoxLayout()
        self.podium_layout.setSpacing(16)
        root.addLayout(self.podium_layout)

        # Table headers
        headers = QHBoxLayout()
        for text, stretch in [("#", 1), ("STUDENT", 5), ("MEDIA", 2), ("CREDITE", 2)]:
            h = QLabel(text)
            h.setObjectName("TableHeader")
            headers.addWidget(h, stretch)
        root.addLayout(headers)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.list_host = QWidget()
        self.list_layout = QVBoxLayout(self.list_host)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.list_host)
        root.addWidget(scroll)

        back_btn = QPushButton("← Dashboard")
        back_btn.clicked.connect(lambda: self.router.navigate("dashboard"))
        root.addWidget(back_btn)

    def on_screen_shown(self):
        self.api = APIClient()
        try:
            visible = self.api.get_leaderboard_visibility()
            self.visibility_toggle.blockSignals(True)
            self.visibility_toggle.setChecked(visible)
            self.visibility_toggle.blockSignals(False)
        except Exception as e:
            print(f"Visibility error: {e}")
        self._load_leaderboard()

    def _on_visibility_changed(self, checked: bool):
        try:
            self.api.set_leaderboard_visibility(checked)
        except Exception as e:
            print(f"Failed to update visibility: {e}")

    def _load_leaderboard(self):
        try:
            data = self.api.get_leaderboard()
        except Exception as e:
            print(f"Leaderboard error: {e}")
            return

        uni = data.get("filter_university") or "—"
        major = data.get("filter_major") or "—"
        self.filter_label.setText(f"{uni} · {major}")

        entries = data.get("entries", [])
        self._clear_layout(self.podium_layout)
        self._clear_layout(self.list_layout)

        for entry in entries[:3]:
            self.podium_layout.addWidget(self._make_podium_card(entry))

        for entry in entries[3:]:
            self.list_layout.addWidget(self._make_row(entry))

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _make_podium_card(self, entry: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("PodiumCard")
        card.setMinimumWidth(200)
        lay = QVBoxLayout(card)
        rank_icons = {1: "👑", 2: "🥈", 3: "🥉"}
        lay.addWidget(QLabel(rank_icons.get(entry["rank"], str(entry["rank"]))))
        initial = (entry["display_name"] or "?")[0].upper()
        avatar = QLabel(initial)
        avatar.setFixedSize(48, 48)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            f"background:{SAGE_GREEN}; border-radius:24px; font-weight:bold;"
        )
        lay.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignHCenter)
        name = QLabel(entry["display_name"])
        name.setStyleSheet("font-weight:bold; font-size:14px;")
        lay.addWidget(name, alignment=Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(
            QLabel(entry["university_short"]),
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )
        avg = QLabel(f"{entry['weighted_avg']:.2f}")
        avg.setObjectName("PodiumAvg")
        lay.addWidget(avg, alignment=Qt.AlignmentFlag.AlignHCenter)
        cr = QLabel(f"{entry['credits']} cr")
        cr.setObjectName("PodiumCredits")
        lay.addWidget(cr, alignment=Qt.AlignmentFlag.AlignHCenter)
        return card

    def _make_row(self, entry: dict) -> QFrame:
        row = QFrame()
        row.setObjectName("LeaderRow")
        is_me = entry.get("is_current_user", False)
        row.setProperty("is_me", is_me)
        row.style().unpolish(row)
        row.style().polish(row)

        grid = QHBoxLayout(row)
        rank_lbl = QLabel(str(entry["rank"]))
        student_col = QVBoxLayout()
        name_text = entry["display_name"]
        if is_me:
            name_text += " (Tu)"
        name = QLabel(name_text)
        name.setStyleSheet("font-weight:bold;")
        meta = QLabel(f"{entry['university_short']} · Anul {entry['year_level']}")
        meta.setStyleSheet(f"color:{STONE_GREY}; font-size:11px;")
        student_col.addWidget(name)
        student_col.addWidget(meta)

        avg = QLabel(f"{entry['weighted_avg']:.2f}")
        if is_me:
            avg.setObjectName("RowAvgMe")
        credits = QLabel(f"{entry['credits']} cr")
        credits.setStyleSheet(f"color:{STONE_GREY};")

        grid.addWidget(rank_lbl, 1)
        grid.addLayout(student_col, 5)
        grid.addWidget(avg, 2)
        grid.addWidget(credits, 2)
        return row