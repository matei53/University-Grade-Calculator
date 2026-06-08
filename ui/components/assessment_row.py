from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)


class AssessmentRow(QWidget):
    remove_requested = pyqtSignal(QWidget)
    weight_changed = pyqtSignal()
    score_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)  # Small spacing between elements

        # 1. Assessment name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Name (e.g.: Exam)")

        # 2. Weight
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(0.0, 100.0)
        self.weight_input.setPrefix("Weight: ")
        self.weight_input.setSuffix(" %")
        self.weight_input.valueChanged.connect(self.weight_changed.emit)

        # 3. Obtained grade
        self.score_input = QDoubleSpinBox()
        self.score_input.setRange(0.0, 1000.0)
        self.score_input.setDecimals(2)
        self.score_input.setPrefix("Grade: ")
        self.score_input.valueChanged.connect(self.score_changed.emit)

        # 4. Maximum grade for the assessment
        self.max_score_input = QDoubleSpinBox()
        self.max_score_input.setRange(1.0, 1000.0)
        self.max_score_input.setValue(10.0)
        self.max_score_input.setPrefix("Out of: ")
        self.max_score_input.valueChanged.connect(self.score_changed.emit)

        # 5. Passing condition for the assessment
        self.passing_grade_input = QDoubleSpinBox()
        self.passing_grade_input.setRange(0.0, 1000.0)
        self.passing_grade_input.setValue(5.0)
        self.passing_grade_input.setPrefix("Min. score: ")

        # --- NEW: Dynamic Constraints ---
        self.max_score_input.valueChanged.connect(self._update_limits)
        self._update_limits(self.max_score_input.value())  # Initialize limits on creation

        # Remove button
        self.remove_btn = QPushButton("X")
        self.remove_btn.setStyleSheet("background-color: #ffcccc; font-weight: bold; \
            border-radius: 4px; padding: 4px 8px;")
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))

        # Stretch: name gets more space; controls keep compact widths
        layout.addWidget(self.name_input, 3)
        layout.addWidget(self.weight_input, 1)
        layout.addWidget(self.score_input, 1)
        layout.addWidget(self.max_score_input, 1)
        layout.addWidget(self.passing_grade_input, 1)
        layout.addWidget(self.remove_btn, 0)
        self.setLayout(layout)

    def _update_limits(self, max_val):
        """Ensures the obtained grade/passing grade cannot exceed the maximum grade."""
        self.score_input.setMaximum(max_val)
        self.passing_grade_input.setMaximum(max_val)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "weight": self.weight_input.value(),
            "score": self.score_input.value(),
            "max_score": self.max_score_input.value(),
            "passing_grade": self.passing_grade_input.value(),
        }
