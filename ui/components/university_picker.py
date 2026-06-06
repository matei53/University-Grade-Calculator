import json
import os

from PyQt6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "universities.json"
)


class UniversityPicker(QWidget):
    def __init__(self):
        super().__init__()
        self._universities = []
        self._selected_id = None
        self._custom_input = ""
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Dropdown
        self.combo_box = QComboBox()
        self._load_dropdown()
        self.combo_box.currentIndexChanged.connect(self._on_combo_changed)
        layout.addWidget(self.combo_box)

        # Custom input
        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("Or type your university here...")
        self.custom_input.textChanged.connect(self._on_custom_changed)
        layout.addWidget(self.custom_input)

    def _load_dropdown(self):
        self.combo_box.addItem("Select your university...", userData=None)
        try:
            with open(DATA_PATH, "r") as f:
                self._universities = json.load(
                    f
                )  # expects [{"id": 1, "name": "..."}]
            for uni in self._universities:
                self.combo_box.addItem(uni["name"], userData=uni["id"])
        except FileNotFoundError:
            pass  # Picker still works, just empty

    def _on_combo_changed(self):
        """When dropdown selection changes, clear custom input."""
        if self.combo_box.currentIndex() > 0:  # Not the placeholder
            self.custom_input.blockSignals(True)
            self.custom_input.clear()
            self.custom_input.blockSignals(False)
            self._selected_id = self.combo_box.currentData()
            self._custom_input = ""
        else:
            self._selected_id = None

    def _on_custom_changed(self):
        """When custom input changes, deselect dropdown."""
        self._custom_input = self.custom_input.text().strip()
        if self._custom_input:
            self.combo_box.blockSignals(True)
            self.combo_box.setCurrentIndex(0)  # Reset to placeholder
            self.combo_box.blockSignals(False)
            self._selected_id = None
        else:
            self._selected_id = self.combo_box.currentData()

    def selected_id(self):
        """Returns the ID of selected university from dropdown."""
        return self._selected_id

    def custom_input_value(self):
        """Returns the custom input text if provided, otherwise None."""
        return self._custom_input if self._custom_input else None

    def reload_dropdown(self):
        """Reload the dropdown with latest data from JSON."""
        self.combo_box.blockSignals(True)
        self.combo_box.clear()
        self._load_dropdown()
        self.combo_box.setCurrentIndex(0)  # Reset to placeholder
        self.combo_box.blockSignals(False)
