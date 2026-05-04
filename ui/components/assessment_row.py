from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QDoubleSpinBox, QPushButton
from PyQt6.QtCore import pyqtSignal

class AssessmentRow(QWidget):
    remove_requested = pyqtSignal(QWidget)
    weight_changed = pyqtSignal()
    score_changed = pyqtSignal() # Semnal nou pentru notă

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

        # Câmp nou pentru notă (0-10)
        self.score_input = QDoubleSpinBox()
        self.score_input.setRange(0.0, 10.0)
        self.score_input.setDecimals(2)
        # AM ȘTERS LINIA CU setPlaceholderText și am pus un ToolTip în loc
        self.score_input.setToolTip("Introdu nota (0 - 10)")
        self.score_input.valueChanged.connect(self.score_changed.emit)

        self.remove_btn = QPushButton("X")
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))

        layout.addWidget(self.name_input)
        layout.addWidget(self.weight_input)
        layout.addWidget(self.score_input)
        layout.addWidget(self.remove_btn)
        self.setLayout(layout)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "weight": self.weight_input.value(),
            "score": self.score_input.value()
        }