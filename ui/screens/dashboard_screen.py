from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
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
from services.graduation_service import GraduationService
from ui.components.collapsible_year import CollapsibleYear
from ui.styles import DASHBOARD_STYLE

# ---------------------------------------------------------------------------
# Background workers — fetch data without blocking the UI thread
# ---------------------------------------------------------------------------


class _DashboardLoadWorker(QThread):
    finished = pyqtSignal(dict, str, str)  # all_data, uni, major
    error = pyqtSignal(str)

    def run(self):
        try:
            client = APIClient()
            uni, major = "—", "—"
            try:
                profile = client.get_profile()
                uni = profile.get("university_name") or "No University Set"
                major = profile.get("major_name") or "No Major Set"
            except Exception:
                pass
            all_data = DashboardService.get_user_dashboard_data(None)
            self.finished.emit(all_data, uni, major)
        except Exception as e:
            self.error.emit(str(e))


class _GradDataWorker(QThread):
    finished = pyqtSignal(object, object)  # settings dict, assessments list
    error = pyqtSignal(str)

    def run(self):
        try:
            svc = GraduationService()
            settings = svc.get_settings()
            assessments = svc.get_final_assessments()
            self.finished.emit(settings, assessments)
        except Exception as e:
            self.error.emit(str(e))


# ---------------------------------------------------------------------------
# Dashboard screen
# ---------------------------------------------------------------------------


