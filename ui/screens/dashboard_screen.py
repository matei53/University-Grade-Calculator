from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt
from ui.components.collapsible_year import CollapsibleYear
from ui.styles import DASHBOARD_STYLE 
from services.dashboard_service import DashboardService
from models.session import Session
from database.db import get_connection
import json
import os

class DashboardScreen(QWidget):
    # Move this here so it's a class constant
    UNI_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "universities.json")

    def __init__(self, router):
        super().__init__()
        self.router = router
        self.current_view_year = 1 
        
        # Load real data from database (will be empty if no user logged in during init)
        try:
            self.all_data = self._load_user_data()
        except RuntimeError:
            self.all_data = {}
        
        # Calculate total degree credits as sum of all subject credits
        self.total_degree_credits = sum(
            subject['credits'] 
            for year_data in self.all_data.values() 
            for subject in year_data['subjects']
        )

        self.setStyleSheet(DASHBOARD_STYLE)
        self.year_buttons = []
        self.year_components = {}
        self._build_ui()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 20, 40, 20)
        self.main_layout.setSpacing(20)

        # 1. Header
        header_layout = QHBoxLayout()
        title_container = QVBoxLayout()
        
        self.header_title = QLabel("UniGrade")
        self.header_title.setObjectName("HeaderTitle")

        user_info = self._get_logged_in_user_info()

        self.subtitle = QLabel(f"{user_info['university']} · {user_info['major']}")
        self.subtitle.setObjectName("HeaderSubtitle") # Set an ID instead of inline style
        
        title_container.addWidget(self.header_title)
        title_container.addWidget(self.subtitle)
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        
        add_grades_btn = QPushButton("+ Add Grades")
        add_grades_btn.setObjectName("SecondaryButton")
        add_grades_btn.setFixedWidth(120)
        add_grades_btn.clicked.connect(lambda: self.router.navigate("subject_setup"))
        
        logout_btn = QPushButton("Log Out")
        logout_btn.setFixedWidth(100)
        logout_btn.clicked.connect(self._handle_logout)
        
        header_layout.addWidget(add_grades_btn)
        header_layout.addWidget(logout_btn)
        self.main_layout.addLayout(header_layout)

        # 2. Filter Bar
        filter_widget = QWidget()
        self.filter_layout = QHBoxLayout(filter_widget)
        self.filter_layout.setContentsMargins(0, 0, 0, 0)
        
        self.filter_label = QLabel("View up to:")
        self.filter_label.setStyleSheet("font-weight: bold; color: #555;")
        self.filter_layout.addWidget(self.filter_label)

        print(f"[Dashboard._build_ui()] self.all_data.keys() = {list(self.all_data.keys())}")
        
        for year_num in sorted(self.all_data.keys()):
            print(f"[Dashboard._build_ui()] Creating button for Year {year_num}")
            btn = QPushButton(f"Year {year_num}")
            btn.setObjectName("FilterButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, y=year_num: self.update_dashboard(y))
            self.year_buttons.append(btn)
            self.filter_layout.addWidget(btn)
        
        print(f"[Dashboard._build_ui()] Created {len(self.year_buttons)} year buttons")
        
        self.filter_layout.addStretch()
        self.main_layout.addWidget(filter_widget)

        # 3. Main Stats Cards
        stats_layout = QHBoxLayout()
        self.media_card = self._create_stat_card("WEIGHTED AVERAGE", "—", "all graded subjects")
        self.credits_card = self._create_stat_card("CREDITS EARNED", "0", "out of 180 total")
        self.progress_card = self._create_stat_card("DEGREE PROGRESS", "0%", "completed")
        
        self.main_progress_bar = QProgressBar()
        self.main_progress_bar.setFixedHeight(10)
        self.main_progress_bar.setTextVisible(False)
        self.progress_card.layout().addWidget(self.main_progress_bar)

        stats_layout.addWidget(self.media_card)
        stats_layout.addWidget(self.credits_card)
        stats_layout.addWidget(self.progress_card)
        self.main_layout.addLayout(stats_layout)

        # 4. Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.years_container = QVBoxLayout(self.scroll_content)
        self.years_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(scroll)

        for year_num, data in self.all_data.items():
            collapsible = CollapsibleYear(f"Year {year_num}")
            collapsible.set_subjects(data['subjects'], data['target_credits'])
            self.years_container.addWidget(collapsible)
            self.year_components[year_num] = collapsible

        self.update_dashboard(1)

    def _create_stat_card(self, title, value, subtitle):
        card = QFrame(); card.setObjectName("StatCard")
        layout = QVBoxLayout(card)
        t_label = QLabel(title); t_label.setObjectName("CardTitle")
        v_label = QLabel(value); v_label.setObjectName("CardValue")
        s_label = QLabel(subtitle); s_label.setObjectName("CardSub")
        layout.addWidget(t_label); layout.addWidget(v_label); layout.addWidget(s_label)
        return card

    def update_dashboard(self, up_to_year):
        self.current_view_year = up_to_year 

        # 1. Update Filter Button Styles
        for btn in self.year_buttons:
            is_active = btn.text() == f"Year {up_to_year}"
            btn.setProperty("active", is_active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # 2. Get Stats using dynamic Degree Credits
        stats = DashboardService.calculate_stats(
            self.all_data, 
            up_to_year, 
            total_program_credits=self.total_degree_credits
        )

        # 3. Update Visibility for each year component
        for year_num, component in self.year_components.items():
            component.setVisible(year_num <= up_to_year)

        # 4. Update Main Stats Cards
        # Weighted Average
        self.media_card.findChild(QLabel, "CardValue").setText(f"{stats['weighted_avg']:.2f}")
        
        # Credits Earned
        self.credits_card.findChild(QLabel, "CardValue").setText(str(stats['credits']))
        
        # Use f-string with the dynamic total_degree_credits
        self.credits_card.findChild(QLabel, "CardSub").setText(f"out of {self.total_degree_credits} possible")
        
        # Degree Progress
        prog_int = int(stats['progress'])
        self.progress_card.findChild(QLabel, "CardValue").setText(f"{prog_int}%")
        self.main_progress_bar.setValue(prog_int)

    # def on_screen_shown(self):
    #     # Triggered by Router to refresh from DB
    #     self.update_dashboard(self.current_view_year)

    def on_screen_shown(self):
        # 1. Reload all data from DB to catch changes from Signup/Setup
        self.all_data = self._load_user_data()
        
        # 2. Recalculate total degree credits
        self.total_degree_credits = sum(
            subject['credits'] 
            for year_data in self.all_data.values() 
            for subject in year_data['subjects']
        )
        
        # 3. Rebuild year filter buttons
        self._rebuild_year_buttons()
        
        # 4. Rebuild year components
        self._rebuild_year_components()
        
        # 5. Update the Header labels (University/Major)
        info = self._get_logged_in_user_info()
        self.subtitle.setText(f"{info['university']} · {info['major']}")
        
        # 6. Refresh the UI components
        self.update_dashboard(self.current_view_year)

    def _rebuild_year_buttons(self):
        """Rebuild the year filter buttons based on current all_data."""
        # Clear the layout of all buttons (but keep the label and stretch)
        # We need to remove items starting from index 1 until we hit the stretch
        while self.filter_layout.count() > 2:  # Keep label (0) and stretch (last)
            item = self.filter_layout.takeAt(1)
            if item and item.widget():
                item.widget().deleteLater()
        
        # Clear old buttons list
        self.year_buttons = []
        
        # Add new buttons for each year
        print(f"[Dashboard._rebuild_year_buttons()] Rebuilding buttons for years: {sorted(self.all_data.keys())}")
        for year_num in sorted(self.all_data.keys()):
            btn = QPushButton(f"Year {year_num}")
            btn.setObjectName("FilterButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, y=year_num: self.update_dashboard(y))
            self.year_buttons.append(btn)
            # Insert before the stretch (which is at the end)
            self.filter_layout.insertWidget(self.filter_layout.count() - 1, btn)
        
        print(f"[Dashboard._rebuild_year_buttons()] Recreated {len(self.year_buttons)} year buttons")

    def _rebuild_year_components(self):
        """Rebuild the year components (CollapsibleYear widgets)."""
        # Clear old year components from the scroll area
        while self.years_container.count():
            widget = self.years_container.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        self.year_components = {}
        
        # Add new collapsible year components
        for year_num, data in self.all_data.items():
            collapsible = CollapsibleYear(f"Year {year_num}")
            collapsible.set_subjects(data['subjects'], data['target_credits'])
            self.years_container.addWidget(collapsible)
            self.year_components[year_num] = collapsible
        
        print(f"[Dashboard._rebuild_year_components()] Recreated {len(self.year_components)} year components")

    # def _get_logged_in_user_info(self):
    #     user = None
    #     try:
    #         user = Session.get_user()
    #     except RuntimeError:
    #         pass
        
    #     uni_name = "University of Bucharest"
    #     major_name = "Computer Science"

    #     if user:
    #         # Get university name
    #         if "university_id" in user and user["university_id"]:
    #             try:
    #                 with open(self.UNI_DATA_PATH, "r") as f:
    #                     universities = json.load(f)
    #                     for uni in universities:
    #                         if uni["id"] == user["university_id"]:
    #                             uni_name = uni["name"]
    #                             break
    #             except Exception:
    #                 pass
            
    #         # Get major name
    #         if "major_id" in user and user["major_id"]:
    #             try:
    #                 majors_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "majors.json")
    #                 with open(majors_path, "r") as f:
    #                     majors = json.load(f)
    #                     for major in majors:
    #                         if major["id"] == user["major_id"]:
    #                             major_name = major["name"]
    #                             break
    #             except Exception:
    #                 pass
        
    #     return {
    #         "university": uni_name, 
    #         "major": major_name
    #     }

    def _get_logged_in_user_info(self):
        try:
            user_id = Session.get_current_user_id()
            from repositories.user_repo import UserRepo
            repo = UserRepo()
            profile = repo.get_profile_info(user_id)
            
            return {
                "university": profile['university_name'] if profile and profile['university_name'] else "No University Set",
                "major": profile['major_name'] if profile and profile['major_name'] else "No Major Set"
            }
        except (RuntimeError, Exception):
            # Return default values if no user is logged in or error occurs
            return {"university": "UniGrade", "major": "Student"}

    def _load_user_data(self):
        """Load real user data from database and format it for the dashboard."""
        try:
            user_id = Session.get_current_user_id()
        except RuntimeError:
            return {}
        
        print(f"[Dashboard] Loading data for user {user_id}")
        all_data = {}
        
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all academic years for this user
            years = cursor.execute(
                "SELECT id, label, order_index, credit_requirement FROM academic_years WHERE user_id = ? ORDER BY order_index",
                (user_id,)
            ).fetchall()
            
            print(f"[Dashboard] Found {len(years)} years for user {user_id}")
            
            for year in years:
                year_id = year['id']
                year_num = year['order_index']
                target_credits = year['credit_requirement'] or 60
                
                print(f"[Dashboard] Processing Year {year_num} (ID: {year_id})")
                
                subjects_list = []
                
                # Get all semesters for this year
                semesters = cursor.execute(
                    "SELECT id, order_index FROM semesters WHERE academic_year_id = ? ORDER BY order_index",
                    (year_id,)
                ).fetchall()
                
                for semester in semesters:
                    semester_id = semester['id']
                    semester_num = semester['order_index']
                    
                    # Get all subjects for this semester
                    subjects = cursor.execute(
                        "SELECT id, name, credit_value FROM subjects WHERE semester_id = ? ORDER BY id",
                        (semester_id,)
                    ).fetchall()
                    
                    for subject in subjects:
                        subject_id = subject['id']
                        subject_name = subject['name']
                        credits = subject['credit_value']
                        
                        # Get assessments and grades for this subject
                        assessments = cursor.execute(
                            "SELECT id, weight FROM assessments WHERE subject_id = ? ORDER BY id",
                            (subject_id,)
                        ).fetchall()
                        
                        # Calculate weighted grade
                        weighted_grade = None
                        total_weight = 0
                        total_weighted_score = 0
                        
                        has_grade = False
                        for assessment in assessments:
                            assessment_id = assessment['id']
                            weight = assessment['weight']
                            
                            grade_row = cursor.execute(
                                "SELECT score FROM grades WHERE assessment_id = ?",
                                (assessment_id,)
                            ).fetchone()
                            
                            if grade_row and grade_row['score'] is not None:
                                has_grade = True
                                total_weight += weight
                                total_weighted_score += grade_row['score'] * weight
                        
                        if has_grade and total_weight > 0:
                            weighted_grade = total_weighted_score / total_weight
                        
                        subjects_list.append({
                            'name': subject_name,
                            'credits': credits,
                            'grade': weighted_grade,
                            'semester': semester_num
                        })
                
                all_data[year_num] = {
                    "target_credits": target_credits,
                    "subjects": subjects_list
                }
        
        return all_data

    def _handle_logout(self):
        Session.logout() # Using Person A's method
        self.router.navigate("login")