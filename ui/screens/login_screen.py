from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.session import Session
from services.auth_service import AuthService
from ui.styles import AUTH_STYLE


class LoginScreen(QWidget):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.auth_service = AuthService()
        self.setStyleSheet(AUTH_STYLE)
        self._build_ui()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(20)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel("UniGrade")
        title.setObjectName("AuthTitle")
        self.main_layout.addWidget(
            title, alignment=Qt.AlignmentFlag.AlignCenter
        )

        subtitle = QLabel("Log In")
        subtitle.setObjectName("AuthSubtitle")
        self.main_layout.addWidget(
            subtitle, alignment=Qt.AlignmentFlag.AlignCenter
        )

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

        self.main_layout.addWidget(
            self.username_input,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        self.main_layout.addWidget(
            self.password_input,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        # Error label
        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorLabel")
        self.main_layout.addWidget(
            self.error_label, alignment=Qt.AlignmentFlag.AlignCenter
        )

        self.main_layout.addSpacing(10)

        # Buttons
        login_btn = QPushButton("Log In")
        login_btn.setObjectName("PrimaryButton")
        login_btn.setFixedWidth(300)
        login_btn.clicked.connect(self._handle_login)

        signup_btn = QPushButton("Don't have an account? Sign Up")
        signup_btn.setObjectName("SecondaryLink")
        signup_btn.clicked.connect(lambda: self.router.navigate("signup"))

        self.main_layout.addWidget(
            login_btn, alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.main_layout.addWidget(
            signup_btn, alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.main_layout.addStretch()

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
