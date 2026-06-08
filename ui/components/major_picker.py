from PyQt6.QtWidgets import QComboBox, QLineEdit, QVBoxLayout, QWidget

from services.data_service import DataService


class MajorPicker(QWidget):
    def __init__(self):
        super().__init__()
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
        self.custom_input.setPlaceholderText("Or type your major here...")
        self.custom_input.textChanged.connect(self._on_custom_changed)
        layout.addWidget(self.custom_input)

    def _load_dropdown(self):
        self.combo_box.addItem("Select your major...", userData=None)
        for major in DataService.get_majors():
            self.combo_box.addItem(major["name"], userData=major["id"])

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
        """Returns the ID of selected major from dropdown."""
        return self._selected_id

    def custom_input_value(self):
        """Returns the custom input text if provided, otherwise None."""
        return self._custom_input if self._custom_input else None

    def reload_dropdown(self):
        """Reload the dropdown with latest data from the API."""
        self.combo_box.blockSignals(True)
        self.combo_box.clear()
        self._load_dropdown()
        self.combo_box.setCurrentIndex(0)  # Reset to placeholder
        self.combo_box.blockSignals(False)
