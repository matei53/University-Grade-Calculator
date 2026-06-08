from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class CollapsibleYear(QWidget):
    """
    Component representing a single academic year.
    Features a toggle header, year-specific statistics,
    and a breakdown of subjects by semester.
    """

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 10)
        self.layout.setSpacing(0)

        # 1. Expand/Collapse Toggle Button
        self.toggle_button = QToolButton()
        self.toggle_button.setObjectName("YearToggle")
        self.toggle_button.setText(title)
        self.toggle_button.setCheckable(True)

        # Apply the fix + ensure it stays left-aligned
        # We include the font-size here to kill the PointSize error
        self.toggle_button.setStyleSheet("font-size: 15px; text-align: left;")

        self.toggle_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.toggle_button.setArrowType(Qt.ArrowType.RightArrow)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        # 2. Content Area (Hidden by default)
        self.content_area = QFrame()
        self.content_area.setObjectName("YearContentArea")
        self.content_area.setVisible(False)
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(20, 20, 20, 20)

        self.layout.addWidget(self.toggle_button)
        self.layout.addWidget(self.content_area)
        self.toggle_button.clicked.connect(self._toggle)

    def _toggle(self):
        """Switches visibility of year content + updates arrow icon."""
        is_checked = self.toggle_button.isChecked()
        self.content_area.setVisible(is_checked)
        self.toggle_button.setArrowType(
            Qt.ArrowType.DownArrow if is_checked else Qt.ArrowType.RightArrow
        )

    def _create_mini_card(self, label, value):
        """Utility to create small stat boxes for the internal dashboard."""
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
        """
        Dynamically populates the year view with data.
        :param subjects: List of dictionaries containing subject details.
        :param year_target_credits: The credit requirement for this year.
        :param passing_grade: Minimum grade to count credits toward completion.
        """
        # Clear existing content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not subjects:
            self.content_layout.addWidget(QLabel("No data recorded for this academic year."))
            return

        # --- 1. Year Statistics Summary ---
        stats_row = QHBoxLayout()
        stats_row.setSpacing(15)

        graded_list = [s for s in subjects if s["grade"] is not None]

        # FIX 2: Only sum credits for subjects that are actually PASSED
        total_passed_creds = sum(
            s["credits"] for s in graded_list if s["grade"] >= s.get("passing_grade", passing_grade)
        )

        # We still want to see total credits Attempted vs Earned?
        # Usually, students want to see Earned/Target.
        weighted_sum = sum(s["grade"] * s["credits"] for s in graded_list)
        total_graded_creds = sum(s["credits"] for s in graded_list)

        avg_weighted = weighted_sum / total_graded_creds if total_graded_creds > 0 else 0
        avg_simple = sum(s["grade"] for s in graded_list) / len(graded_list) if graded_list else 0

        # Update mini cards to show passed credits
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

        # --- 2. Year Progress Bar ---
        prog_container = QWidget()
        prog_v = QVBoxLayout(prog_container)
        prog_v.setContentsMargins(0, 15, 0, 10)

        # FIX 2: Progress percentage now uses total_passed_creds
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

        # --- 3. Semester Grouping ---
        for sem in [1, 2]:
            sem_subs = [s for s in subjects if s.get("semester") == sem]
            if sem_subs:
                h = QLabel(f"SEMESTER {sem}")
                h.setObjectName("SemesterHeader")
                self.content_layout.addWidget(h)

                # Sort subjects: highest grades first, 'None' grades last
                sorted_subs = sorted(
                    sem_subs,
                    key=lambda x: (x["grade"] if x["grade"] is not None else -1),
                    reverse=True,
                )

                for sub in sorted_subs:
                    row = QFrame()
                    row.setObjectName("SubjectRow")
                    row_l = QHBoxLayout(row)
                    row_l.setContentsMargins(10, 8, 10, 8)

                    # 1. SUBJECT NAME & CREDIT SUBTITLE
                    name_info = QVBoxLayout()
                    n = QLabel(sub["name"])
                    n.setStyleSheet("font-weight: 600; font-size: 13px;")

                    grade_val = sub["grade"]
                    # logic for failure: must have a grade
                    # AND it must be below threshold
                    is_failed = grade_val is not None and grade_val < sub.get(
                        "passing_grade", passing_grade
                    )

                    credit_text = f"{sub['credits']} Credits"
                    if is_failed:
                        credit_text += " (Failed)"

                    c = QLabel(credit_text)
                    # Turn credit text red only if failed
                    c.setStyleSheet(f"color: {'#cc0000' if is_failed else '#888'}; \
                        font-size: 11px;")

                    name_info.addWidget(n)
                    name_info.addWidget(c)
                    row_l.addLayout(name_info)

                    row_l.addStretch()

                    # 2. GRADE LABEL (Passed, Failed, or Not Graded)
                    g = QLabel()
                    if grade_val is not None:
                        # CASE: GRADED (Passed or Failed)
                        g.setText(f"{grade_val:.2f}")
                        # Green if passed, Red if failed
                        grade_color = "#2D4B1D" if not is_failed else "#cc0000"
                        g.setStyleSheet(f"font-weight: bold; color: {grade_color}; \
                                font-size: 14px;")
                    else:
                        # CASE: NOT GRADED (Smaller and subtle)
                        g.setText("Not Graded")
                        g.setStyleSheet("color: #999; font-size: 10px; \
                            font-weight: normal; font-style: italic;")

                    row_l.addWidget(g)
                    self.content_layout.addWidget(row)
