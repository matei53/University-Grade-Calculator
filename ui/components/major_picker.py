import json
import os
from PyQt6.QtWidgets import QComboBox

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "majors.json")

class MajorPicker(QComboBox):
    def __init__(self):
        super().__init__()
        self._load()

    def _load(self):
        self.addItem("Select your major...", userData=None)
        try:
            with open(DATA_PATH, "r") as f:
                majors = json.load(f)
            for major in majors:
                self.addItem(major["name"], userData=major["id"])
        except FileNotFoundError:
            pass

    def selected_id(self):
        return self.currentData()