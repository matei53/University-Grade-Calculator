from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QSpinBox, QPushButton, QMessageBox, QComboBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt

from ui.components.assessment_row import AssessmentRow
from services.grade_service import GradeService
from repositories.subject_repo import SubjectRepo
from repositories.assessment_repo import AssessmentRepo
from models.session import Session
from database.db import get_connection

class SubjectScreen(QWidget):
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.assessment_rows = []
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # --- Navigație ---
        nav_layout = QHBoxLayout()
        self.back_btn = QPushButton("← Înapoi la Dashboard")
        self.back_btn.setFixedWidth(160)
        self.back_btn.setStyleSheet("background-color: #E0DDD9; color: #0A0D08; font-weight: bold; border-radius: 6px; padding: 6px;")
        self.back_btn.clicked.connect(self.exit_to_dashboard)
        
        self.title = QLabel("Adaugă Materie Nouă")
        self.title.setStyleSheet("color: #2D4B1D; font-size: 18px; font-weight: bold;")
        
        nav_layout.addWidget(self.back_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.title)
        main_layout.addLayout(nav_layout)
        main_layout.addSpacing(20)

        # --- Nume Materie ---
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nume Materie (ex: Structuri de Date)")
        self.name_input.setStyleSheet("padding: 5px; font-size: 14px;")
        main_layout.addWidget(self.name_input)

        # --- Selector An, Semestru și Credite ---
        details_layout = QHBoxLayout()
        
        # 1. Selector An (NOU)
        self.year_combo = QComboBox()
        
        # 2. Selector Semestru
        self.semester_input = QSpinBox()
        self.semester_input.setRange(1, 2)
        
        # 3. Selector Credite
        self.credits_input = QSpinBox()
        self.credits_input.setRange(1, 30)
        self.credits_input.setValue(5)
        
        details_layout.addWidget(QLabel("An Universitar:"))
        details_layout.addWidget(self.year_combo)
        details_layout.addStretch()
        details_layout.addWidget(QLabel("Semestru:"))
        details_layout.addWidget(self.semester_input)
        details_layout.addStretch()
        details_layout.addWidget(QLabel("Credite:"))
        details_layout.addWidget(self.credits_input)
        
        main_layout.addLayout(details_layout)

        # --- NOU: Setări Notare Materie ---
        grading_layout = QHBoxLayout()
        
        self.subject_passing_grade = QDoubleSpinBox()
        self.subject_passing_grade.setRange(1.0, 1000.0)
        self.subject_passing_grade.setValue(5.0)
        
        self.subject_max_grade = QDoubleSpinBox()
        self.subject_max_grade.setRange(1.0, 1000.0)
        self.subject_max_grade.setValue(10.0)
        self.subject_max_grade.valueChanged.connect(self.update_average_display)
        
        self.subject_max_grade.valueChanged.connect(self.subject_passing_grade.setMaximum)
        self.subject_passing_grade.setMaximum(self.subject_max_grade.value())

        grading_layout.addWidget(QLabel("Notă Trecere Materie:"))
        grading_layout.addWidget(self.subject_passing_grade)
        grading_layout.addStretch()
        grading_layout.addWidget(QLabel("Notă Maximă Materie:"))
        grading_layout.addWidget(self.subject_max_grade)
        
        main_layout.addLayout(grading_layout)

        # --- Secțiune Evaluări ---
        self.assessments_label = QLabel("Evaluări")
        self.assessments_label.setStyleSheet("font-weight: bold; margin-top: 15px;")
        main_layout.addWidget(self.assessments_label)
        
        self.assessments_container = QWidget()
        self.assessments_layout = QVBoxLayout(self.assessments_container)
        self.assessments_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.assessments_container)
        
        self.add_assessment_btn = QPushButton("+ Adaugă Componentă Evaluare")
        self.add_assessment_btn.setStyleSheet("background-color: #C4B7A6; color: #0A0D08; padding: 5px; border-radius: 4px;")
        self.add_assessment_btn.clicked.connect(self.add_assessment_row)
        main_layout.addWidget(self.add_assessment_btn)

        # --- Status și Salvare ---
        self.weight_status_label = QLabel("Pondere Totală: 0.0%")
        self.weight_status_label.setStyleSheet("color: red;")
        main_layout.addWidget(self.weight_status_label)

        self.average_label = QLabel("Media Curentă: 0.00")
        self.average_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2D4B1D;")
        main_layout.addWidget(self.average_label)
        
        main_layout.addStretch()

        self.save_btn = QPushButton("Salvează Materia")
        self.save_btn.setStyleSheet("background-color: #2D4B1D; color: white; font-weight: bold; font-size: 14px; padding: 10px; border-radius: 6px;")
        self.save_btn.clicked.connect(self.save_subject)
        main_layout.addWidget(self.save_btn)

        self.setLayout(main_layout)
        self.add_assessment_row()

    def on_screen_shown(self):
        """Se apelează automat de router când intrăm pe acest ecran pentru a reîncărca anii."""
        self.year_combo.clear()
        try:
            user_id = Session.get_current_user_id()
            with get_connection() as conn:
                # Căutăm câți ani a generat acest utilizator la Sign Up
                years = conn.execute(
                    "SELECT order_index FROM academic_years WHERE user_id = ? ORDER BY order_index",
                    (user_id,)
                ).fetchall()
            
            # Populăm dropdown-ul dinamic
            if years:
                for y in years:
                    self.year_combo.addItem(f"Anul {y['order_index']}")
            else:
                # Fallback de siguranță
                self.year_combo.addItems(["Anul 1", "Anul 2", "Anul 3"])
        except Exception as e:
            print(f"Eroare la încărcarea anilor: {e}")
            self.year_combo.addItems(["Anul 1", "Anul 2", "Anul 3"])

    def add_assessment_row(self):
        row = AssessmentRow()
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
        self.average_label.setText(f"Media Curentă: {avg:.2f}")

    def remove_assessment_row(self, row_widget):
        if len(self.assessment_rows) > 1:
            self.assessment_rows.remove(row_widget)
            self.assessments_layout.removeWidget(row_widget)
            row_widget.deleteLater()
            self.update_weight_status()
            self.update_average_display()
        else:
            QMessageBox.warning(self, "Atenție", "Trebuie să existe cel puțin o evaluare.")

    def update_weight_status(self):
        total_weight = sum(float(row.get_data()['weight']) for row in self.assessment_rows)
        self.weight_status_label.setText(f"Pondere Totală: {total_weight:.1f}%")
        color = "#2D4B1D" if total_weight == 100.0 else "red"
        self.weight_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def clear_form(self):
        self.name_input.clear()
        self.year_combo.setCurrentIndex(0) # Reset la Anul 1
        self.semester_input.setValue(1)
        self.credits_input.setValue(5)
        for row in list(self.assessment_rows):
            self.assessment_rows.remove(row)
            self.assessments_layout.removeWidget(row)
            row.deleteLater()
        self.add_assessment_row()
        self.average_label.setText("Media Curentă: 0.00")

    def exit_to_dashboard(self):
        self.clear_form()
        self.router.navigate("dashboard")

    def save_subject(self):
        try:
            user_id = Session.get_current_user_id()
        except Exception as e:
            QMessageBox.critical(self, "Eroare Sesiune", "Nu ești logat!")
            return

        subject_name = self.name_input.text().strip()
        assessments_data = [row.get_data() for row in self.assessment_rows]

        if not subject_name:
            QMessageBox.warning(self, "Eroare", "Introdu numele materiei.")
            return

        if not GradeService.validate_weights_total(assessments_data):
            QMessageBox.warning(self, "Eroare", "Ponderile evaluărilor trebuie să însumeze 100%.")
            return

        # Extragem numărul anului din selecția ("Anul 1" -> 1)
        selected_year_text = self.year_combo.currentText()
        year_level = int(selected_year_text.split(" ")[1])

        try:
            subject_id = SubjectRepo.add_subject(
                user_id=user_id,
                subject_name=subject_name,
                credits=self.credits_input.value(),
                semester_index=self.semester_input.value(),
                year_level=year_level,
                passing_grade=self.subject_passing_grade.value(),
                max_grade=self.subject_max_grade.value()
            )
            
            for a in assessments_data:
                AssessmentRepo.add_assessment(
                    subject_id=subject_id, 
                    name=a['name'], 
                    weight=a['weight'], 
                    score=a['score'],
                    max_score=a['max_score'],
                    passing_grade=a['passing_grade']
                )
                
            QMessageBox.information(self, "Succes", "Materia a fost adăugată cu succes!")
            self.exit_to_dashboard()
        except Exception as e:
            QMessageBox.critical(self, "Eroare DB", f"A apărut o problemă la salvare: {str(e)}")