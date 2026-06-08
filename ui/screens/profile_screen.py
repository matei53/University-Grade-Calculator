from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from client.api_client import APIClient
from models.session import Session
from ui.styles import DASHBOARD_STYLE


class ProfileScreen(QWidget):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.api_client = APIClient()
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

        self.main_layout.addWidget(QLabel("Select University"))
        self.main_layout.addWidget(self.university_combo)
        self.main_layout.addWidget(QLabel("Select Major"))
        self.main_layout.addWidget(self.major_combo)

        self.update_btn = QPushButton("Update Profile")
        self.update_btn.setObjectName("PrimaryButton")
        self.update_btn.setFixedHeight(45)
        self.update_btn.clicked.connect(self._handle_update_profile)
        self.main_layout.addWidget(self.update_btn)

        self.delete_btn = QPushButton("Delete Account")
        self.delete_btn.setObjectName("DangerButton")
        self.delete_btn.setStyleSheet(
            "background-color: #cc0000; color: #ffffff; border-radius: 8px; padding: 10px;"
        )
        self.delete_btn.setFixedHeight(45)
        self.delete_btn.clicked.connect(self._handle_delete_account)
        self.main_layout.addWidget(self.delete_btn)

        self.main_layout.addStretch()

    def on_screen_shown(self):
        self.api_client = APIClient()
        self._load_profile_info()
        self._load_select_options()

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

    def _load_select_options(self):
        self.university_combo.clear()
        self.major_combo.clear()

        self.university_combo.addItem("No change", -1)
        self.major_combo.addItem("No change", -1)

        try:
            universities = self.api_client.get_universities()
            for uni in universities:
                self.university_combo.addItem(uni["name"], uni["id"])
        except Exception as error:
            QMessageBox.warning(self, "Load Error", f"Unable to load universities: {error}")

        try:
            majors = self.api_client.get_majors()
            for major in majors:
                self.major_combo.addItem(major["name"], major["id"])
        except Exception as error:
            QMessageBox.warning(self, "Load Error", f"Unable to load majors: {error}")

    def _handle_update_profile(self):
        university_id = self.university_combo.currentData()
        major_id = self.major_combo.currentData()

        payload = {}
        if university_id is not None and university_id != -1:
            payload["university_id"] = university_id
        if major_id is not None and major_id != -1:
            payload["major_id"] = major_id

        if not payload:
            QMessageBox.information(self, "No changes", "Choose a new university or major before updating.")
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
        self.router.navigate("dashboard")
