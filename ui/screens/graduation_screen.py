from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from services.graduation_service import GraduationService
from ui.styles import DASHBOARD_STYLE


class _GraduationLoadWorker(QThread):
    finished = pyqtSignal(dict, list)  # settings, assessments
    error = pyqtSignal(str)

    def run(self):
        try:
            svc = GraduationService()
            settings = svc.get_settings()
            assessments = svc.get_final_assessments()
            self.finished.emit(settings, assessments)
        except Exception as e:
            self.error.emit(str(e))


class _AssessmentDialog(QDialog):
    """Dialog for adding or editing a final assessment."""

    def __init__(self, parent=None, data: Optional[dict] = None):
        super().__init__(parent)
        self.setWindowTitle("Final Assessment" if data is None else "Edit Assessment")
        self.setMinimumWidth(360)
        self.setStyleSheet(parent.styleSheet() if parent else DASHBOARD_STYLE)
        self._build(data or {})

    def _build(self, data: dict):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        def _row(label_text, widget):
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFixedWidth(110)
            row.addWidget(lbl)
            row.addWidget(widget)
            layout.addLayout(row)

        self.name_edit = QLineEdit(data.get("name", ""))
        self.name_edit.setPlaceholderText("e.g. Final Exam")
        self.name_edit.setObjectName("AuthInput")
        _row("Name:", self.name_edit)

        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(0.0, 100.0)
        self.weight_spin.setDecimals(1)
        self.weight_spin.setSuffix(" %")
        self.weight_spin.setValue(float(data.get("weight", 0.0)))
        self.weight_spin.setObjectName("AuthInput")
        _row("Weight:", self.weight_spin)

        self.max_score_spin = QDoubleSpinBox()
        self.max_score_spin.setRange(0.1, 10000.0)
        self.max_score_spin.setDecimals(2)
        self.max_score_spin.setValue(float(data.get("max_score", 10.0)))
        self.max_score_spin.setObjectName("AuthInput")
        _row("Max Score:", self.max_score_spin)

        self.passing_spin = QDoubleSpinBox()
        self.passing_spin.setRange(0.0, 10000.0)
        self.passing_spin.setDecimals(2)
        self.passing_spin.setValue(float(data.get("passing_grade", 5.0)))
        self.passing_spin.setObjectName("AuthInput")
        _row("Min pass score:", self.passing_spin)

        self.error_lbl = QLabel("")
        self.error_lbl.setObjectName("ErrorLabel")
        self.error_lbl.setWordWrap(True)
        layout.addWidget(self.error_lbl)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save")
        save_btn.setObjectName("PrimaryButton")
        save_btn.clicked.connect(self._validate_and_accept)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _validate_and_accept(self):
        if not self.name_edit.text().strip():
            self.error_lbl.setText("Name cannot be empty.")
            return
        self.accept()

    def get_values(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "weight": self.weight_spin.value(),
            "max_score": self.max_score_spin.value(),
            "passing_grade": self.passing_spin.value(),
        }


