import json
import os
from PyQt6.QtWidgets import QComboBox

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "universities.json")

class UniversityPicker(QComboBox):
    def __init__(self):
        super().__init__()
        self._universities = []
        self._load()

    def _load(self):
        self.addItem("Select your university...", userData=None)
        try:
            with open(DATA_PATH, "r") as f:
                self._universities = json.load(f)  # expects [{"id": 1, "name": "..."}]
            for uni in self._universities:
                self.addItem(uni["name"], userData=uni["id"])
        except FileNotFoundError:
            pass  # Picker still works, just empty

    def selected_id(self):
        return self.currentData()  # returns None if placeholder is selected