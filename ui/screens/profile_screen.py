from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from client.api_client import APIClient
from models.session import Session
from ui.styles import DASHBOARD_STYLE


class _ProfileLoadWorker(QThread):
    finished = pyqtSignal(dict, list, list)  # profile, universities, majors
    error = pyqtSignal(str)

    def run(self):
        try:
            api_client = APIClient()
            profile = api_client.get_profile()
            universities = api_client.get_universities()
            majors = api_client.get_majors()
            self.finished.emit(profile, universities, majors)
        except Exception as e:
            self.error.emit(str(e))


class _CareerGuidanceWorker(QThread):
    result_ready = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, api_client):
        super().__init__()
        self._api_client = api_client

    def run(self):
        try:
            from agents.career_advisor import run_career_guidance

            self.result_ready.emit(run_career_guidance(self._api_client))
        except Exception as e:
            self.error.emit(str(e))


class ProfileScreen(QWidget):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.api_client = APIClient()
        self._worker: Optional[_ProfileLoadWorker] = None
        self._career_worker: Optional[_CareerGuidanceWorker] = None
        self.setStyleSheet(DASHBOARD_STYLE)
        self._build_ui()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 20, 40, 20)
        self.main_layout.setSpacing(16)

        header_layout = QHBoxLayout()
        title = QLabel("Profile Management")
        title.setObjectName("HeaderTitle")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2D4B1D;")

        back_btn = QPushButton("← Back")
        back_btn.setFixedWidth(100)
        back_btn.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #ccc; border-radius: 6px; padding: 6px;"
        )
        back_btn.clicked.connect(self._back_to_dashboard)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(back_btn)
        self.main_layout.addLayout(header_layout)

        self.current_university_label = QLabel("University: —")
        self.current_major_label = QLabel("Major: —")
        self.main_layout.addWidget(self.current_university_label)
        self.main_layout.addWidget(self.current_major_label)

        self.university_combo = QComboBox()
        self.university_combo.setObjectName("AuthInput")
        self.major_combo = QComboBox()
        self.major_combo.setObjectName("AuthInput")

        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(10)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)

        university_label = QLabel("Select University:")
        university_label.setStyleSheet("font-weight: 600; color: #2D4B1D;")
        major_label = QLabel("Select Major:")
        major_label.setStyleSheet("font-weight: 600; color: #2D4B1D;")

        form_layout.addRow(university_label, self.university_combo)
        form_layout.addRow(major_label, self.major_combo)

        self.main_layout.addLayout(form_layout)

        self.update_btn = QPushButton("Update Profile")
        self.update_btn.setObjectName("PrimaryButton")
        self.update_btn.setFixedHeight(45)
        self.update_btn.clicked.connect(self._handle_update_profile)
        self.main_layout.addWidget(self.update_btn)

        self.main_layout.addSpacing(25)

        self.delete_btn = QPushButton("Delete Account")
        self.delete_btn.setObjectName("DangerButton")
        self.delete_btn.setStyleSheet(
            "background-color: #cc0000; color: #ffffff; border-radius: 8px; padding: 10px;"
        )
        self.delete_btn.setFixedHeight(45)
        self.delete_btn.clicked.connect(self._handle_delete_account)
        self.main_layout.addWidget(self.delete_btn)

        self.main_layout.addSpacing(30)
        self._build_career_advisor_section()
        self.main_layout.addWidget(self.ai_group_box)

        self.main_layout.addStretch()

    def on_screen_shown(self):
        self.api_client = APIClient()
        if self._worker and self._worker.isRunning():
            try:
                self._worker.finished.disconnect()
                self._worker.error.disconnect()
            except Exception:
                pass
            self._worker.finished.connect(self._worker.deleteLater)
        self._worker = _ProfileLoadWorker()
        self._worker.finished.connect(self._on_data_loaded)
        self._worker.error.connect(lambda e: QMessageBox.warning(self, "Load Error", e))
        self._worker.start()

    def _on_data_loaded(self, profile: dict, universities: list, majors: list):
        university = profile.get("university_name") or "—"
        major = profile.get("major_name") or "—"
        self.current_university_label.setText(f"University: {university}")
        self.current_major_label.setText(f"Major: {major}")

        self.university_combo.clear()
        self.major_combo.clear()
        self.university_combo.addItem("No change", -1)
        self.major_combo.addItem("No change", -1)
        for uni in universities:
            self.university_combo.addItem(uni["name"], uni["id"])
        for m in majors:
            self.major_combo.addItem(m["name"], m["id"])

    def _build_career_advisor_section(self):
        advisor_group = QGroupBox("")
        advisor_group.setStyleSheet(
            "QGroupBox { border: 1px solid #cfe8e0; border-radius: 10px; margin-top: 10px; background: #f7fbf9; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 12px; padding: 0 0px; background: transparent; color: #0f4f36; font-weight: bold; }"
        )

        advisor_layout = QVBoxLayout()
        advisor_layout.setContentsMargins(16, 16, 16, 16)
        advisor_layout.setSpacing(12)

        advisor_label = QLabel(
            "Get personalized career path and elective suggestions based on your subjects and grades."
        )
        advisor_label.setWordWrap(True)
        advisor_label.setStyleSheet("color: #3f5a4b; font-size: 12px;")

        self.career_button = QPushButton("Generate Career Guidance")
        self.career_button.setFixedHeight(44)
        self.career_button.setStyleSheet(
            "background-color: #2e7d32; color: white; border-radius: 8px; font-weight: bold;"
        )
        self.career_button.clicked.connect(self._handle_generate_career_guidance)

        self.career_output = QTextEdit()
        self.career_output.setReadOnly(True)
        self.career_output.setMarkdown(
            "### Career guidance will appear here after you click the button."
        )
        self.career_output.setMinimumHeight(220)
        self.career_output.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #cbded8; border-radius: 10px; padding: 12px;"
        )

        advisor_layout.addWidget(advisor_label)
        advisor_layout.addWidget(self.career_button)
        advisor_layout.addWidget(self.career_output)
        advisor_group.setLayout(advisor_layout)

        self.ai_group_box = advisor_group

    def _handle_generate_career_guidance(self):
        self.career_button.setEnabled(False)
        self.career_button.setText("Analyzing your performance...")
        self.career_output.setMarkdown("*Fetching guidance from the AI advisor...*")

        if self._career_worker and self._career_worker.isRunning():
            try:
                self._career_worker.result_ready.disconnect()
                self._career_worker.error.disconnect()
            except Exception:
                pass
            self._career_worker.finished.connect(self._career_worker.deleteLater)

        self._career_worker = _CareerGuidanceWorker(self.api_client)
        self._career_worker.result_ready.connect(self._on_career_guidance_ready)
        self._career_worker.error.connect(self._on_career_guidance_error)
        self._career_worker.start()

    def _on_career_guidance_ready(self, text: str):
        self.career_output.setMarkdown(text)
        self._career_button_ready()

    def _on_career_guidance_error(self, error: str):
        QMessageBox.critical(
            self, "Career Guidance Failed", f"Unable to fetch career guidance: {error}"
        )
        self.career_output.setMarkdown("**Failed to load career guidance.**")
        self._career_button_ready()

    def _career_button_ready(self):
        self.career_button.setEnabled(True)
        self.career_button.setText("Generate Career Guidance")

    def _load_profile_info(self):
        try:
            profile = self.api_client.get_profile()
            university = profile.get("university_name") or "—"
            major = profile.get("major_name") or "—"
            self.current_university_label.setText(f"University: {university}")
            self.current_major_label.setText(f"Major: {major}")
        except Exception as error:
            QMessageBox.warning(self, "Profile Load Error", str(error))
            self.current_university_label.setText("University: —")
            self.current_major_label.setText("Major: —")

    def _handle_update_profile(self):
        university_id = self.university_combo.currentData()
        major_id = self.major_combo.currentData()

        payload = {}
        if university_id is not None and university_id != -1:
            payload["university_id"] = university_id
        if major_id is not None and major_id != -1:
            payload["major_id"] = major_id

        if not payload:
            QMessageBox.information(
                self, "No changes", "Choose a new university or major before updating."
            )
            return

        try:
            self.api_client.update_profile(
                university_id=payload.get("university_id"),
                major_id=payload.get("major_id"),
            )
            QMessageBox.information(self, "Profile Updated", "Your profile has been updated.")
            self._load_profile_info()
        except Exception as error:
            QMessageBox.critical(self, "Update Failed", str(error))

    def _handle_delete_account(self):
        confirm = QMessageBox.critical(
            self,
            "Delete Account",
            "Deleting your account will permanently remove all academic years, subjects, and grades. This cannot be undone. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            self.api_client.delete_account()
            Session.logout()
            QMessageBox.information(self, "Deleted", "Your account has been deleted.")
            self.router.navigate("login")
        except Exception as error:
            QMessageBox.critical(self, "Delete Failed", str(error))

    def _back_to_dashboard(self):
        if self._career_worker and self._career_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Guidance in progress",
                "Career guidance is still being generated. Cancel it and go back?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            try:
                self._career_worker.result_ready.disconnect(self._on_career_guidance_ready)
                self._career_worker.error.disconnect(self._on_career_guidance_error)
            except Exception:
                pass
            self._career_button_ready()
        self.router.navigate("dashboard")
