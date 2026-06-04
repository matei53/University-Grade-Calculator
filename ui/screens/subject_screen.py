from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from client.api_client import APIClient
from services.grade_service import GradeService
from ui.components.assessment_row import AssessmentRow


class SubjectScreen(QWidget):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.assessment_rows = []
        self.api_client = APIClient()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 30, 40, 40)
        main_layout.setSpacing(15)

        # --- Navigation & Left-Aligned Title ---
        header_area = QVBoxLayout()

        self.back_btn = QPushButton("← Back to Dashboard")
        self.back_btn.setObjectName("FilterButton")
        self.back_btn.setFixedWidth(180)
        self.back_btn.clicked.connect(self.exit_to_dashboard)

        self.title = QLabel("Add New Subject")
        self.title.setObjectName("HeaderTitle")
        self.title.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #2D4B1D; \
            margin-top: 10px;"
        )

        header_area.addWidget(self.back_btn)
        header_area.addWidget(self.title)
        main_layout.addLayout(header_area)

        # --- Subject Details Card ---
        self.form_card = QFrame()
        self.form_card.setObjectName("StatCard")
        card_layout = QVBoxLayout(self.form_card)
        card_layout.setContentsMargins(25, 25, 25, 25)
        card_layout.setSpacing(15)

        detail_title = QLabel("SUBJECT DETAILS")
        detail_title.setStyleSheet(
            "color: #2D4B1D; font-weight: bold; font-size: 11px; \
            letter-spacing: 1px;"
        )
        card_layout.addWidget(detail_title)

        self.name_input = QLineEdit()
        self.name_input.setObjectName("AuthInput")
        self.name_input.setPlaceholderText(
            "Subject Name (e.g. Data Structures)"
        )
        card_layout.addWidget(self.name_input)

        # --- Exact Alignment Grid ---
        # Column 0-1: Left group (Year/Semester)
        # Column 2: Stretch spacer
        # Column 3-4: Center group (Credits) - Level with top row
        # Column 5: Stretch spacer
        # Column 6-7: Right group (Grades)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)

        # Left Column (Year & Semester)
        self.year_combo = QComboBox()
        self.year_combo.setObjectName("AuthInput")
        self.semester_input = QSpinBox()
        self.semester_input.setObjectName("AuthInput")
        self.semester_input.setRange(1, 2)

        grid_layout.addWidget(QLabel("Academic Year:"), 0, 0)
        grid_layout.addWidget(self.year_combo, 0, 1)
        grid_layout.addWidget(QLabel("Semester:"), 1, 0)
        grid_layout.addWidget(self.semester_input, 1, 1)

        # Center Group (Credits) - Centered Left exactly
        self.credits_input = QSpinBox()
        self.credits_input.setObjectName("AuthInput")
        self.credits_input.setRange(1, 30)
        self.credits_input.setValue(5)

        grid_layout.setColumnStretch(2, 1)  # Spacer before credits
        grid_layout.addWidget(
            QLabel("Credits:"),
            0,
            3,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        grid_layout.addWidget(
            self.credits_input, 0, 4, Qt.AlignmentFlag.AlignVCenter
        )
        grid_layout.setColumnStretch(5, 1)  # Spacer after credits

        # Right Column (Grades)
        self.subject_max_grade = QDoubleSpinBox()
        self.subject_max_grade.setObjectName("AuthInput")
        self.subject_max_grade.setRange(1.0, 100.0)
        self.subject_max_grade.setValue(10.0)
        self.subject_max_grade.valueChanged.connect(
            self.update_average_display
        )

        self.subject_passing_grade = QDoubleSpinBox()
        self.subject_passing_grade.setObjectName("AuthInput")
        self.subject_passing_grade.setRange(1.0, 100.0)
        self.subject_passing_grade.setValue(5.0)

        grid_layout.addWidget(QLabel("Max Grade:"), 0, 6)
        grid_layout.addWidget(self.subject_max_grade, 0, 7)
        grid_layout.addWidget(QLabel("Passing Grade:"), 1, 6)
        grid_layout.addWidget(self.subject_passing_grade, 1, 7)

        card_layout.addLayout(grid_layout)
        main_layout.addWidget(self.form_card)

        # --- Assessments Section ---
        assessment_header_layout = QVBoxLayout()
        assessment_header_layout.setSpacing(2)

        self.assessments_label = QLabel("ASSESSMENTS")
        self.assessments_label.setStyleSheet(
            "color: #2D4B1D; font-weight: bold; font-size: 11px; \
            letter-spacing: 1px; margin-top: 10px;"
        )

        self.weight_rule_label = QLabel("Total weight must equal 100%")
        self.weight_rule_label.setStyleSheet(
            "color: #A8C686; font-size: 10px; font-weight: bold;"
        )

        assessment_header_layout.addWidget(self.assessments_label)
        assessment_header_layout.addWidget(self.weight_rule_label)
        main_layout.addLayout(assessment_header_layout)

        self.assessments_container = QWidget()
        self.assessments_layout = QVBoxLayout(self.assessments_container)
        self.assessments_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.assessments_container)

        self.add_assessment_btn = QPushButton("+ Add Assessment Component")
        self.add_assessment_btn.setObjectName("SecondaryButton")
        self.add_assessment_btn.clicked.connect(self.add_assessment_row)
        main_layout.addWidget(self.add_assessment_btn)

        # --- Status Row ---
        status_layout = QHBoxLayout()
        self.weight_status_label = QLabel("Total Weight: 0.0%")
        self.weight_status_label.setStyleSheet(
            "color: #D32F2F; font-weight: bold; font-size: 13px;"
        )

        self.average_label = QLabel("Current Average: 0.00")
        self.average_label.setStyleSheet(
            "font-weight: bold; font-size: 13px; color: #2D4B1D;"
        )

        status_layout.addWidget(self.weight_status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.average_label)
        main_layout.addLayout(status_layout)

        main_layout.addStretch()

        self.save_btn = QPushButton("Save Subject")
        self.save_btn.setObjectName("PrimaryButton")
        self.save_btn.setFixedHeight(45)
        self.save_btn.clicked.connect(self.save_subject)
        main_layout.addWidget(self.save_btn)

        self.setLayout(main_layout)
        self.add_assessment_row()

    def on_screen_shown(self):
        # Create fresh API client to ensure we have the current user's token
        self.api_client = APIClient()

        self.year_combo.clear()
        try:
            years = self.api_client.get_academic_years()

            if years:
                for y in years:
                    self.year_combo.addItem(f"Year {y['order_index']}")
            else:
                self.year_combo.addItems(["Year 1", "Year 2", "Year 3"])
        except Exception as e:
            print(f"Error loading academic years: {e}")
            self.year_combo.addItems(["Year 1", "Year 2", "Year 3"])

    def add_assessment_row(self):
        row = AssessmentRow()
        row.name_input.setPlaceholderText("Name (e.g. Exam)")
        row.weight_input.setPrefix("Weight: ")
        row.weight_input.setSuffix(" %")
        row.score_input.setPrefix("Grade: ")
        row.max_score_input.setPrefix("Max: ")
        row.passing_grade_input.setPrefix("Pass: ")

        self.assessment_rows.append(row)
        self.assessments_layout.addWidget(row)
        row.remove_requested.connect(self.remove_assessment_row)
        row.weight_changed.connect(self.update_weight_status)
        row.score_changed.connect(self.update_average_display)
        self.update_weight_status()

    def update_average_display(self):
        data_list = [row.get_data() for row in self.assessment_rows]
        subject_max = self.subject_max_grade.value()
        avg = GradeService.calculate_subject_average(data_list, subject_max)
        self.average_label.setText(f"Current Average: {avg:.2f}")

    def remove_assessment_row(self, row_widget):
        if len(self.assessment_rows) > 1:
            self.assessment_rows.remove(row_widget)
            self.assessments_layout.removeWidget(row_widget)
            row_widget.deleteLater()
            self.update_weight_status()
            self.update_average_display()
        else:
            QMessageBox.warning(
                self,
                "Warning",
                "At least one assessment component is required.",
            )

    def update_weight_status(self):
        total_weight = sum(
            float(row.get_data()["weight"]) for row in self.assessment_rows
        )
        self.weight_status_label.setText(f"Total Weight: {total_weight:.1f}%")
        color = "#2D4B1D" if total_weight == 100.0 else "#D32F2F"
        self.weight_status_label.setStyleSheet(
            f"color: {color}; font-weight: bold; font-size: 13px;"
        )

    def clear_form(self):
        self.name_input.clear()
        self.year_combo.setCurrentIndex(0)
        self.semester_input.setValue(1)
        self.credits_input.setValue(5)
        for row in list(self.assessment_rows):
            self.assessment_rows.remove(row)
            self.assessments_layout.removeWidget(row)
            row.deleteLater()
        self.add_assessment_row()
        self.average_label.setText("Current Average: 0.00")

    def exit_to_dashboard(self):
        self.clear_form()
        self.router.navigate("dashboard")

    def save_subject(self):
        subject_name = self.name_input.text().strip()
        assessments_data = [row.get_data() for row in self.assessment_rows]

        if not subject_name:
            QMessageBox.warning(self, "Error", "Please enter a subject name.")
            return

        if not GradeService.validate_weights_total(assessments_data):
            QMessageBox.warning(
                self,
                "Error",
                "Total assessment weights must equal 100%.",
            )
            return

        try:
            selected_year_text = self.year_combo.currentText()
            year_level = int(selected_year_text.split(" ")[1])

            # Add subject via API
            subject = self.api_client.add_subject(
                name=subject_name,
                credits=self.credits_input.value(),
                semester_index=self.semester_input.value(),
                year_level=year_level,
                passing_grade=self.subject_passing_grade.value(),
                max_grade=self.subject_max_grade.value(),
            )

            # Add assessments via API
            for a in assessments_data:
                self.api_client.add_assessment(
                    subject_id=subject["id"],
                    name=a["name"],
                    weight=a["weight"],
                    score=a["score"],
                    max_score=a["max_score"],
                    passing_grade=a["passing_grade"],
                )

            QMessageBox.information(
                self, "Success", "Subject added successfully!"
            )
            self.exit_to_dashboard()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")
