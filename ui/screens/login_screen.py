from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from services.auth_service import AuthService
from models.session import Session

class LoginScreen(QWidget):
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

        layout.addWidget(QLabel("<h2>Grade Tracker</h2>"))

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedWidth(300)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedWidth(300)

        login_btn = QPushButton("Log In")
        login_btn.setFixedWidth(300)
        login_btn.clicked.connect(self._handle_login)

        signup_btn = QPushButton("Don't have an account? Sign Up")
        signup_btn.setFlat(True)
        signup_btn.clicked.connect(lambda: self.router.navigate("signup"))

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")

        layout.addWidget(self.username_input, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.password_input, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(login_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(signup_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def _handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        try:
            user = self.auth_service.login(username, password)
            Session.login(user)
            self.error_label.setText("")
            self.router.navigate("dashboard")
        except ValueError as e:
            self.error_label.setText(str(e))