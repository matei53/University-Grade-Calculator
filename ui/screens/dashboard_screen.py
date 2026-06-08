from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from client.api_client import APIClient
from models.session import Session
from services.dashboard_service import DashboardService
from ui.components.collapsible_year import CollapsibleYear
from ui.styles import DASHBOARD_STYLE


class DashboardScreen(QWidget):

    def __init__(self, router):
        super().__init__()
        self.router = router
        self.all_data = {}
        self.year_buttons = []
        self.year_components = {}
        self.api_client = APIClient()
        self.setStyleSheet(DASHBOARD_STYLE)
        self._build_ui()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 20, 40, 20)
        self.main_layout.setSpacing(20)

        # 1. Header
        header_layout = QHBoxLayout()
        title_container = QVBoxLayout()

        self.header_title = QLabel("UniGrade")
        self.header_title.setObjectName("HeaderTitle")
        self.subtitle = QLabel("Welcome")
        self.subtitle.setObjectName("HeaderSubtitle")

        title_container.addWidget(self.header_title)
        title_container.addWidget(self.subtitle)
        header_layout.addLayout(title_container)
        header_layout.addStretch()

        # leaderboard 
        leaderboard_btn = QPushButton("Leaderboard")
        leaderboard_btn.setFixedWidth(100)
        leaderboard_btn.setStyleSheet("background-color: #ffffff; border: 1px solid #ccc; border-radius: 6px; padding: 6px;")
        leaderboard_btn.clicked.connect(lambda: self.router.navigate("leaderboard"))

        # Add Subject button
        add_subject_btn = QPushButton("+ Add Subject")
        add_subject_btn.setFixedWidth(140)
        add_subject_btn.setStyleSheet(
            "background-color: #A8C686; color: #0A0D08; font-weight: bold; \
            border-radius: 6px; padding: 6px;"
        )
        add_subject_btn.clicked.connect(
            lambda: self.router.navigate("subject_setup")
        )

        logout_btn = QPushButton("Log Out")
        logout_btn.setFixedWidth(90)
        logout_btn.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #ccc; \
            border-radius: 6px; padding: 6px;"
        )
        logout_btn.clicked.connect(self._handle_logout)
        
        header_layout.addWidget(leaderboard_btn)  
        header_layout.addWidget(add_subject_btn)
        header_layout.addWidget(logout_btn)
        self.main_layout.addLayout(header_layout)

        # 2. Filter Bar
        self.filter_layout = QHBoxLayout()
        self.main_layout.addLayout(self.filter_layout)

        # 3. Main Stats Cards
        stats_layout = QHBoxLayout()
        self.media_card = self._create_stat_card("WEIGHTED AVERAGE", "0.00")
        self.credits_card = self._create_stat_card("CREDITS", "0")
        self.progress_card = self._create_stat_card("PROGRESS", "0%")

        self.main_progress_bar = QProgressBar()
        self.main_progress_bar.setFixedHeight(10)
        self.main_progress_bar.setTextVisible(False)
        self.progress_card.layout().addWidget(self.main_progress_bar)

        stats_layout.addWidget(self.media_card)
        stats_layout.addWidget(self.credits_card)
        stats_layout.addWidget(self.progress_card)
        self.main_layout.addLayout(stats_layout)

        # 4. Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.years_container = QVBoxLayout(self.scroll_content)
        self.years_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(scroll)

    def on_screen_shown(self):
        """Refreshes the UI with real data every time the screen is shown."""
        # Clear any cached API client to ensure fresh token
        self.api_client = APIClient()

        # 1. Fetch real Profile Info (University & Major)
        try:
            profile = self.api_client.get_profile()
            uni = profile.get("university_name") or "No University Set"
            major = profile.get("major_name") or "No Major Set"
            self.subtitle.setText(f"{uni} | {major}")
        except Exception as e:
            print(f"Error fetching profile: {e}")
            self.subtitle.setText("Loading...")

        # 2. Load Academic Data for Stats
        try:
            self.all_data = DashboardService.get_user_dashboard_data(None)
        except Exception:
            self.all_data = {}

        self._rebuild_dynamic_ui()

        if self.all_data:
            self.update_dashboard(max(self.all_data.keys()))

    def _rebuild_dynamic_ui(self):
        """Metoda sigură de curățare a layout-urilor pentru a evita
        crash-ul la login."""
        # 1. Curățare Filtre
        while self.filter_layout.count():
            item = self.filter_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.year_buttons = []
        filter_label = QLabel("Filter up to:")
        filter_label.setStyleSheet("font-weight: bold; color: #555;")
        self.filter_layout.addWidget(filter_label)

        for y in sorted(self.all_data.keys()):
            btn = QPushButton(f"Year {y}")
            btn.setObjectName("FilterButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda ch, yr=y: self.update_dashboard(yr))
            self.year_buttons.append(btn)
            self.filter_layout.addWidget(btn)
        self.filter_layout.addStretch()

        # 2. Curățare Componente Ani
        while self.years_container.count():
            item = self.years_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.year_components = {}
        for y, data in self.all_data.items():
            comp = CollapsibleYear(f"Year {y}")
            comp.set_subjects(data["subjects"], data["target_credits"])

            # Deschidem cardul automat pentru vizibilitate instantă
            comp.toggle_button.setChecked(True)
            comp._toggle()

            self.years_container.addWidget(comp)
            self.year_components[y] = comp

    def _create_stat_card(self, title, val):
        card = QFrame()
        card.setObjectName("StatCard")
        l_ = QVBoxLayout(card)
        t = QLabel(title)
        t.setObjectName("CardTitle")
        v = QLabel(val)
        v.setObjectName("CardValue")
        l_.addWidget(t)
        l_.addWidget(v)
        return card

    def update_dashboard(self, up_to_yr):

        for b in self.year_buttons:
            is_active = b.text() == f"Year {up_to_yr}"
            b.setProperty("active", is_active)
            b.style().unpolish(b)
            b.style().polish(b)

        # 1. Calculate dynamic total for the progress bar
        total_program_credits = sum(
            year_data["target_credits"] for year_data in self.all_data.values()
        )

        # 2. Get passing grade fallback
        current_passing_grade = getattr(self, "passing_grade", 5.0)

        # 3. Call the stats service with dynamic values
        stats = DashboardService.calculate_stats(
            self.all_data,
            up_to_yr,
            total_program_credits=total_program_credits,
            passing_grade=float(current_passing_grade),
        )

        # 4. Handle Visibility of Year Components
        for y, comp in self.year_components.items():
            comp.setVisible(y <= up_to_yr)

        # 5. Update UI labels
        self.media_card.findChild(QLabel, "CardValue").setText(
            f"{stats['weighted_avg']:.2f}"
        )
        self.credits_card.findChild(QLabel, "CardValue").setText(
            str(stats["credits"])
        )

        p = int(stats["progress"])
        self.progress_card.findChild(QLabel, "CardValue").setText(f"{p}%")
        self.main_progress_bar.setValue(p)

    def _handle_logout(self):
        Session.logout()
        self.router.navigate("login")
