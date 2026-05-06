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

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nume (ex: Examen)")
        
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(0.0, 100.0)
        self.weight_input.setSuffix(" %")
        self.weight_input.valueChanged.connect(self.weight_changed.emit)

        self.score_input = QDoubleSpinBox()
        self.score_input.setRange(0.0, 1000.0) # Mărit pentru flexibilitate
        self.score_input.setDecimals(2)
        self.score_input.setToolTip("Introdu nota obținută")
        self.score_input.valueChanged.connect(self.score_changed.emit)

        # NOU: Nota maximă
        self.max_score_input = QDoubleSpinBox()
        self.max_score_input.setRange(1.0, 1000.0)
        self.max_score_input.setValue(10.0)
        self.max_score_input.setToolTip("Nota maximă (ex: 10)")

        # NOU: Nota de trecere
        self.passing_grade_input = QDoubleSpinBox()
        self.passing_grade_input.setRange(0.0, 1000.0)
        self.passing_grade_input.setValue(5.0)
        self.passing_grade_input.setToolTip("Nota de trecere (ex: 5)")

        self.remove_btn = QPushButton("X")
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))

        layout.addWidget(self.name_input)
        layout.addWidget(self.weight_input)
        layout.addWidget(self.score_input)
        layout.addWidget(self.max_score_input)
        layout.addWidget(self.passing_grade_input)
        layout.addWidget(self.remove_btn)
        self.setLayout(layout)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "weight": self.weight_input.value(),
            "score": self.score_input.value(),
            "max_score": self.max_score_input.value(),
            "passing_grade": self.passing_grade_input.value()
        }