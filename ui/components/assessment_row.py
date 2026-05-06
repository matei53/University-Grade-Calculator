from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QDoubleSpinBox, QPushButton
from PyQt6.QtCore import pyqtSignal

class AssessmentRow(QWidget):
    remove_requested = pyqtSignal(QWidget)
    weight_changed = pyqtSignal()
    score_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10) # Puțin spațiu între elemente

        # 1. Nume evaluare
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nume (ex: Examen)")
        
        # 2. Pondere
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(0.0, 100.0)
        self.weight_input.setPrefix("Pondere: ")
        self.weight_input.setSuffix(" %")
        self.weight_input.valueChanged.connect(self.weight_changed.emit)

        # 3. Nota obținută
        self.score_input = QDoubleSpinBox()
        self.score_input.setRange(0.0, 1000.0)
        self.score_input.setDecimals(2)
        self.score_input.setPrefix("Notă: ")
        self.score_input.valueChanged.connect(self.score_changed.emit)

        # 4. Nota maximă a probei
        self.max_score_input = QDoubleSpinBox()
        self.max_score_input.setRange(1.0, 1000.0)
        self.max_score_input.setValue(10.0)
        self.max_score_input.setPrefix("Din max: ")
        self.max_score_input.valueChanged.connect(self.score_changed.emit) 

        # 5. Condiție de trecere a probei
        self.passing_grade_input = QDoubleSpinBox()
        self.passing_grade_input.setRange(0.0, 1000.0)
        self.passing_grade_input.setValue(5.0)
        self.passing_grade_input.setPrefix("Minim probă: ")

        # --- NOU: Constrângeri Dinamice ---
        self.max_score_input.valueChanged.connect(self._update_limits)
        self._update_limits(self.max_score_input.value()) # Inițializare limite la creare

        # Buton ștergere
        self.remove_btn = QPushButton("X")
        self.remove_btn.setStyleSheet("background-color: #ffcccc; font-weight: bold; border-radius: 4px; padding: 4px 8px;")
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))

        layout.addWidget(self.name_input)
        layout.addWidget(self.weight_input)
        layout.addWidget(self.score_input)
        layout.addWidget(self.max_score_input)
        layout.addWidget(self.passing_grade_input)
        layout.addWidget(self.remove_btn)
        self.setLayout(layout)

    def _update_limits(self, max_val):
        """Asigură că nota obținută și nota de trecere nu pot depăși nota maximă."""
        self.score_input.setMaximum(max_val)
        self.passing_grade_input.setMaximum(max_val)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "weight": self.weight_input.value(),
            "score": self.score_input.value(),
            "max_score": self.max_score_input.value(),
            "passing_grade": self.passing_grade_input.value()
        }