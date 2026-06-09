from PyQt6.QtCore import Qt, QThread, pyqtSignal
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


class _LoginWorker(QThread):
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(self, username: str, password: str):
        super().__init__()
        self._username = username
        self._password = password

    def run(self):
        try:
            user = AuthService().login(self._username, self._password)
            self.success.emit(user)
        except ValueError as e:
            self.failure.emit(str(e))


class LoginScreen(QWidget):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.auth_service = AuthService()
        self._worker = None
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
        self.main_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Log In")
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
        self.main_layout.addWidget(self.error_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addSpacing(10)

        # Buttons
        self.login_btn = QPushButton("Log In")
        self.login_btn.setObjectName("PrimaryButton")
        self.login_btn.setFixedWidth(300)
        self.login_btn.clicked.connect(self._handle_login)

        signup_btn = QPushButton("Don't have an account? Sign Up")
        signup_btn.setObjectName("SecondaryLink")
        signup_btn.clicked.connect(lambda: self.router.navigate("signup"))

        self.main_layout.addWidget(self.login_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(signup_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addStretch()

    def _handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        self.error_label.setText("")
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Logging in...")

        self._worker = _LoginWorker(username, password)
        self._worker.success.connect(self._on_login_success)
        self._worker.failure.connect(self._on_login_failure)
        self._worker.start()

    def _on_login_success(self, user: dict):
        Session.login(user)
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Log In")
        self.router.navigate("dashboard")

    def _on_login_failure(self, message: str):
        self.error_label.setText(message)
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Log In")