class GraduationScreen(QWidget):

    def __init__(self, router):
        super().__init__()
        self.router = router
        self._service = GraduationService()
        self._assessments: list[dict] = []
        self._settings: dict = {"subject_average_weight": 100.0, "max_grade": 10.0}
        self._worker: Optional[_GraduationLoadWorker] = None
        self.setStyleSheet(DASHBOARD_STYLE)
        self._build_ui()

    # ------------------------------------------------------------------
    # Build UI (called once)
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 20, 40, 20)
        root.setSpacing(20)

        # Header row
        header = QHBoxLayout()
        back_btn = QPushButton("← Back to Dashboard")
        back_btn.setObjectName("SecondaryButton")
        back_btn.setFixedWidth(180)
        back_btn.clicked.connect(lambda: self.router.navigate("dashboard"))
        title = QLabel("Final Assessments")
        title.setObjectName("HeaderTitle")
        header.addWidget(back_btn)
        header.addSpacing(20)
        header.addWidget(title)
        header.addStretch()
        root.addLayout(header)

        # Settings card
        settings_card = QFrame()
        settings_card.setObjectName("StatCard")
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setSpacing(10)

        settings_title = QLabel("GRADE COMPOSITION")
        settings_title.setObjectName("CardTitle")
        settings_layout.addWidget(settings_title)

        fields_row = QHBoxLayout()

        subj_lbl = QLabel("Subject average weight:")
        self.subj_weight_spin = QDoubleSpinBox()
        self.subj_weight_spin.setRange(0.0, 100.0)
        self.subj_weight_spin.setDecimals(1)
        self.subj_weight_spin.setSuffix(" %")
        self.subj_weight_spin.setFixedWidth(110)
        self.subj_weight_spin.setObjectName("AuthInput")

        max_lbl = QLabel("Max final grade:")
        self.max_grade_spin = QDoubleSpinBox()
        self.max_grade_spin.setRange(1.0, 100.0)
        self.max_grade_spin.setDecimals(2)
        self.max_grade_spin.setFixedWidth(90)
        self.max_grade_spin.setObjectName("AuthInput")

        save_settings_btn = QPushButton("Save")
        save_settings_btn.setObjectName("SecondaryButton")
        save_settings_btn.setFixedWidth(70)
        save_settings_btn.clicked.connect(self._save_settings)

        fields_row.addWidget(subj_lbl)
        fields_row.addWidget(self.subj_weight_spin)
        fields_row.addSpacing(20)
        fields_row.addWidget(max_lbl)
        fields_row.addWidget(self.max_grade_spin)
        fields_row.addSpacing(20)
        fields_row.addWidget(save_settings_btn)
        fields_row.addStretch()
        settings_layout.addLayout(fields_row)

        self.settings_error_lbl = QLabel("")
        self.settings_error_lbl.setObjectName("ErrorLabel")
        settings_layout.addWidget(self.settings_error_lbl)

        root.addWidget(settings_card)

        # Assessments card
        assessments_card = QFrame()
        assessments_card.setObjectName("StatCard")
        assessments_card_layout = QVBoxLayout(assessments_card)
        assessments_card_layout.setSpacing(10)

        asses_header = QHBoxLayout()
        asses_title = QLabel("FINAL ASSESSMENTS")
        asses_title.setObjectName("CardTitle")
        add_btn = QPushButton("+ Add Assessment")
        add_btn.setObjectName("SecondaryButton")
        add_btn.clicked.connect(self._add_assessment)
        asses_header.addWidget(asses_title)
        asses_header.addStretch()
        asses_header.addWidget(add_btn)
        assessments_card_layout.addLayout(asses_header)

        # Column header
        col_header = QFrame()
        col_layout = QHBoxLayout(col_header)
        col_layout.setContentsMargins(8, 0, 8, 0)
        for text, width in [
            ("Name", 180),
            ("Weight", 70),
            ("Score", 110),
            ("Max Score", 90),
            ("Min Pass Score", 110),
        ]:
            lbl = QLabel(text)
            lbl.setObjectName("CardTitle")
            lbl.setFixedWidth(width)
            col_layout.addWidget(lbl)
        col_layout.addStretch()
        assessments_card_layout.addWidget(col_header)

        # Scrollable list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(260)
        self._list_content = QWidget()
        self._list_layout = QVBoxLayout(self._list_content)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._list_layout.setSpacing(2)
        scroll.setWidget(self._list_content)
        assessments_card_layout.addWidget(scroll)

        self.weight_total_lbl = QLabel("")
        self.weight_total_lbl.setObjectName("CardSub")
        assessments_card_layout.addWidget(self.weight_total_lbl)

        root.addWidget(assessments_card)
        root.addStretch()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_screen_shown(self):
        self._service = GraduationService()
        if self._worker and self._worker.isRunning():
            try:
                self._worker.finished.disconnect()
                self._worker.error.disconnect()
            except Exception:
                pass
            self._worker.finished.connect(self._worker.deleteLater)
        self._worker = _GraduationLoadWorker()
        self._worker.finished.connect(self._on_data_loaded)
        self._worker.error.connect(lambda e: print(f"Error loading graduation data: {e}"))
        self._worker.start()

    def _on_data_loaded(self, settings: dict, assessments: list):
        self._settings = settings
        self._assessments = assessments
        self.subj_weight_spin.setValue(settings.get("subject_average_weight", 100.0))
        self.max_grade_spin.setValue(settings.get("max_grade", 10.0))
        self._rebuild_list()

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _save_settings(self):
        self.settings_error_lbl.setText("")
        try:
            self._settings = self._service.update_settings(
                self.subj_weight_spin.value(),
                self.max_grade_spin.value(),
            )
            self._update_weight_total()
        except Exception as e:
            self.settings_error_lbl.setText(f"Error: {e}")

    # ------------------------------------------------------------------
    # Assessment list
    # ------------------------------------------------------------------

    def _rebuild_list(self):
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for a in self._assessments:
            self._list_layout.addWidget(self._make_row(a))

        self._update_weight_total()

    def _make_row(self, data: dict) -> QFrame:
        row = QFrame()
        row.setObjectName("SubjectRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(8, 6, 8, 6)

        max_score = float(data.get("max_score", 10.0))
        passing_grade = float(data.get("passing_grade", 5.0))
        grade_obj = data.get("grade")
        current_score = (
            float(grade_obj["score"]) if grade_obj and grade_obj.get("score") is not None else None
        )
        is_failing = current_score is not None and current_score < passing_grade

        name_lbl = QLabel(data["name"])
        name_lbl.setFixedWidth(180)
        name_lbl.setWordWrap(True)
        if is_failing:
            name_lbl.setStyleSheet("color: #c0392b; font-weight: bold;")

        weight_lbl = QLabel(f"{data['weight']:.1f}%")
        weight_lbl.setFixedWidth(70)

        score_spin = QDoubleSpinBox()
        score_spin.setRange(-1.0, max_score)
        score_spin.setDecimals(2)
        score_spin.setSpecialValueText("—")
        score_spin.setFixedWidth(100)
        score_spin.setObjectName("AuthInput")
        score_spin.setValue(current_score if current_score is not None else -1.0)

        max_lbl = QLabel(str(max_score))
        max_lbl.setFixedWidth(90)

        passing_lbl = QLabel(str(passing_grade))
        passing_lbl.setFixedWidth(110)

        fail_badge = QLabel("✗ FAIL" if is_failing else "")
        fail_badge.setFixedWidth(55)
        fail_badge.setStyleSheet("color: #c0392b; font-weight: bold; font-size: 11px;")

        save_score_btn = QPushButton("Save score")
        save_score_btn.setMinimumWidth(80)
        save_score_btn.setObjectName("SecondaryButton")
        a_id = data["id"]
        save_score_btn.clicked.connect(lambda _, sid=a_id, sp=score_spin: self._save_score(sid, sp))

        edit_btn = QPushButton("Edit")
        edit_btn.setFixedWidth(50)
        edit_btn.clicked.connect(lambda _, d=data: self._edit_assessment(d))

        del_btn = QPushButton("✕")
        del_btn.setFixedWidth(36)
        del_btn.setStyleSheet("color: #c0392b; font-weight: bold;")
        del_btn.clicked.connect(lambda _, sid=a_id: self._delete_assessment(sid))

        for w in (name_lbl, weight_lbl, score_spin, max_lbl, passing_lbl, fail_badge):
            layout.addWidget(w)
        layout.addStretch()
        layout.addWidget(save_score_btn)
        layout.addWidget(edit_btn)
        layout.addWidget(del_btn)

        return row

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _add_assessment(self):
        dlg = _AssessmentDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        v = dlg.get_values()
        try:
            new_a = self._service.add_final_assessment(
                v["name"], v["weight"], v["max_score"], v["passing_grade"]
            )
            self._assessments.append(new_a)
            self._rebuild_list()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _edit_assessment(self, data: dict):
        dlg = _AssessmentDialog(self, data)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        v = dlg.get_values()
        try:
            updated = self._service.update_final_assessment(
                data["id"], v["name"], v["weight"], v["max_score"], v["passing_grade"]
            )
            self._assessments = [updated if a["id"] == data["id"] else a for a in self._assessments]
            self._rebuild_list()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _delete_assessment(self, assessment_id: int):
        reply = QMessageBox.question(
            self,
            "Delete",
            "Delete this final assessment?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self._service.delete_final_assessment(assessment_id)
            self._assessments = [a for a in self._assessments if a["id"] != assessment_id]
            self._rebuild_list()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _save_score(self, assessment_id: int, spin: QDoubleSpinBox):
        score = None if spin.value() < 0 else spin.value()
        try:
            updated = self._service.set_grade(assessment_id, score)
            self._assessments = [
                updated if a["id"] == assessment_id else a for a in self._assessments
            ]
            self._rebuild_list()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _update_weight_total(self):
        subj_w = self._settings.get("subject_average_weight", 100.0)
        fa_total = sum(a.get("weight", 0.0) for a in self._assessments)
        total = subj_w + fa_total
        color = "#2D4B1D" if abs(total - 100.0) < 0.05 else "#c0392b"
        self.weight_total_lbl.setText(
            f'<span style="color:{color}">Total weight: {total:.1f}% '
            f"(subject avg {subj_w:.1f}% + assessments {fa_total:.1f}%)"
            f'{"  ✓" if abs(total - 100.0) < 0.05 else "  — should sum to 100%"}</span>'
        )
        self.weight_total_lbl.setTextFormat(Qt.TextFormat.RichText)
