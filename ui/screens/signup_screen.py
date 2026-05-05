# ui/screens/signup_screen.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt
from services.auth_service import AuthService
from models.session import Session
from ui.components.university_picker import UniversityPicker
from ui.components.major_picker import MajorPicker
from ui.styles import AUTH_STYLE

class SignupScreen(QWidget):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.auth_service = AuthService()
        self.setStyleSheet(AUTH_STYLE)
        self._build_ui()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(15)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel("UniGrade")
        title.setObjectName("AuthTitle")
        self.main_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Create Account")
        subtitle.setObjectName("AuthSubtitle")
        self.main_layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addSpacing(20)

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

        self.main_layout.addWidget(self.username_input, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.password_input, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.confirm_input, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.university_picker, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.major_picker, alignment=Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addSpacing(10)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorLabel")
        self.main_layout.addWidget(self.error_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addSpacing(10)

        # Buttons
        signup_btn = QPushButton("Sign Up")
        signup_btn.setObjectName("PrimaryButton")
        signup_btn.setFixedWidth(300)
        signup_btn.clicked.connect(self._handle_signup)

        back_btn = QPushButton("Already have an account? Log In")
        back_btn.setObjectName("SecondaryLink")
        back_btn.clicked.connect(lambda: self.router.navigate("login"))

        self.main_layout.addWidget(signup_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addStretch()

    def _handle_signup(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        confirm = self.confirm_input.text().strip()
        university_id = self.university_picker.selected_id()
        major_id = self.major_picker.selected_id()

        if password != confirm:
            self.error_label.setText("Passwords do not match.")
            return

        try:
            user = self.auth_service.sign_up(username, password)
            from repositories.user_repo import UserRepo
            repo = UserRepo()
            if university_id:
                repo.update_university(user["id"], university_id)
                user["university_id"] = university_id
            if major_id:
                repo.update_major(user["id"], major_id)
                user["major_id"] = major_id
            Session.login(user)
            self.error_label.setText("")
            self.router.navigate("dashboard")
        except ValueError as e:
            self.error_label.setText(str(e))