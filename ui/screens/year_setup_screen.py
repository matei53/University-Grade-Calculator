from PyQt6.QtWidgets import (
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from client.api_client import APIClient


class YearSetupScreen(QWidget):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.api_client = APIClient()
        layout = QVBoxLayout()

        self.title = QLabel("Set Up Academic Year")
        self.title.setStyleSheet(
            "color: #2D4B1D; font-size: 18px; font-weight: bold;"
        )

        self.year_name_input = QLineEdit()
        self.year_name_input.setPlaceholderText("e.g. Year 1")

        self.target_credits_label = QLabel("Target Credits:")
        self.target_credits_input = QSpinBox()
        self.target_credits_input.setRange(1, 100)
        self.target_credits_input.setValue(60)

        self.save_btn = QPushButton("Save Year")
        self.save_btn.clicked.connect(self.save_year)

        # Button to proceed to subject setup
        self.next_btn = QPushButton("Go to Subjects")
        self.next_btn.clicked.connect(
            lambda: self.router.navigate("subject_setup")
        )

        layout.addWidget(self.title)
        layout.addWidget(self.year_name_input)
        layout.addWidget(self.target_credits_label)
        layout.addWidget(self.target_credits_input)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.next_btn)
        layout.addStretch()

        self.setLayout(layout)

    def save_year(self):
        year_name = self.year_name_input.text().strip()

        if not year_name:
            QMessageBox.warning(self, "Error", "Please enter the year name.")
            return

        try:
            # Note: Academic years are created during signup
            # This is kept for reference but the actual year creation
            # happens on the server
            QMessageBox.information(
                self,
                "Info",
                "Academic years are managed automatically.\n\
                    Please add subjects instead.",
            )
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))
