"""
Progression Settings Screen for customizing year advancement requirements.

credit passing percentage: Allows students to modify credit percentage thresholds
credit passing percentage: Shows eligibility status for each year
"""

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from client.api_client import APIClient


class _ProgressionLoadWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client

    def run(self):
        try:
            data = self.api_client.get_all_year_eligibility()
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))


class _ProgressionSaveWorker(QThread):
    finished = pyqtSignal(list, list)

    def __init__(self, api_client, requirements: list):
        super().__init__()
        self.api_client = api_client
        self.requirements = requirements

    def run(self):
        saved_years: list[int] = []
        failed_years: list[tuple[int, str]] = []
        for req in self.requirements:
            try:
                self.api_client.update_progression_requirement(
                    target_year=req["target_year"],
                    credit_percentage=req["credit_percentage"],
                    cumulative=req["cumulative"],
                )
                saved_years.append(req["target_year"])
            except Exception as e:
                failed_years.append((req["target_year"], str(e)))
        self.finished.emit(saved_years, failed_years)


class ProgressionSettingsScreen(QWidget):
    """
    credit passing percentage: UI screen for managing year progression requirements
    credit passing percentage: Displays and allows modification of credit percentage thresholds
    """

    def __init__(self, router):
        super().__init__()
        self.router = router
        self.api_client = APIClient()
        self.eligibility_data = []
        self.requirement_widgets = []
        self._load_worker = None
        self._save_worker = None
        self.setup_ui()

    def setup_ui(self):
        """credit passing percentage: Build the progression settings interface"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 30, 40, 40)
        main_layout.setSpacing(15)

        # credit passing percentage: Navigation header
        header_area = QVBoxLayout()
        back_btn = QPushButton("← Back to Dashboard")
        back_btn.setObjectName("FilterButton")
        back_btn.setFixedWidth(180)
        back_btn.clicked.connect(self.exit_to_dashboard)

        title = QLabel("Year Progression Requirements")
        title.setObjectName("HeaderTitle")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2D4B1D; margin-top: 10px;")

        header_area.addWidget(back_btn)
        header_area.addWidget(title)
        main_layout.addLayout(header_area)

        # credit passing percentage: Info section
        info_label = QLabel(
            "Set the minimum credit percentage required to advance to each year. "
            "You can choose between single-year or cumulative requirements."
        )
        info_label.setWordWrap(True)
        info_label.setObjectName("HeaderSubtitle")
        main_layout.addWidget(info_label)

        # credit passing percentage: Scrollable requirements list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.requirements_layout = QVBoxLayout(self.scroll_content)
        self.requirements_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.requirements_layout.setSpacing(10)
        scroll.setWidget(self.scroll_content)
        main_layout.addWidget(scroll, 1)

        # credit passing percentage: Action buttons
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh Status")
        refresh_btn.setObjectName("PrimaryButton")
        refresh_btn.setFixedWidth(150)
        refresh_btn.clicked.connect(self.load_eligibility_data)

        save_btn = QPushButton("Save Changes")
        save_btn.setObjectName("PrimaryButton")
        save_btn.setFixedWidth(150)
        save_btn.clicked.connect(self.save_all_requirements)

        button_layout.addStretch()
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def on_screen_shown(self):
        """credit passing percentage: Refresh data when screen is displayed"""
        self.api_client = APIClient()
        self.load_eligibility_data()

    def load_eligibility_data(self):
        """credit passing percentage: Fetch current eligibility and requirements from server"""
        if self._load_worker and self._load_worker.isRunning():
            return

        self._load_worker = _ProgressionLoadWorker(self.api_client)
        self._load_worker.finished.connect(self._on_load_finished)
        self._load_worker.error.connect(self._on_load_error)
        self._load_worker.start()

    def _on_load_finished(self, data: list):
        self.eligibility_data = data

        while self.requirements_layout.count():
            item = self.requirements_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.requirement_widgets = []

        if not self.eligibility_data:
            empty_label = QLabel("No academic years found.")
            empty_label.setObjectName("HeaderSubtitle")
            self.requirements_layout.addWidget(empty_label)
            return

        for eligibility in self.eligibility_data:
            card = self._create_requirement_card(eligibility)
            self.requirements_layout.addWidget(card)

    def _on_load_error(self, message: str):
        QMessageBox.critical(self, "Error", f"Failed to load eligibility data: {message}")

    def _create_requirement_card(self, eligibility: dict) -> QFrame:
        """
        credit passing percentage: Create a UI card for a single year's progression requirement
        credit passing percentage: Shows status and allows modification of threshold
        """
        card = QFrame()
        card.setObjectName("StatCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # credit passing percentage: Title showing target year
        target_year = eligibility["target_year"]
        title = QLabel(f"Advancing to Year {target_year}")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #2D4B1D;")
        layout.addWidget(title)

        # credit passing percentage: Status row showing current progress
        status_row = QHBoxLayout()
        earned = eligibility["credits_earned"]
        required = eligibility["credits_required"]
        current_pct = eligibility["current_percentage"]
        is_eligible = eligibility["is_eligible"]

        status_text = f"Earned: {earned}/{required} credits ({current_pct:.1f}%)"
        status_label = QLabel(status_text)
        status_label.setObjectName("HeaderSubtitle")

        # credit passing percentage: Show green checkmark if eligible, red X if not
        eligible_indicator = QLabel("✓ Eligible" if is_eligible else "✗ Not Eligible")
        color = "#2D4B1D" if is_eligible else "#D32F2F"
        eligible_indicator.setStyleSheet(f"color: {color}; font-weight: bold;")

        status_row.addWidget(status_label)
        status_row.addStretch()
        status_row.addWidget(eligible_indicator)
        layout.addLayout(status_row)

        # credit passing percentage: Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #E0E0E0; margin: 0px;")
        layout.addWidget(sep)

        # credit passing percentage: Requirement input row
        requirement_row = QHBoxLayout()

        req_label = QLabel("Required %:")
        req_label.setObjectName("HeaderSubtitle")
        requirement_row.addWidget(req_label)

        # credit passing percentage: Spinner for percentage input
        percentage_spinner = QDoubleSpinBox()
        percentage_spinner.setMinimum(0.0)
        percentage_spinner.setMaximum(100.0)
        percentage_spinner.setValue(eligibility["required_percentage"])
        percentage_spinner.setSuffix(" %")
        percentage_spinner.setFixedWidth(120)
        percentage_spinner.setObjectName("AuthInput")
        requirement_row.addWidget(percentage_spinner)

        requirement_row.addStretch()

        # credit passing percentage: Cumulative checkbox
        cumulative_check = QCheckBox("Cumulative (Years 1 + 2 + ...)")
        cumulative_check.setChecked(eligibility["cumulative"])
        requirement_row.addWidget(cumulative_check)

        layout.addLayout(requirement_row)

        # credit passing percentage: Store widgets for later retrieval when saving
        self.requirement_widgets.append(
            {
                "target_year": target_year,
                "percentage_spinner": percentage_spinner,
                "cumulative_check": cumulative_check,
            }
        )

        return card

    def save_all_requirements(self):
        """
        credit passing percentage: Save all modified progression requirements to server
        credit passing percentage: Attempts every year independently and collects any failures
        credit passing percentage: Reports a per-year breakdown if any saves fail
        """
        if not self.requirement_widgets:
            QMessageBox.warning(self, "Warning", "No requirements to save.")
            return

        if self._save_worker and self._save_worker.isRunning():
            return

        requirements = [
            {
                "target_year": w["target_year"],
                "credit_percentage": w["percentage_spinner"].value(),
                "cumulative": w["cumulative_check"].isChecked(),
            }
            for w in self.requirement_widgets
        ]

        self._save_worker = _ProgressionSaveWorker(self.api_client, requirements)
        self._save_worker.finished.connect(self._on_save_finished)
        self._save_worker.start()

    def _on_save_finished(self, saved_years: list, failed_years: list):
        if not failed_years:
            QMessageBox.information(
                self, "Success", "Progression requirements updated successfully!"
            )
        elif not saved_years:
            error_lines = "\n".join(f"  • Year {yr}: {msg}" for yr, msg in failed_years)
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Failed to save requirements for all years:\n\n{error_lines}",
            )
        else:
            ok_text = ", ".join(f"Year {yr}" for yr in saved_years)
            fail_lines = "\n".join(f"  • Year {yr}: {msg}" for yr, msg in failed_years)
            QMessageBox.warning(
                self,
                "Partial Save",
                f"Saved: {ok_text}\n\nFailed to save:\n{fail_lines}",
            )

        self.load_eligibility_data()

    def exit_to_dashboard(self):
        """credit passing percentage: Navigate back to dashboard"""
        self.router.navigate("dashboard")
