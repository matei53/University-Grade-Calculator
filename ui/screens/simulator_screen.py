"""
PyQt6 screen for the grade simulator.
Allows students to input a target average and get AI-predicted scores.
"""

from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from agents.grade_simulator import run_simulation
from agents.tools import set_api_client
from ui.styles import DASHBOARD_STYLE


class SimulatorWorker(QThread):
    """Worker thread — runs the agent without blocking the UI."""

    result_ready = pyqtSignal(object)

    def __init__(
        self,
        target: float,
        user_note: str,
        assessment_ids: list[int],
        year_id: Optional[int],
        years_data: list[dict],
        year_label: str,
    ):
        super().__init__()
        self.target = target
        self.user_note = user_note
        self.assessment_ids = assessment_ids
        self.year_id = year_id
        self.years_data = years_data
        self.year_label = year_label

    def run(self):
        try:
            result = run_simulation(
                self.target,
                self.user_note,
                self.assessment_ids,
                self.year_id,
                self.years_data,
                self.year_label,
            )
            self.result_ready.emit(result)
        except Exception as e:
            self.result_ready.emit({"grades": [], "message": f"Error: {e}"})


class SimulatorScreen(QWidget):
    """Grade simulator screen with year filter buttons and AI-predicted scores."""

    def __init__(self, router):
        super().__init__()
        self.router = router
        self.api_client = None
        self.years_data: list[dict] = []
        self.year_buttons: list[QPushButton] = []
        self.selected_year_id: Optional[int] = None
        self.retake_checkboxes: dict[int, QCheckBox] = {}
        # Maps assessment_id -> {"grade_label": QLabel, "predicted_label": QLabel,
        #                         "existing_score": float | None}
        self.assessment_row_info: dict[int, dict] = {}
        self._simulation_ids: set[int] = set()
        self.worker_thread = None
        self.setStyleSheet(DASHBOARD_STYLE)
        self._build_ui()

    # ------------------------------------------------------------------ #
    #  UI construction                                                      #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 20, 40, 20)
        main_layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Grade Simulator")
        title.setObjectName("HeaderTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()

        back_btn = QPushButton("Back to Dashboard")
        back_btn.setFixedWidth(160)
        back_btn.setStyleSheet(
            "background-color: #E0DDD9; border: none; border-radius: 6px; "
            "padding: 6px; font-weight: bold;"
        )
        back_btn.clicked.connect(self._go_back)
        header_layout.addWidget(back_btn)
        main_layout.addLayout(header_layout)

        # Year filter button row
        year_row = QHBoxLayout()
        year_row.setSpacing(8)
        year_label = QLabel("Academic Year:")
        year_label.setStyleSheet("font-weight: bold; color: #555;")
        year_label.setFixedWidth(120)
        year_row.addWidget(year_label)

        self.year_buttons_layout = QHBoxLayout()
        self.year_buttons_layout.setSpacing(8)
        year_row.addLayout(self.year_buttons_layout)
        year_row.addStretch()
        main_layout.addLayout(year_row)

        # Subject / assessment scroll area — expands to fill available space
        self.subjects_scroll = QScrollArea()
        self.subjects_scroll.setWidgetResizable(True)
        self.subjects_scroll.setMinimumHeight(200)
        self.subjects_scroll.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.subjects_content = QWidget()
        self.subjects_layout = QVBoxLayout(self.subjects_content)
        self.subjects_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.subjects_layout.setSpacing(8)
        self.subjects_scroll.setWidget(self.subjects_content)
        main_layout.addWidget(self.subjects_scroll, stretch=1)

        # Target grade
        input_label = QLabel("Step 1: Set Your Target")
        input_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(input_label)

        target_layout = QHBoxLayout()
        target_label_w = QLabel("Target Average (1-10):")
        target_label_w.setFixedWidth(150)
        self.target_spinbox = QDoubleSpinBox()
        self.target_spinbox.setMinimum(1.0)
        self.target_spinbox.setMaximum(10.0)
        self.target_spinbox.setSingleStep(0.1)
        self.target_spinbox.setValue(7.0)
        self.target_spinbox.setFixedWidth(100)
        target_layout.addWidget(target_label_w)
        target_layout.addWidget(self.target_spinbox)
        target_layout.addStretch()
        main_layout.addLayout(target_layout)

        # Notes
        notes_label = QLabel("Step 2: Add Context (Optional)")
        notes_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        main_layout.addWidget(notes_label)

        notes_hint = QLabel(
            "Describe which subjects you find difficult, which ones you "
            "expect to do well in, or how much time you have available."
        )
        notes_hint.setStyleSheet("color: #666; font-size: 12px;")
        notes_hint.setWordWrap(True)
        main_layout.addWidget(notes_hint)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText(
            "Optional: describe your expectations or difficulty per subject..."
        )
        self.notes_edit.setFixedHeight(80)
        main_layout.addWidget(self.notes_edit)

        # Simulate button + response message, centred as a column
        action_outer = QHBoxLayout()
        action_outer.addStretch()

        action_col = QVBoxLayout()
        action_col.setSpacing(8)

        self.simulate_btn = QPushButton("Simulate")
        self.simulate_btn.setObjectName("SecondaryButton")
        self.simulate_btn.setFixedWidth(150)
        self.simulate_btn.clicked.connect(self._run_simulation)
        action_col.addWidget(self.simulate_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Response label — always in layout, text cleared when idle
        self.response_label = QLabel()
        self.response_label.setWordWrap(True)
        self.response_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.response_label.setFixedWidth(420)
        self.response_label.setStyleSheet("color: #555; font-size: 12px;")
        action_col.addWidget(self.response_label)

        action_outer.addLayout(action_col)
        action_outer.addStretch()
        main_layout.addLayout(action_outer)

        main_layout.addStretch()

    # ------------------------------------------------------------------ #
    #  Year filter buttons                                                  #
    # ------------------------------------------------------------------ #

    def _populate_year_buttons(self):
        """Rebuild the year filter button strip from self.years_data."""
        # Clear existing buttons
        while self.year_buttons_layout.count():
            item = self.year_buttons_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.year_buttons.clear()

        # "All Years" button — active by default
        all_btn = QPushButton("All Years")
        all_btn.setObjectName("FilterButton")
        all_btn.setProperty("active", True)
        all_btn.clicked.connect(lambda ch: self._on_year_button_clicked(None))
        all_btn._year_id = None  # type: ignore[attr-defined]
        self.year_buttons_layout.addWidget(all_btn)
        self.year_buttons.append(all_btn)

        for year in sorted(self.years_data, key=lambda y: y.get("order_index", 0)):
            lbl = year.get("label") or f"Year {year.get('order_index', '?')}"
            yid = year.get("id")
            btn = QPushButton(lbl)
            btn.setObjectName("FilterButton")
            btn.setProperty("active", False)
            btn.clicked.connect(lambda ch, y=yid: self._on_year_button_clicked(y))
            btn._year_id = yid  # type: ignore[attr-defined]
            self.year_buttons_layout.addWidget(btn)
            self.year_buttons.append(btn)

        # Apply initial stylesheet for active state
        for btn in self.year_buttons:
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_year_button_clicked(self, year_id: Optional[int]):
        """Handle a year filter button click — update active state and display."""
        self.selected_year_id = year_id

        for btn in self.year_buttons:
            is_active = getattr(btn, "_year_id", None) == year_id
            btn.setProperty("active", is_active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self._rebuild_subjects_display()

    # ------------------------------------------------------------------ #
    #  Subject / assessment display                                         #
    # ------------------------------------------------------------------ #

    def _clear_subjects_layout(self):
        while self.subjects_layout.count():
            item = self.subjects_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _rebuild_subjects_display(self):
        """Repopulate the scroll area for the currently selected year."""
        self.retake_checkboxes.clear()
        self.assessment_row_info.clear()
        self._clear_subjects_layout()

        year_id = self.selected_year_id

        if year_id is None:
            years_to_show = sorted(self.years_data, key=lambda y: y.get("order_index", 0))
        else:
            years_to_show = [y for y in self.years_data if y.get("id") == year_id]

        if not years_to_show:
            self.subjects_layout.addWidget(QLabel("No academic data available."))
            return

        for year in years_to_show:
            if year_id is None:
                # Year heading only when viewing all years
                heading_text = (year.get("label") or f"Year {year.get('order_index', '?')}").upper()
                heading = QLabel(heading_text)
                heading.setObjectName("SemesterHeader")
                self.subjects_layout.addWidget(heading)

            subjects = year.get("subjects", [])
            if not subjects:
                no_sub = QLabel("No subjects recorded for this year.")
                no_sub.setStyleSheet("color: #999; font-size: 11px; font-style: italic;")
                self.subjects_layout.addWidget(no_sub)
                continue

            # Group subjects by semester
            semesters = sorted(set(s.get("semester_index", 1) for s in subjects))
            for sem in semesters:
                sem_subjects = [s for s in subjects if s.get("semester_index", 1) == sem]
                if not sem_subjects:
                    continue

                sem_lbl = QLabel(f"SEMESTER {sem}")
                sem_lbl.setObjectName("SemesterHeader")
                self.subjects_layout.addWidget(sem_lbl)

                for subject in sem_subjects:
                    self._add_subject_card(subject)

    def _add_subject_card(self, subject: dict):
        """Add a MiniStatCard frame for a single subject with its assessments."""
        card = QFrame()
        card.setObjectName("MiniStatCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 8)
        card_layout.setSpacing(4)

        # Subject header: bold name + credits
        header = QHBoxLayout()
        name_lbl = QLabel(subject.get("name", "Unknown"))
        name_lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
        credits_lbl = QLabel(f"{subject.get('credit_value', 0)} Credits")
        credits_lbl.setStyleSheet("color: #888; font-size: 11px;")
        header.addWidget(name_lbl)
        header.addStretch()
        header.addWidget(credits_lbl)
        card_layout.addLayout(header)

        assessments = subject.get("assessments", [])
        if not assessments:
            no_a = QLabel("No assessments")
            no_a.setStyleSheet("color: #999; font-size: 11px; font-style: italic;")
            card_layout.addWidget(no_a)
        else:
            for assessment in assessments:
                self._add_assessment_row(card_layout, assessment)

        self.subjects_layout.addWidget(card)

    def _add_assessment_row(self, parent_layout: QVBoxLayout, assessment: dict):
        """
        Add a single assessment row.

        Graded assessments receive a 'Can retake' checkbox so the user can
        opt to include them in the simulation.  Ungraded assessments are
        automatically eligible and carry no checkbox.
        """
        assessment_id = assessment.get("id")
        a_name = assessment.get("name", "Assessment")
        weight = assessment.get("weight", 0)
        grades = assessment.get("grades", [])
        existing_score: Optional[float] = None
        if grades:
            s = grades[0].get("score")
            if s is not None:
                existing_score = float(s)

        row_widget = QWidget()
        row = QHBoxLayout(row_widget)
        row.setContentsMargins(16, 2, 0, 2)
        row.setSpacing(8)

        name_lbl = QLabel(a_name)
        name_lbl.setStyleSheet("font-size: 12px;")
        name_lbl.setWordWrap(True)

        weight_lbl = QLabel(f"{weight}%")
        weight_lbl.setStyleSheet("color: #666; font-size: 11px;")

        # Current grade display label (mutable — updated post-simulation)
        grade_lbl = QLabel()
        if existing_score is not None:
            grade_lbl.setText(f"{existing_score:.1f}")
            grade_lbl.setStyleSheet("font-weight: bold; color: #2D4B1D; font-size: 12px;")
        else:
            grade_lbl.setText("Not Graded")
            grade_lbl.setStyleSheet("color: #999; font-size: 11px; font-style: italic;")

        # Predicted score label — hidden until simulation results arrive
        predicted_lbl = QLabel()
        predicted_lbl.setStyleSheet("font-weight: bold; color: #2D4B1D; font-size: 12px;")
        predicted_lbl.setVisible(False)

        row.addWidget(name_lbl)
        row.addWidget(weight_lbl)
        row.addStretch()
        row.addWidget(grade_lbl)
        row.addWidget(predicted_lbl)

        # Checkbox only for assessments that already have a grade
        if existing_score is not None and assessment_id is not None:
            retake_box = QCheckBox("Can retake")
            self.retake_checkboxes[assessment_id] = retake_box
            row.addWidget(retake_box)
        parent_layout.addWidget(row_widget)

        if assessment_id is not None:
            self.assessment_row_info[assessment_id] = {
                "grade_label": grade_lbl,
                "predicted_label": predicted_lbl,
                "existing_score": existing_score,
            }

    # ------------------------------------------------------------------ #
    #  Data helpers                                                         #
    # ------------------------------------------------------------------ #

    def set_api_client_instance(self, api_client):
        self.api_client = api_client
        set_api_client(api_client)

    def _load_years_data(self):
        if self.api_client is None:
            self.years_data = []
            return
        try:
            self.years_data = self.api_client.get_academic_years()
        except Exception:
            self.years_data = []

    def _get_selected_year_label(self) -> str:
        if self.selected_year_id is None:
            return "All Years"
        for year in self.years_data:
            if year.get("id") == self.selected_year_id:
                return year.get("label") or f"Year {year.get('order_index', '?')}"
        return "All Years"

    def _assessment_has_grade(self, assessment: dict) -> bool:
        grades = assessment.get("grades", [])
        if not grades:
            return False
        return grades[0].get("score") is not None

    def _collect_assessment_ids(self) -> list[int]:
        """Return IDs of assessments that are ungraded or marked as retakeable."""
        assessment_ids: list[int] = []
        year_id = self.selected_year_id

        years_to_scan = self.years_data
        if year_id is not None:
            years_to_scan = [y for y in self.years_data if y.get("id") == year_id]

        for year in years_to_scan:
            for subject in year.get("subjects", []):
                for assessment in subject.get("assessments", []):
                    a_id = assessment.get("id")
                    if a_id is None:
                        continue
                    is_retakeable = (
                        a_id in self.retake_checkboxes and self.retake_checkboxes[a_id].isChecked()
                    )
                    if is_retakeable or not self._assessment_has_grade(assessment):
                        assessment_ids.append(a_id)

        return assessment_ids

    # ------------------------------------------------------------------ #
    #  Simulation                                                           #
    # ------------------------------------------------------------------ #

    def _reset_assessment_display(self):
        """Restore every assessment row to its pre-simulation state."""
        for info in self.assessment_row_info.values():
            grade_lbl: QLabel = info["grade_label"]
            predicted_lbl: QLabel = info["predicted_label"]
            existing_score: Optional[float] = info["existing_score"]

            predicted_lbl.setVisible(False)
            predicted_lbl.setText("")

            grade_lbl.setTextFormat(Qt.TextFormat.AutoText)
            grade_lbl.setVisible(True)
            if existing_score is not None:
                grade_lbl.setText(f"{existing_score:.1f}")
                grade_lbl.setStyleSheet("font-weight: bold; color: #2D4B1D; font-size: 12px;")
            else:
                grade_lbl.setText("Not Graded")
                grade_lbl.setStyleSheet("color: #999; font-size: 11px; font-style: italic;")

    def _set_controls_enabled(self, enabled: bool) -> None:
        """Enable or disable interactive controls during simulation."""
        self.simulate_btn.setEnabled(enabled)
        for btn in self.year_buttons:
            btn.setEnabled(enabled)
        for cb in self.retake_checkboxes.values():
            cb.setEnabled(enabled)

    def _run_simulation(self):
        target = self.target_spinbox.value()
        assessment_ids = self._collect_assessment_ids()
        year_label = self._get_selected_year_label()

        scoped_years = (
            self.years_data
            if self.selected_year_id is None
            else [y for y in self.years_data if y.get("id") == self.selected_year_id]
        )

        self._simulation_ids = set(assessment_ids)
        self._reset_assessment_display()
        self.response_label.clear()
        self._set_controls_enabled(False)
        self.response_label.setText("Thinking…")

        if self.worker_thread is not None and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()

        self.worker_thread = SimulatorWorker(
            target,
            self.notes_edit.toPlainText(),
            assessment_ids,
            self.selected_year_id,
            scoped_years,
            year_label,
        )
        self.worker_thread.result_ready.connect(self._on_result_ready)
        self.worker_thread.start()

    def _on_result_ready(self, result: dict):
        """Update assessment rows with predicted scores, then show/hide message."""
        self._set_controls_enabled(True)

        grades = result.get("grades", [])

        for entry in grades:
            a_id = entry.get("assessment_id")
            predicted_score = entry.get("predicted_score")
            if a_id is None or predicted_score is None:
                continue
            if a_id not in self._simulation_ids:
                continue

            info = self.assessment_row_info.get(a_id)
            if info is None:
                continue

            grade_lbl: QLabel = info["grade_label"]
            predicted_lbl: QLabel = info["predicted_label"]
            existing_score: Optional[float] = info["existing_score"]

            if existing_score is not None:
                # Strikethrough old grade in grey, new score shown separately
                grade_lbl.setTextFormat(Qt.TextFormat.RichText)
                grade_lbl.setText(f'<s style="color:#888;">{existing_score:.1f}</s>')
            else:
                # No prior grade — hide the "Not Graded" label
                grade_lbl.setVisible(False)

            predicted_lbl.setText(f"{predicted_score:.1f}")
            predicted_lbl.setVisible(True)

        self.response_label.setText(result.get("message", ""))

    # ------------------------------------------------------------------ #
    #  Navigation / lifecycle                                               #
    # ------------------------------------------------------------------ #

    def _go_back(self):
        self.router.navigate("dashboard")

    def on_screen_shown(self):
        self.response_label.clear()
        self.notes_edit.clear()
        self.target_spinbox.setValue(7.0)
        self.selected_year_id = None
        self._load_years_data()
        self._populate_year_buttons()
        self._rebuild_subjects_display()
