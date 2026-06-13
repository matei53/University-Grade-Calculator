# ui/screens/signup_screen.py
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from models.session import Session
from services.auth_service import AuthService
from services.data_service import DataService
from ui.components.major_picker import MajorPicker
from ui.components.university_picker import UniversityPicker
from ui.styles import AUTH_STYLE


class _SignupWorker(QThread):
    success = pyqtSignal(str, bool, bool)  # token, used_custom_uni, used_custom_major
    failure = pyqtSignal(str)

    def __init__(  # noqa: PLR0913
        self,
        username,
        password,
        num_years,
        credit_requirements,
        university_id,
        major_id,
        custom_university,
        custom_major,
    ):
        super().__init__()
        self._username = username
        self._password = password
        self._num_years = num_years
        self._credits = credit_requirements
        self._uni_id = university_id
        self._major_id = major_id
        self._custom_uni = custom_university
        self._custom_major = custom_major

    def run(self):  # noqa: C901
        try:
            auth = AuthService()

            if self._custom_uni:
                try:
                    self._uni_id = DataService.add_university(self._custom_uni)
                except ValueError as e:
                    self.failure.emit(f"Error adding university: {e}")
                    return

            if self._custom_major:
                try:
                    self._major_id = DataService.add_major(self._custom_major)
                except ValueError as e:
                    self.failure.emit(f"Error adding major: {e}")
                    return

            response = auth.sign_up(self._username, self._password, self._num_years, self._credits)
            token = response.get("access_token", "")
            if token:
                auth.client.token = token

            if self._uni_id or self._major_id:
                auth.client.update_profile(
                    university_id=self._uni_id or None,
                    major_id=self._major_id or None,
                )

            user_profile = auth.client.get_profile()
            Session.login(
                {"id": user_profile.get("id"), "username": self._username, "token": token}
            )
            self.success.emit(token, bool(self._custom_uni), bool(self._custom_major))
        except ValueError as e:
            self.failure.emit(str(e))


class SignupScreen(QWidget):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.auth_service = AuthService()
        self._worker = None
        self.setStyleSheet(AUTH_STYLE)
        self.credit_requirement_inputs = []
        self._build_ui()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(15)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Title
        title = QLabel("UniGrade")
        title.setObjectName("AuthTitle")
        self.main_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Create Account")
        subtitle.setObjectName("AuthSubtitle")
        self.main_layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addSpacing(20)

        # Scrollable content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(15)
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Input fields
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setObjectName("AuthInput")
        self.username_input.setFixedWidth(300)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setObjectName("AuthInput")
        self.password_input.setFixedWidth(300)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Confirm Password")
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setObjectName("AuthInput")
        self.confirm_input.setFixedWidth(300)

        self.university_picker = UniversityPicker()
        self.university_picker.setFixedWidth(300)

        self.major_picker = MajorPicker()
        self.major_picker.setFixedWidth(300)

        years_label = QLabel("Number of Years in Your Program:")
        years_label.setObjectName("AuthLabel")
        self.years_spinbox = QSpinBox()
        self.years_spinbox.setMinimum(1)
        self.years_spinbox.setMaximum(10)
        self.years_spinbox.setValue(3)
        self.years_spinbox.setFixedWidth(300)
        self.years_spinbox.valueChanged.connect(self._update_credit_inputs)

        scroll_layout.addWidget(
            self.username_input,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        scroll_layout.addWidget(
            self.password_input,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        scroll_layout.addWidget(self.confirm_input, alignment=Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(
            self.university_picker,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        scroll_layout.addWidget(self.major_picker, alignment=Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(years_label, alignment=Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(self.years_spinbox, alignment=Qt.AlignmentFlag.AlignCenter)

        # Container for credit requirement inputs
        self.credit_container = QWidget()
        self.credit_layout = QVBoxLayout(self.credit_container)
        self.credit_layout.setContentsMargins(0, 0, 0, 0)
        self.credit_layout.setSpacing(10)
        self.credit_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(
            self.credit_container,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        scroll_area.setWidget(scroll_content)
        self.main_layout.addWidget(scroll_area)

        self.main_layout.addSpacing(10)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorLabel")
        self.main_layout.addWidget(self.error_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addSpacing(10)

        # Buttons
        self.signup_btn = QPushButton("Sign Up")
        self.signup_btn.setObjectName("PrimaryButton")
        self.signup_btn.setFixedWidth(300)
        self.signup_btn.clicked.connect(self._handle_signup)

        back_btn = QPushButton("Already have an account? Log In")
        back_btn.setObjectName("SecondaryLink")
        back_btn.clicked.connect(lambda: self.router.navigate("login"))

        self.main_layout.addWidget(self.signup_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Initialize credit inputs
        self._update_credit_inputs()

    def _update_credit_inputs(self):
        """Update the credit requirement input fields based on selected
        number of years."""
        # Clear existing inputs
        while self.credit_layout.count():
            widget = self.credit_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        self.credit_requirement_inputs = []

        num_years = self.years_spinbox.value()

        # Create input fields for each year
        for year_index in range(1, num_years + 1):
            year_label = QLabel(f"Year {year_index} Credit Requirement:")
            year_label.setObjectName("AuthLabel")

            spinbox = QSpinBox()
            spinbox.setMinimum(1)
            spinbox.setMaximum(200)
            spinbox.setValue(60)
            spinbox.setFixedWidth(300)

            self.credit_layout.addWidget(year_label, alignment=Qt.AlignmentFlag.AlignCenter)
            self.credit_layout.addWidget(spinbox, alignment=Qt.AlignmentFlag.AlignCenter)
            self.credit_requirement_inputs.append(spinbox)

    def _handle_signup(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        confirm = self.confirm_input.text().strip()
        university_id = self.university_picker.selected_id()
        major_id = self.major_picker.selected_id()
        custom_university = self.university_picker.custom_input_value()
        custom_major = self.major_picker.custom_input_value()

        if password != confirm:
            self.error_label.setText("Passwords do not match.")
            return
        if not university_id and not custom_university:
            self.error_label.setText("Please select or enter a university.")
            return
        if not major_id and not custom_major:
            self.error_label.setText("Please select or enter a major.")
            return

        self.error_label.setText("")
        self.signup_btn.setEnabled(False)
        self.signup_btn.setText("Creating account...")

        self._worker = _SignupWorker(
            username,
            password,
            self.years_spinbox.value(),
            [s.value() for s in self.credit_requirement_inputs],
            university_id,
            major_id,
            custom_university,
            custom_major,
        )
        self._worker.success.connect(self._on_signup_success)
        self._worker.failure.connect(self._on_signup_failure)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_signup_success(self, _token: str, used_custom_uni: bool, used_custom_major: bool):
        if used_custom_uni:
            self.university_picker.reload_dropdown()
        if used_custom_major:
            self.major_picker.reload_dropdown()
        self.signup_btn.setEnabled(True)
        self.signup_btn.setText("Sign Up")
        self.router.navigate("dashboard")

    def _on_signup_failure(self, message: str):
        self.error_label.setText(message)
        self.signup_btn.setEnabled(True)
        self.signup_btn.setText("Sign Up")
