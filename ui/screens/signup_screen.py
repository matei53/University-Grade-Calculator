from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt
from services.auth_service import AuthService
from models.session import Session
from ui.components.university_picker import UniversityPicker

class SignupScreen(QWidget):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.auth_service = AuthService()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        self.setLayout(layout)

        layout.addWidget(QLabel("<h2>Create Account</h2>"))

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedWidth(300)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedWidth(300)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Confirm Password")
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setFixedWidth(300)

        self.university_picker = UniversityPicker()
        self.university_picker.setFixedWidth(300)

        signup_btn = QPushButton("Sign Up")
        signup_btn.setFixedWidth(300)
        signup_btn.clicked.connect(self._handle_signup)

        back_btn = QPushButton("Already have an account? Log In")
        back_btn.setFlat(True)
        back_btn.clicked.connect(lambda: self.router.navigate("login"))

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")

        for widget in [
            self.username_input, self.password_input,
            self.confirm_input, self.university_picker,
            self.error_label, signup_btn, back_btn
        ]:
            layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignCenter)

    def _handle_signup(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        confirm = self.confirm_input.text().strip()
        university_id = self.university_picker.selected_id()

        if password != confirm:
            self.error_label.setText("Passwords do not match.")
            return

        try:
            user = self.auth_service.sign_up(username, password)
            if university_id:
                from repositories.user_repo import UserRepo
                UserRepo().update_university(user["id"], university_id)
                user["university_id"] = university_id
            Session.login(user)
            self.error_label.setText("")
            self.router.navigate("dashboard")
        except ValueError as e:
            self.error_label.setText(str(e))