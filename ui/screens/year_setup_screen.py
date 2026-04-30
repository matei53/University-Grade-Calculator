from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt

class YearSetupScreen(QWidget):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        self.setLayout(layout)

        layout.addWidget(QLabel("<h2>Years & Subjects</h2>"),
                         alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(QLabel("Person B's screen will go here."),
                         alignment=Qt.AlignmentFlag.AlignCenter)

        back_btn = QPushButton("Back to Dashboard")
        back_btn.setFixedWidth(300)
        back_btn.clicked.connect(lambda: self.router.navigate("dashboard"))
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)