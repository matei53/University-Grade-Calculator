# ui/screens/signup_screen.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QSpinBox, QScrollArea
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

        scroll_layout.addWidget(self.username_input, alignment=Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(self.password_input, alignment=Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(self.confirm_input, alignment=Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(self.university_picker, alignment=Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(self.major_picker, alignment=Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(years_label, alignment=Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(self.years_spinbox, alignment=Qt.AlignmentFlag.AlignCenter)

        # Container for credit requirement inputs
        self.credit_container = QWidget()
        self.credit_layout = QVBoxLayout(self.credit_container)
        self.credit_layout.setContentsMargins(0, 0, 0, 0)
        self.credit_layout.setSpacing(10)
        self.credit_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(self.credit_container, alignment=Qt.AlignmentFlag.AlignCenter)

        scroll_area.setWidget(scroll_content)
        self.main_layout.addWidget(scroll_area)

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

        # Initialize credit inputs
        self._update_credit_inputs()

    def _update_credit_inputs(self):
        """Update the credit requirement input fields based on selected number of years."""
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
        num_years = self.years_spinbox.value()
        credit_requirements = [spinbox.value() for spinbox in self.credit_requirement_inputs]

        if password != confirm:
            self.error_label.setText("Passwords do not match.")
            return

        try:
            user = self.auth_service.sign_up(username, password, num_years, credit_requirements)
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