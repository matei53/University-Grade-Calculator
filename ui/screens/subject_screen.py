from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QSpinBox, QPushButton, QMessageBox, 
                             QScrollArea, QFrame)
from PyQt6.QtCore import Qt

# Import your newly created components and services
from ui.components.assessment_row import AssessmentRow
from services.grade_service import GradeService
from repositories.subject_repo import SubjectRepo
from repositories.assessment_repo import AssessmentRepo

# ... (importurile raman la fel ca in mesajul anterior)

class SubjectScreen(QWidget):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.current_year_id = 1
        self.assessment_rows = []
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # --- Subject Details Section ---
        self.title = QLabel("Add New Subject")
        self.title.setStyleSheet("color: #2D4B1D; font-size: 18px; font-weight: bold;")
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Subject Name (e.g., Data Structures)")

        credits_layout = QHBoxLayout()
        self.credits_label = QLabel("Credits:")
        self.credits_input = QSpinBox()
        self.credits_input.setRange(1, 30)
        self.credits_input.setValue(5)
        
        self.semester_label = QLabel("Semester:")
        self.semester_input = QSpinBox()
        self.semester_input.setRange(1, 2)
        
        credits_layout.addWidget(self.credits_label)
        credits_layout.addWidget(self.credits_input)
        credits_layout.addStretch()
        credits_layout.addWidget(self.semester_label)
        credits_layout.addWidget(self.semester_input)

        # --- Dynamic Assessments Section ---
        self.assessments_label = QLabel("Assessments (Must total 100%)")
        self.assessments_label.setStyleSheet("font-weight: bold; margin-top: 15px;")
        
        # Container for the dynamic rows
        self.assessments_container = QWidget()
        self.assessments_layout = QVBoxLayout(self.assessments_container)
        self.assessments_layout.setContentsMargins(0, 0, 0, 0)
        
        self.add_assessment_btn = QPushButton("+ Add Assessment Component")
        self.add_assessment_btn.setStyleSheet("background-color: #C4B7A6; color: #0A0D08;") # STONE_GREY
        self.add_assessment_btn.clicked.connect(self.add_assessment_row)

        # Status label to show real-time percentage
        self.weight_status_label = QLabel("Total Weight: 0.0%")
        self.weight_status_label.setStyleSheet("color: red;")

        self.average_label = QLabel("Media Curentă: 0.00")
        self.average_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2D4B1D;")
        main_layout.addWidget(self.average_label)

        # --- Save Button ---
        self.save_btn = QPushButton("Save Subject")
        self.save_btn.clicked.connect(self.save_subject)

        # Assemble the layout
        main_layout.addWidget(self.title)
        main_layout.addWidget(self.name_input)
        main_layout.addLayout(credits_layout)
        main_layout.addWidget(self.assessments_label)
        main_layout.addWidget(self.assessments_container)
        main_layout.addWidget(self.add_assessment_btn)
        main_layout.addWidget(self.weight_status_label)
        main_layout.addStretch()
        main_layout.addWidget(self.save_btn)

        self.setLayout(main_layout)

        # Add one row by default
        self.add_assessment_row()

    def add_assessment_row(self):
        """Spawns a new AssessmentRow widget and wires up its signals."""
        row = AssessmentRow()
        self.assessment_rows.append(row)
        self.assessments_layout.addWidget(row)
        
        # Connect signals
        row.remove_requested.connect(self.remove_assessment_row)
        row.weight_changed.connect(self.update_weight_status)
        
        self.update_weight_status()
        row.score_changed.connect(self.update_average_display)

    def update_average_display(self):
        """Calculează media ponderată în timp real."""
        data_list = [row.get_data() for row in self.assessment_rows]

        # Folosim GradeService pentru calcul
        from services.grade_service import GradeService

        # Simulăm formatul de date pentru service
        assessments_for_math = []
        grades_dict = {}
        for i, data in enumerate(data_list):
            assessments_for_math.append({'id': i, 'weight': data['weight']})
            grades_dict[i] = data['score']

        avg = GradeService.calculate_subject_average(assessments_for_math, grades_dict)
        self.average_label.setText(f"Media Curentă: {avg:.2f}")

    def remove_assessment_row(self, row_widget):
        """Removes an AssessmentRow widget."""
        if len(self.assessment_rows) > 1: # Keep at least one row
            self.assessment_rows.remove(row_widget)
            self.assessments_layout.removeWidget(row_widget)
            row_widget.deleteLater()
            self.update_weight_status()
        else:
            QMessageBox.warning(self, "Warning", "You must have at least one assessment component.")

    def update_weight_status(self):
        """Recalculates the total weight and updates the UI label."""
        data_list = [row.get_data() for row in self.assessment_rows]
        total_weight = sum(float(item['weight']) for item in data_list)
        
        self.weight_status_label.setText(f"Total Weight: {total_weight:.1f}%")
        
        if total_weight == 100.0:
            self.weight_status_label.setStyleSheet("color: #2D4B1D; font-weight: bold;") # Green if valid
        else:
            self.weight_status_label.setStyleSheet("color: red; font-weight: bold;")

    def save_subject(self):
        """Validates all data and saves to the database using Repositories."""
        if not self.current_year_id:
             # For testing purposes later, we'll hardcode an ID if none is passed
             self.current_year_id = 1 

        subject_name = self.name_input.text().strip()
        if not subject_name:
            QMessageBox.warning(self, "Error", "Subject name cannot be empty.")
            return

        # 1. Grab all data from the dynamic rows
        assessments_data = [row.get_data() for row in self.assessment_rows]

        # 2. Validate using your GradeService
        if not GradeService.validate_weights_total(assessments_data):
            QMessageBox.warning(self, "Error", "Assessment weights must total exactly 100%.")
            return

        # 3. Save to Database
        try:
            # Save the subject first
            subject_id = SubjectRepo.add_subject(
                year_id=self.current_year_id,
                name=subject_name,
                credits=self.credits_input.value(),
                semester_index=self.semester_input.value() # <--- NEW NAME
            )

            # Loop through and save each assessment attached to that subject
            for assessment in assessments_data:
                AssessmentRepo.add_assessment(
                    subject_id=subject_id,
                    name=assessment['name'],
                    weight=assessment['weight'],
                    score=assessment['score'] # ADAUGĂ ACEASTĂ LINIE
                )

            QMessageBox.information(self, "Success", "Subject and assessments saved successfully!")
            self.name_input.clear()
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))