class DashboardScreen(QWidget):

    def __init__(self, router):
        super().__init__()
        self.router = router
        self.all_data = {}
        self.year_buttons = []
        self.total_btn = None
        self.year_components = {}
        self._total_mode = False
        self._overall_avg: Optional[float] = None
        self._grad_settings: dict = {"subject_average_weight": 100.0, "max_grade": 10.0}
        self._grad_assessments: list = []
        self._grad_worker: Optional[_GradDataWorker] = None
        self._dash_worker: Optional[_DashboardLoadWorker] = None
        self._grad_data_loaded: bool = False
        self.api_client = APIClient()
        self._grad_service = GraduationService()
        self.setStyleSheet(DASHBOARD_STYLE)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 20, 40, 20)
        self.main_layout.setSpacing(16)

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

        add_subject_btn = QPushButton("+ Add Subject")
        add_subject_btn.setFixedWidth(140)
        add_subject_btn.setStyleSheet(
            "background-color: #A8C686; color: #0A0D08; font-weight: bold; "
            "border-radius: 6px; padding: 6px;"
        )
        add_subject_btn.clicked.connect(lambda: self.router.navigate("subject_setup"))

        simulator_btn = QPushButton("Grade Simulator")
        simulator_btn.setFixedWidth(140)
        simulator_btn.setStyleSheet(
            "background-color: #A8C686; color: #0A0D08; font-weight: bold; "
            "border-radius: 6px; padding: 6px;"
        )
        simulator_btn.clicked.connect(lambda: self.router.navigate("simulator"))

        logout_btn = QPushButton("Log Out")
        logout_btn.setFixedWidth(90)
        logout_btn.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #ccc; "
            "border-radius: 6px; padding: 6px;"
        )
        logout_btn.clicked.connect(self._handle_logout)

        header_layout.addWidget(add_subject_btn)
        header_layout.addWidget(simulator_btn)
        header_layout.addWidget(logout_btn)
        self.main_layout.addLayout(header_layout)

        # 2. Filter Bar
        self.filter_layout = QHBoxLayout()
        self.main_layout.addLayout(self.filter_layout)

        # 3. Graduation section — ABOVE the stats row, hidden until Total mode
        self.graduation_section = self._build_graduation_section()
        self.graduation_section.setVisible(False)
        self.main_layout.addWidget(self.graduation_section)

        # 4. Main Stats Cards (always visible)
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

        # 5. Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.years_container = QVBoxLayout(self.scroll_content)
        self.years_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(scroll)

    def _build_graduation_section(self) -> QFrame:
        section = QFrame()
        section.setObjectName("StatCard")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Top bar: FINAL GRADE value + loading indicator + manage button
        top_bar = QHBoxLayout()

        grade_title = QLabel("FINAL GRADUATION GRADE")
        grade_title.setObjectName("CardTitle")

        self.final_grade_lbl = QLabel("—")
        self.final_grade_lbl.setObjectName("CardValue")
        self.final_grade_lbl.setStyleSheet("font-size: 28px; font-weight: bold; color: #2D4B1D;")

        self.grad_loading_lbl = QLabel("Loading…")
        self.grad_loading_lbl.setObjectName("CardSub")
        self.grad_loading_lbl.setVisible(False)

        manage_btn = QPushButton("Manage Final Assessments →")
        manage_btn.setObjectName("SecondaryButton")
        manage_btn.clicked.connect(lambda: self.router.navigate("graduation"))

        top_bar.addWidget(grade_title)
        top_bar.addSpacing(12)
        top_bar.addWidget(self.final_grade_lbl)
        top_bar.addWidget(self.grad_loading_lbl)
        top_bar.addStretch()
        top_bar.addWidget(manage_btn)
        layout.addLayout(top_bar)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #E0E0E0; margin: 0px;")
        layout.addWidget(sep)

        # FA list title
        fa_title = QLabel("FINAL ASSESSMENTS")
        fa_title.setObjectName("CardTitle")
        layout.addWidget(fa_title)

        # Scrollable FA list — allow ~6 rows before scrolling
        fa_scroll = QScrollArea()
        fa_scroll.setWidgetResizable(True)
        fa_scroll.setMaximumHeight(220)
        self.fa_list_widget = QWidget()
        self.fa_list_layout = QVBoxLayout(self.fa_list_widget)
        self.fa_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.fa_list_layout.setSpacing(2)
        self.fa_list_layout.setContentsMargins(0, 0, 0, 0)
        fa_scroll.setWidget(self.fa_list_widget)
        layout.addWidget(fa_scroll)

        return section

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

    def _set_stat_cards_compact(self, compact: bool) -> None:
        """Shrink the three stat cards in Total mode to give room to the graduation section."""
        style = (
            "font-size: 20px; font-weight: bold; color: #2D4B1D;"
            if compact
            else "font-size: 32px; font-weight: bold; color: #2D4B1D;"
        )
        for card in (self.media_card, self.credits_card, self.progress_card):
            card.findChild(QLabel, "CardValue").setStyleSheet(style)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_screen_shown(self):
        self.api_client = APIClient()
        self._grad_service = GraduationService()
        self._grad_data_loaded = False

        # Stop stale workers before launching fresh ones
        for w in (self._dash_worker, self._grad_worker):
            if w and w.isRunning():
                try:
                    w.finished.disconnect()
                    w.error.disconnect()
                except Exception:
                    pass

        self._dash_worker = _DashboardLoadWorker(self)
        self._dash_worker.finished.connect(self._on_dashboard_loaded)
        self._dash_worker.error.connect(self._on_dashboard_error)
        self._dash_worker.start()

        # Start graduation prefetch in parallel so Total mode is instant
        self._grad_worker = _GradDataWorker(self)
        self._grad_worker.finished.connect(self._on_grad_data_ready)
        self._grad_worker.error.connect(self._on_grad_data_error)
        self._grad_worker.start()

    def _on_dashboard_loaded(self, all_data: dict, uni: str, major: str):
        self.all_data = all_data
        self.subtitle.setText(f"{uni} | {major}")
        self._rebuild_dynamic_ui()
        if self._total_mode:
            self._show_total_view()
        elif self.all_data:
            self.update_dashboard(max(self.all_data.keys()))

    def _on_dashboard_error(self, error_msg: str):
        self.subtitle.setText("Error loading data")
        print(f"Dashboard load error: {error_msg}")

    def _rebuild_dynamic_ui(self):
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

        self.total_btn = QPushButton("Total")
        self.total_btn.setObjectName("FilterButton")
        self.total_btn.setCheckable(True)
        self.total_btn.clicked.connect(self._show_total_view)
        self.filter_layout.addWidget(self.total_btn)
        self.filter_layout.addStretch()

        while self.years_container.count():
            item = self.years_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.year_components = {}
        for y, data in self.all_data.items():
            comp = CollapsibleYear(f"Year {y}")
            comp.set_subjects(data["subjects"], data["target_credits"])
            comp.toggle_button.setChecked(True)
            comp._toggle()
            self.years_container.addWidget(comp)
            self.year_components[y] = comp

    # ------------------------------------------------------------------
    # Year-filter mode
    # ------------------------------------------------------------------

    def update_dashboard(self, up_to_yr):
        self._total_mode = False

        for b in self.year_buttons:
            is_active = b.text() == f"Year {up_to_yr}"
            b.setProperty("active", is_active)
            b.style().unpolish(b)
            b.style().polish(b)

        if self.total_btn:
            self.total_btn.setProperty("active", False)
            self.total_btn.style().unpolish(self.total_btn)
            self.total_btn.style().polish(self.total_btn)

        total_program_credits = sum(
            year_data["target_credits"] for year_data in self.all_data.values()
        )
        stats = DashboardService.calculate_stats(
            self.all_data,
            up_to_yr,
            total_program_credits=total_program_credits,
            passing_grade=float(getattr(self, "passing_grade", 5.0)),
        )

        for y, comp in self.year_components.items():
            comp.setVisible(y <= up_to_yr)

        self.media_card.findChild(QLabel, "CardValue").setText(f"{stats['weighted_avg']:.2f}")
        self.credits_card.findChild(QLabel, "CardValue").setText(str(stats["credits"]))
        p = int(stats["progress"])
        self.progress_card.findChild(QLabel, "CardValue").setText(f"{p}%")
        self.main_progress_bar.setValue(p)

        self.graduation_section.setVisible(False)
        self._set_stat_cards_compact(False)

    # ------------------------------------------------------------------
    # Total mode
    # ------------------------------------------------------------------

    def _show_total_view(self):
        self._total_mode = True

        # Update button active states
        for b in self.year_buttons:
            b.setProperty("active", False)
            b.style().unpolish(b)
            b.style().polish(b)
        if self.total_btn:
            self.total_btn.setProperty("active", True)
            self.total_btn.style().unpolish(self.total_btn)
            self.total_btn.style().polish(self.total_btn)

        # Show all year components
        for comp in self.year_components.values():
            comp.setVisible(True)

        # Compute stats synchronously (no API call needed)
        if self.all_data:
            total_program_credits = sum(yd["target_credits"] for yd in self.all_data.values())
            max_yr = max(self.all_data.keys())
            stats = DashboardService.calculate_stats(
                self.all_data,
                max_yr,
                total_program_credits=total_program_credits,
                passing_grade=float(getattr(self, "passing_grade", 5.0)),
            )
            self.media_card.findChild(QLabel, "CardValue").setText(f"{stats['weighted_avg']:.2f}")
            self.credits_card.findChild(QLabel, "CardValue").setText(str(stats["credits"]))
            p = int(stats["progress"])
            self.progress_card.findChild(QLabel, "CardValue").setText(f"{p}%")
            self.main_progress_bar.setValue(p)
            self._overall_avg = stats["weighted_avg"] if stats["weighted_avg"] > 0 else None
        else:
            self._overall_avg = None

        self._set_stat_cards_compact(True)
        self.graduation_section.setVisible(True)

        if self._grad_data_loaded:
            # Data already available from background prefetch — show instantly
            self.grad_loading_lbl.setVisible(False)
            final_grade = DashboardService.calculate_graduation_grade(
                self._overall_avg, self._grad_settings, self._grad_assessments
            )
            self.final_grade_lbl.setText(f"{final_grade:.2f}" if final_grade is not None else "—")
            self._rebuild_fa_list(self._grad_assessments)
        else:
            # Still loading from prefetch — show indicator and wait for signal
            self.grad_loading_lbl.setVisible(True)
            self.final_grade_lbl.setText("—")
            self._rebuild_fa_list([])
            if not (self._grad_worker and self._grad_worker.isRunning()):
                self._grad_worker = _GradDataWorker(self)
                self._grad_worker.finished.connect(self._on_grad_data_ready)
                self._grad_worker.error.connect(self._on_grad_data_error)
                self._grad_worker.start()

    def _on_grad_data_ready(self, settings: dict, assessments: list):
        self._grad_data_loaded = True
        self._grad_settings = settings
        self._grad_assessments = assessments
        if not self._total_mode:
            return  # cached silently; _show_total_view will use it when Total is clicked
        self.grad_loading_lbl.setVisible(False)
        final_grade = DashboardService.calculate_graduation_grade(
            self._overall_avg, settings, assessments
        )
        self.final_grade_lbl.setText(f"{final_grade:.2f}" if final_grade is not None else "—")
        self._rebuild_fa_list(assessments)

    def _on_grad_data_error(self, error_msg: str):
        self.grad_loading_lbl.setVisible(False)
        self.final_grade_lbl.setText("—")
        print(f"Graduation data error: {error_msg}")

    # ------------------------------------------------------------------
    # FA list (editable, with pass/fail badge)
    # ------------------------------------------------------------------

    def _rebuild_fa_list(self, assessments: list):
        while self.fa_list_layout.count():
            item = self.fa_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not assessments:
            lbl = QLabel("No final assessments yet. Use 'Manage Final Assessments' to add them.")
            lbl.setObjectName("CardSub")
            lbl.setWordWrap(True)
            self.fa_list_layout.addWidget(lbl)
            return

        for a in assessments:
            self.fa_list_layout.addWidget(self._make_fa_row(a))

    def _make_fa_row(self, data: dict) -> QFrame:
        row = QFrame()
        row.setObjectName("SubjectRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(4, 4, 4, 4)

        passing_grade = float(data.get("passing_grade", 5.0))
        max_score = float(data.get("max_score", 10.0))
        grade_obj = data.get("grade")
        current_score = (
            float(grade_obj["score"]) if grade_obj and grade_obj.get("score") is not None else None
        )
        is_failing = current_score is not None and current_score < passing_grade

        name_lbl = QLabel(data["name"])
        name_lbl.setFixedWidth(180)
        name_lbl.setStyleSheet(
            "font-size: 14px; color: #c0392b; font-weight: bold;"
            if is_failing
            else "font-size: 14px;"
        )

        weight_lbl = QLabel(f"{data['weight']:.1f}%")
        weight_lbl.setFixedWidth(50)
        weight_lbl.setStyleSheet("color: #777; font-size: 13px;")

        score_spin = QDoubleSpinBox()
        score_spin.setRange(0.0, max_score)
        score_spin.setDecimals(2)
        score_spin.setFixedWidth(110)
        score_spin.setValue(current_score if current_score is not None else 0.0)

        a_id = data["id"]
        save_btn = QPushButton("Save")
        save_btn.setObjectName("SecondaryButton")
        save_btn.setMinimumWidth(80)
        save_btn.clicked.connect(lambda _, sid=a_id, sp=score_spin: self._save_grad_score(sid, sp))

        max_lbl = QLabel(f"/{max_score:.0f}")
        max_lbl.setStyleSheet("font-size: 14px; color: #777;")

        if current_score is not None:
            badge_text = "✗ FAIL" if is_failing else "✓ PASS"
            badge_color = "#c0392b" if is_failing else "#27ae60"
            badge = QLabel(badge_text)
            badge.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {badge_color};")
        else:
            badge = QLabel("")
        badge.setFixedWidth(65)

        layout.addWidget(name_lbl)
        layout.addWidget(weight_lbl)
        layout.addWidget(score_spin)
        layout.addWidget(save_btn)
        layout.addWidget(max_lbl)
        layout.addSpacing(6)
        layout.addWidget(badge)
        layout.addStretch()

        return row

    def _save_grad_score(self, assessment_id: int, spin: QDoubleSpinBox):
        score = spin.value()
        try:
            updated = self._grad_service.set_grade(assessment_id, score)
            self._grad_assessments = [
                updated if a["id"] == assessment_id else a for a in self._grad_assessments
            ]
            final_grade = DashboardService.calculate_graduation_grade(
                self._overall_avg, self._grad_settings, self._grad_assessments
            )
            self.final_grade_lbl.setText(f"{final_grade:.2f}" if final_grade is not None else "—")
            self._rebuild_fa_list(self._grad_assessments)
        except Exception as e:
            print(f"Error saving graduation score: {e}")

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _handle_logout(self):
        Session.logout()
        self.router.navigate("login")
