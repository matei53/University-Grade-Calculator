from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QToolButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QDoubleSpinBox,
    QProgressBar,
)

from client.api_client import APIClient
from services.grade_service import GradeService
from ui.components.assessment_row import AssessmentRow


class EditSubjectDialog(QDialog):
    def __init__(self, parent, subject: dict, api_client: APIClient, refresh_callback=None):
        super().__init__(parent)
        self.subject = subject
        self.api_client = api_client
        self.refresh_callback = refresh_callback
        self.assessment_rows = []
        self.deleted_assessment_ids = []
        self.setWindowTitle("Edit Subject")
        # Increase dialog size to avoid cramped layout
        self.setMinimumWidth(720)
        self.resize(720, 560)

        self._load_year_options()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        form = QFormLayout()
        self.name_input = QLineEdit(subject.get("name", ""))
        self.name_input.setPlaceholderText("Subject name")
        form.addRow("Subject Name:", self.name_input)

        self.year_combo = QComboBox()
        self.year_combo.setObjectName("AuthInput")
        form.addRow("Academic Year:", self.year_combo)

        self.semester_input = QSpinBox()
        self.semester_input.setObjectName("AuthInput")
        self.semester_input.setRange(1, 2)
        form.addRow("Semester:", self.semester_input)

        self.credits_input = QSpinBox()
        self.credits_input.setObjectName("AuthInput")
        self.credits_input.setRange(1, 30)
        form.addRow("Credits:", self.credits_input)

        self.max_grade_input = QDoubleSpinBox()
        self.max_grade_input.setObjectName("AuthInput")
        self.max_grade_input.setRange(1.0, 100.0)
        self.max_grade_input.setDecimals(2)
        self.max_grade_input.setValue(subject.get("max_grade", 10.0))
        form.addRow("Max Grade:", self.max_grade_input)

        self.passing_grade_input = QDoubleSpinBox()
        self.passing_grade_input.setObjectName("AuthInput")
        self.passing_grade_input.setRange(0.0, 100.0)
        self.passing_grade_input.setDecimals(2)
        self.passing_grade_input.setValue(subject.get("passing_grade", 5.0))
        form.addRow("Passing Grade:", self.passing_grade_input)

        layout.addLayout(form)

        # "ASSESSMENTS" on the left, running weight total on the right
        section_header_row = QHBoxLayout()
        assessment_header = QLabel("ASSESSMENTS")
        assessment_header.setStyleSheet(
            "color: #2D4B1D; font-weight: bold; font-size: 11px; letter-spacing: 1px;"
        )
        self.weight_status_label = QLabel("Total Weight: 0.0%")
        self.weight_status_label.setStyleSheet("color: #D32F2F; font-weight: bold; font-size: 12px;")
        section_header_row.addWidget(assessment_header)
        section_header_row.addStretch()
        section_header_row.addWidget(self.weight_status_label)
        layout.addLayout(section_header_row)

        # Column headers — widths mirror the fixed widths used in add_assessment_row
        col_header_widget = QWidget()
        col_header_layout = QHBoxLayout(col_header_widget)
        col_header_layout.setContentsMargins(0, 0, 0, 0)
        col_header_layout.setSpacing(6)
        name_col_hdr = QLabel("Name")
        name_col_hdr.setStyleSheet("color: #555; font-size: 10px; font-weight: bold;")
        col_header_layout.addWidget(name_col_hdr, 1)
        for col_text, col_w in [("Weight", 80), ("Grade", 80), ("Max Score", 80), ("Min. Pass", 80), ("", 30)]:
            lbl = QLabel(col_text)
            lbl.setStyleSheet("color: #555; font-size: 10px; font-weight: bold;")
            lbl.setFixedWidth(col_w)
            col_header_layout.addWidget(lbl)
        layout.addWidget(col_header_widget)

        self.assessments_container = QScrollArea()
        self.assessments_container.setWidgetResizable(True)
        self.assessments_container.setFixedHeight(200)
        self.assessments_container.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.assessments_container.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        assessments_widget = QWidget()
        self.assessments_layout = QVBoxLayout(assessments_widget)
        self.assessments_layout.setContentsMargins(0, 2, 0, 2)
        self.assessments_layout.setSpacing(8)
        self.assessments_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.assessments_container.setWidget(assessments_widget)
        layout.addWidget(self.assessments_container)

        self.add_assessment_btn = QPushButton("+ Add Assessment Component")
        self.add_assessment_btn.setObjectName("SecondaryButton")
        self.add_assessment_btn.clicked.connect(self.add_assessment_row)
        layout.addWidget(self.add_assessment_btn)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self._save_changes)
        self.save_button.setDefault(True)
        button_row.addWidget(self.save_button)

        button_row.addStretch()

        self.delete_button = QPushButton("Delete Subject Entirely")
        self.delete_button.setStyleSheet(
            "background-color: #cc0000; color: #ffffff; padding: 10px;"
        )
        self.delete_button.clicked.connect(self._delete_subject)
        self.delete_button.setFixedHeight(40)
        button_row.addWidget(self.delete_button)

        layout.addLayout(button_row)

        close_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_box.rejected.connect(self.reject)
        layout.addWidget(close_box)

        self._populate_fields()

    def _load_year_options(self):
        try:
            self.academic_years = self.api_client.get_academic_years()
        except Exception:
            self.academic_years = []

    def _populate_fields(self):
        self.year_combo.clear()
        if self.academic_years:
            for year in self.academic_years:
                self.year_combo.addItem(f"Year {year['order_index']}", year["order_index"])
        else:
            for i in range(1, 4):
                self.year_combo.addItem(f"Year {i}", i)

        year_level = self.subject.get("year_level", 1)
        year_index = 0
        for index in range(self.year_combo.count()):
            if self.year_combo.itemData(index) == year_level:
                year_index = index
                break
        self.year_combo.setCurrentIndex(year_index)

        self.semester_input.setValue(self.subject.get("semester_index", 1))
        self.credits_input.setValue(self.subject.get("credits", 5))
        self.max_grade_input.setValue(self.subject.get("max_grade", 10.0))
        self.passing_grade_input.setValue(self.subject.get("passing_grade", 5.0))

        existing_assessments = self.subject.get("assessments", [])
        if existing_assessments:
            for assessment in existing_assessments:
                self.add_assessment_row(assessment)
        else:
            self.add_assessment_row()

        self._update_weight_status()

    def add_assessment_row(self, assessment_data=None):
        row = AssessmentRow()
        row.name_input.setPlaceholderText("Name (e.g. Exam)")
        # Clear verbose embedded prefixes — the column headers above provide context
        row.weight_input.setPrefix("")
        row.weight_input.setSuffix(" %")
        row.score_input.setPrefix("")
        row.max_score_input.setPrefix("")
        row.passing_grade_input.setPrefix("")
        # Fixed widths keep every row's columns aligned under the headers
        row.weight_input.setFixedWidth(80)
        row.score_input.setFixedWidth(80)
        row.max_score_input.setFixedWidth(80)
        row.passing_grade_input.setFixedWidth(80)
        row.remove_btn.setFixedWidth(30)
        if row.layout():
            row.layout().setSpacing(6)
        row.remove_requested.connect(self.remove_assessment_row)
        row.weight_changed.connect(self._update_weight_status)
        row.score_changed.connect(self._update_weight_status)

        if assessment_data:
            row.name_input.setText(assessment_data.get("name", ""))
            row.weight_input.setValue(float(assessment_data.get("weight", 0.0)))
            grade_score = assessment_data.get("grade_score")
            row.score_input.setValue(-1.0 if grade_score is None else float(grade_score))
            row.max_score_input.setValue(float(assessment_data.get("max_score", 10.0)))
            row.passing_grade_input.setValue(float(assessment_data.get("passing_grade", 5.0)))
            row.assessment_id = assessment_data.get("id")
            row.grade_id = assessment_data.get("grade_id")
        else:
            row.assessment_id = None
            row.grade_id = None

        self.assessment_rows.append(row)
        self.assessments_layout.addWidget(row)
        self._update_weight_status()

    def remove_assessment_row(self, row_widget):
        if len(self.assessment_rows) <= 1:
            QMessageBox.warning(self, "Warning", "At least one assessment component is required.")
            return

        self.assessment_rows.remove(row_widget)
        self.assessments_layout.removeWidget(row_widget)
        if getattr(row_widget, "assessment_id", None):
            self.deleted_assessment_ids.append(row_widget.assessment_id)
        row_widget.deleteLater()
        self._update_weight_status()

    def _update_weight_status(self):
        total_weight = sum(float(row.weight_input.value()) for row in self.assessment_rows)
        self.weight_status_label.setText(f"Total Weight: {total_weight:.1f}%")
        color = "#2D4B1D" if total_weight == 100.0 else "#D32F2F"
        self.weight_status_label.setStyleSheet(
            f"color: {color}; font-weight: bold; font-size: 12px;"
        )

    def _save_changes(self):
        if not self.api_client:
            return

        subject_name = self.name_input.text().strip()
        if not subject_name:
            QMessageBox.warning(self, "Validation Error", "Subject name cannot be empty.")
            return

        assessments_payload = []
        for row in self.assessment_rows:
            assessments_payload.append(
                {
                    "assessment_id": getattr(row, "assessment_id", None),
                    "grade_id": getattr(row, "grade_id", None),
                    "name": row.name_input.text().strip(),
                    "weight": float(row.weight_input.value()),
                    "score": None if row.score_input.value() < 0 else float(row.score_input.value()),
                    "max_score": float(row.max_score_input.value()),
                    "passing_grade": float(row.passing_grade_input.value()),
                }
            )

        if not GradeService.validate_weights_total(assessments_payload):
            QMessageBox.warning(self, "Validation Error", "Total assessment weights must equal 100%.")
            return

        # Safely obtain raw year from the combo (can be data or text)
        raw_year = self.year_combo.currentData()
        try:
            year_level = int(raw_year)
        except (TypeError, ValueError):
            try:
                year_level = int(self.year_combo.currentText().replace("Year ", ""))
            except Exception:
                year_level = int(self.year_combo.currentText().split(" ")[-1])

        try:
            self.api_client.update_subject(
                subject_id=self.subject.get("subject_id"),
                name=subject_name,
                credits=self.credits_input.value(),
                semester_index=self.semester_input.value(),
                year_level=year_level,
                passing_grade=self.passing_grade_input.value(),
                max_grade=self.max_grade_input.value(),
            )

            for assessment in assessments_payload:
                if assessment["assessment_id"]:
                    self.api_client.update_assessment(
                        assessment_id=assessment["assessment_id"],
                        name=assessment["name"],
                        weight=assessment["weight"],
                        max_score=assessment["max_score"],
                        passing_grade=assessment["passing_grade"],
                    )
                    if assessment["grade_id"] is not None:
                        self.api_client.update_grade(
                            grade_id=assessment["grade_id"],
                            score=assessment["score"],
                        )
                else:
                    self.api_client.add_assessment(
                        subject_id=self.subject.get("subject_id"),
                        name=assessment["name"],
                        weight=assessment["weight"],
                        score=assessment["score"],
                        max_score=assessment["max_score"],
                        passing_grade=assessment["passing_grade"],
                    )

            for assessment_id in self.deleted_assessment_ids:
                self.api_client.delete_assessment(assessment_id)

            QMessageBox.information(self, "Saved", "Subject changes have been saved.")
            if self.refresh_callback:
                try:
                    self.refresh_callback()
                except Exception:
                    pass
                self.refresh_callback = None  # prevent double-call from closeEvent
            self.accept()
        except Exception as error:
            QMessageBox.critical(self, "Save Failed", str(error))

    def _delete_subject(self):
        if not self.api_client:
            return

        confirm = QMessageBox.critical(
            self,
            "Delete Subject",
            "Delete this subject and all associated grades? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            self.api_client.delete_subject(self.subject.get("subject_id"))

            # Immediately remove the subject row from the parent UI so it vanishes instantly.
            parent_widget = self.parent()
            if parent_widget and hasattr(parent_widget, "remove_subject_widget"):
                try:
                    parent_widget.remove_subject_widget(self.subject.get("subject_id"))
                except Exception:
                    pass

            if self.refresh_callback:
                try:
                    self.refresh_callback()
                except Exception:
                    pass
                self.refresh_callback = None  # prevent double-call from closeEvent

            QMessageBox.information(self, "Deleted", "Subject has been deleted.")
            self.accept()
        except Exception as error:
            QMessageBox.critical(self, "Delete Failed", str(error))

    def closeEvent(self, event):
        if self.refresh_callback:
            self.refresh_callback()
        super().closeEvent(event)


class CollapsibleYear(QWidget):
    """
    Component representing a single academic year.
    Features a toggle header, year-specific statistics,
    and a breakdown of subjects by semester.
    """

    def __init__(self, title="", api_client=None, refresh_callback=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.refresh_callback = refresh_callback
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 10)
        self.layout.setSpacing(0)

        self.toggle_button = QToolButton()
        self.toggle_button.setObjectName("YearToggle")
        self.toggle_button.setText(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setStyleSheet("font-size: 15px; text-align: left;")
        self.toggle_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.toggle_button.setArrowType(Qt.ArrowType.RightArrow)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        self.content_area = QFrame()
        self.content_area.setObjectName("YearContentArea")
        self.content_area.setVisible(False)
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(20, 20, 20, 20)

        self.layout.addWidget(self.toggle_button)
        self.layout.addWidget(self.content_area)
        self.toggle_button.clicked.connect(self._toggle)

    def _toggle(self):
        is_checked = self.toggle_button.isChecked()
        self.content_area.setVisible(is_checked)
        self.toggle_button.setArrowType(
            Qt.ArrowType.DownArrow if is_checked else Qt.ArrowType.RightArrow
        )

    def _create_mini_card(self, label, value):
        card = QFrame()
        card.setObjectName("MiniStatCard")
        l_ = QVBoxLayout(card)
        l_.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 10px; color: #666; text-transform: uppercase;")
        val = QLabel(value)
        val.setStyleSheet("font-weight: bold; font-size: 16px; color: #2D4B1D;")

        l_.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        l_.addWidget(val, alignment=Qt.AlignmentFlag.AlignCenter)
        return card

    def set_subjects(self, subjects, year_target_credits, passing_grade=5.0):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not subjects:
            self.content_layout.addWidget(QLabel("No data recorded for this academic year."))
            return

        stats_row = QHBoxLayout()
        stats_row.setSpacing(15)
        graded_list = [s for s in subjects if s["grade"] is not None]
        total_passed_creds = sum(
            s["credits"] for s in graded_list if s["grade"] >= s.get("passing_grade", passing_grade)
        )
        weighted_sum = sum(s["grade"] * s["credits"] for s in graded_list)
        total_graded_creds = sum(s["credits"] for s in graded_list)
        avg_weighted = weighted_sum / total_graded_creds if total_graded_creds > 0 else 0
        avg_simple = sum(s["grade"] for s in graded_list) / len(graded_list) if graded_list else 0

        stats_row.addWidget(
            self._create_mini_card(
                "Passed Credits",
                f"{total_passed_creds}/{year_target_credits}",
            )
        )
        stats_row.addWidget(self._create_mini_card("Weighted Avg", f"{avg_weighted:.2f}"))
        stats_row.addWidget(self._create_mini_card("Simple Avg", f"{avg_simple:.2f}"))
        stats_row.addWidget(self._create_mini_card("Graded", f"{len(graded_list)}/{len(subjects)}"))
        self.content_layout.addLayout(stats_row)

        prog_container = QWidget()
        prog_v = QVBoxLayout(prog_container)
        prog_v.setContentsMargins(0, 15, 0, 10)

        progress_percentage = (
            int((total_passed_creds / year_target_credits) * 100) if year_target_credits > 0 else 0
        )

        prog_label = QLabel(f"Annual Progress: {progress_percentage}%")
        prog_label.setStyleSheet("font-size: 11px; color: #444; font-weight: bold;")

        bar = QProgressBar()
        bar.setFixedHeight(12)
        bar.setValue(progress_percentage)
        bar.setTextVisible(False)

        prog_v.addWidget(prog_label)
        prog_v.addWidget(bar)
        self.content_layout.addWidget(prog_container)

        for sem in [1, 2]:
            sem_subs = [s for s in subjects if s.get("semester_index") == sem]
            if sem_subs:
                h = QLabel(f"SEMESTER {sem}")
                h.setObjectName("SemesterHeader")
                self.content_layout.addWidget(h)

                sorted_subs = sorted(
                    sem_subs,
                    key=lambda x: (x["grade"] if x["grade"] is not None else -1),
                    reverse=True,
                )

                for sub in sorted_subs:
                    row = QFrame()
                    row.setObjectName("SubjectRow")
                    # attach subject id for quick lookup/removal
                    row.subject_id = sub.get("subject_id")
                    row_l = QHBoxLayout(row)
                    row_l.setContentsMargins(10, 8, 10, 8)

                    name_info = QVBoxLayout()
                    n = QLabel(sub["name"])
                    n.setStyleSheet("font-weight: 600; font-size: 13px;")

                    grade_val = sub["grade"]
                    is_failed = grade_val is not None and grade_val < sub.get("passing_grade", passing_grade)

                    credit_text = f"{sub['credits']} Credits"
                    if is_failed:
                        credit_text += " (Failed)"

                    c = QLabel(credit_text)
                    c.setStyleSheet(
                        f"color: {'#cc0000' if is_failed else '#888'}; font-size: 11px;"
                    )

                    name_info.addWidget(n)
                    name_info.addWidget(c)
                    row_l.addLayout(name_info)

                    row_l.addStretch()

                    grade_label = QLabel()
                    if grade_val is not None:
                        grade_label.setText(f"{grade_val:.2f}")
                        grade_color = "#2D4B1D" if not is_failed else "#cc0000"
                        grade_label.setStyleSheet(
                            f"font-weight: bold; color: {grade_color}; font-size: 14px;"
                        )
                    else:
                        grade_label.setText("Not Graded")
                        grade_label.setStyleSheet(
                            "color: #999; font-size: 11px; font-style: italic;"
                        )
                    grade_label.setFixedWidth(100)
                    row_l.addWidget(grade_label, alignment=Qt.AlignmentFlag.AlignVCenter)

                    edit_btn = QPushButton("Edit")
                    edit_btn.setFixedWidth(80)
                    edit_btn.clicked.connect(lambda _, s=sub: self._open_edit_dialog(s))
                    row_l.addWidget(edit_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

                    self.content_layout.addWidget(row)

    def _open_edit_dialog(self, subject: dict):
        if not self.api_client:
            return

        dialog = EditSubjectDialog(self, subject, self.api_client, refresh_callback=self.refresh_callback)
        dialog.exec()

    def remove_subject_widget(self, subject_id: int):
        # Iterate widgets in content_layout and remove the matching subject row
        for i in reversed(range(self.content_layout.count())):
            item = self.content_layout.itemAt(i)
            w = item.widget()
            if w and getattr(w, "subject_id", None) == subject_id:
                # remove from layout and delete
                self.content_layout.removeWidget(w)
                w.setParent(None)
                w.deleteLater()
                return
