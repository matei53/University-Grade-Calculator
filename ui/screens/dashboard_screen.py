from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt
from models.session import Session

class DashboardScreen(QWidget):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        self.setLayout(layout)

        self.welcome_label = QLabel("")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(QLabel("<h2>Dashboard</h2>"),
                         alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.welcome_label)

        layout.addWidget(
            QLabel("Credits, averages, and subject rankings will appear here."),
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        # Navigation to Person B's screen
        years_btn = QPushButton("Manage Years & Subjects")
        years_btn.setFixedWidth(300)
        years_btn.clicked.connect(lambda: self.router.navigate("year_setup"))
        layout.addWidget(years_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        logout_btn = QPushButton("Log Out")
        logout_btn.setFixedWidth(300)
        logout_btn.clicked.connect(self._handle_logout)
        layout.addWidget(logout_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def showEvent(self, event):
        super().showEvent(event)
        if Session.is_logged_in():
            user = Session.get_user()
            self.welcome_label.setText(f"Welcome, {user['username']}!")

    def _handle_logout(self):
        Session.logout()
        self.router.navigate("login")