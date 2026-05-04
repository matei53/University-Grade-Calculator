# from PyQt6.QtWidgets import (
#     QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
#     QScrollArea, QFrame, QProgressBar
# )
# from PyQt6.QtCore import Qt
# from ui.components.collapsible_year import CollapsibleYear
# from ui.styles import DASHBOARD_STYLE 
# from services.dashboard_service import DashboardService
# from models.session import Session
# import json
# import os

# class DashboardScreen(QWidget):
#     # Move this here so it's a class constant
#     UNI_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "universities.json")

#     def __init__(self, router):
#         super().__init__()
#         self.router = router
#         self.current_view_year = 1 
        
#         # Fetch user settings (Mocked for now)
#         user_info = self._get_logged_in_user_info()
#         self.passing_grade = user_info.get('passing_grade', 5.0)
#         self.total_degree_credits = user_info.get('total_degree_credits', 180)

#         # MOCK DATA
#         self.all_data = {
#             1: {
#                 "target_credits": 60,
#                 "subjects": [
#                     # --- Semester 1 (30 Credits Total) ---
#                     {'name': 'Linear Algebra', 'credits': 6, 'grade': 5.65, 'semester': 1},
#                     {'name': 'Mathematical Analysis', 'credits': 5, 'grade': 5.50, 'semester': 1},
#                     {'name': 'Programming Fundamentals', 'credits': 5, 'grade': 5.00, 'semester': 1},
#                     {'name': 'Computational Logic', 'credits': 4, 'grade': 4, 'semester': 1},
#                     {'name': 'Mock Subject 1', 'credits': 5, 'grade': None, 'semester': 1},
#                     {'name': 'Mock Subject 2', 'credits': 5, 'grade': None, 'semester': 1},

#                     # --- Semester 2 (30 Credits Total) ---
#                     {'name': 'Data Structures', 'credits': 6, 'grade': None, 'semester': 2},
#                     {'name': 'Mock Subject 3', 'credits': 5, 'grade': None, 'semester': 2},
#                     {'name': 'Mock Subject 4', 'credits': 5, 'grade': None, 'semester': 2},
#                     {'name': 'Mock Subject 5', 'credits': 5, 'grade': None, 'semester': 2},
#                     {'name': 'Mock Subject 6', 'credits': 5, 'grade': None, 'semester': 2},
#                     {'name': 'Mock Subject 7', 'credits': 4, 'grade': None, 'semester': 2},
#                 ]
#             },
#             2: { 
#                 "target_credits": 60, 
#                 "subjects": [
#                     {'name': 'Baze de date', 'credits': 6, 'grade': 5, 'semester': 1},
#                     {'name': 'Rețele de calculatoare', 'credits': 5, 'grade': 6, 'semester': 1},
#                     {'name': 'Inginerie software', 'credits': 6, 'grade': 7, 'semester': 2},
#                     {'name': 'Metode avansate de programare', 'credits': 6, 'grade': None, 'semester': 2},
#                 ] 
#             },
#             3: { "target_credits": 60, "subjects": [] }
#         }

#         self.setStyleSheet(DASHBOARD_STYLE)
#         self.year_buttons = []
#         self.year_components = {}
#         self._build_ui()

#     def _build_ui(self):
#         self.main_layout = QVBoxLayout(self)
#         self.main_layout.setContentsMargins(40, 20, 40, 20)
#         self.main_layout.setSpacing(20)

#         # 1. Header
#         header_layout = QHBoxLayout()
#         title_container = QVBoxLayout()
        
#         self.header_title = QLabel("UniGrade")
#         self.header_title.setObjectName("HeaderTitle")

#         user_info = self._get_logged_in_user_info()
#         self.passing_grade = user_info.get('passing_grade', 5.0) 
#         self.total_degree_credits = 180 # Can also be moved to user_info later

#         self.subtitle = QLabel(f"{user_info['university']} · {user_info['major']}")
#         self.subtitle.setObjectName("HeaderSubtitle") # Set an ID instead of inline style
        
#         title_container.addWidget(self.header_title)
#         title_container.addWidget(self.subtitle)
#         header_layout.addLayout(title_container)
#         header_layout.addStretch()
        
#         logout_btn = QPushButton("Log Out")
#         logout_btn.setFixedWidth(100)
#         logout_btn.clicked.connect(self._handle_logout)
#         header_layout.addWidget(logout_btn)
#         self.main_layout.addLayout(header_layout)

#         # 2. Filter Bar
#         filter_widget = QWidget()
#         filter_layout = QHBoxLayout(filter_widget)
#         filter_layout.setContentsMargins(0, 0, 0, 0)
        
#         filter_label = QLabel("View up to:")
#         filter_label.setStyleSheet("font-weight: bold; color: #555;")
#         filter_layout.addWidget(filter_label)

#         for year_num in sorted(self.all_data.keys()):
#             btn = QPushButton(f"Year {year_num}")
#             btn.setObjectName("FilterButton")
#             btn.setCheckable(True)
#             btn.clicked.connect(lambda checked, y=year_num: self.update_dashboard(y))
#             self.year_buttons.append(btn)
#             filter_layout.addWidget(btn)
        
#         filter_layout.addStretch()
#         self.main_layout.addWidget(filter_widget)

#         # 3. Main Stats Cards
#         stats_layout = QHBoxLayout()
#         self.media_card = self._create_stat_card("WEIGHTED AVERAGE", "—", "all graded subjects")
#         self.credits_card = self._create_stat_card("CREDITS EARNED", "0", "out of 180 total")
#         self.progress_card = self._create_stat_card("DEGREE PROGRESS", "0%", "completed")
        
#         self.main_progress_bar = QProgressBar()
#         self.main_progress_bar.setFixedHeight(10)
#         self.main_progress_bar.setTextVisible(False)
#         self.progress_card.layout().addWidget(self.main_progress_bar)

#         stats_layout.addWidget(self.media_card)
#         stats_layout.addWidget(self.credits_card)
#         stats_layout.addWidget(self.progress_card)
#         self.main_layout.addLayout(stats_layout)

#         # 4. Scroll Area
#         scroll = QScrollArea()
#         scroll.setWidgetResizable(True)
#         self.scroll_content = QWidget()
#         self.years_container = QVBoxLayout(self.scroll_content)
#         self.years_container.setAlignment(Qt.AlignmentFlag.AlignTop)
#         scroll.setWidget(self.scroll_content)
#         self.main_layout.addWidget(scroll)

#         for year_num, data in self.all_data.items():
#             collapsible = CollapsibleYear(f"Year {year_num}")
#             collapsible.set_subjects(data['subjects'], data['target_credits'])
#             self.years_container.addWidget(collapsible)
#             self.year_components[year_num] = collapsible

#         self.update_dashboard(1)

#     def _create_stat_card(self, title, value, subtitle):
#         card = QFrame(); card.setObjectName("StatCard")
#         layout = QVBoxLayout(card)
#         t_label = QLabel(title); t_label.setObjectName("CardTitle")
#         v_label = QLabel(value); v_label.setObjectName("CardValue")
#         s_label = QLabel(subtitle); s_label.setObjectName("CardSub")
#         layout.addWidget(t_label); layout.addWidget(v_label); layout.addWidget(s_label)
#         return card

#     def update_dashboard(self, up_to_year):
#         self.current_view_year = up_to_year 

#         # 1. Update Filter Button Styles
#         for btn in self.year_buttons:
#             is_active = btn.text() == f"Year {up_to_year}"
#             btn.setProperty("active", is_active)
#             btn.style().unpolish(btn)
#             btn.style().polish(btn)

#         # 2. Get Stats using dynamic Degree Credits and Passing Grade
#         stats = DashboardService.calculate_stats(
#             self.all_data, 
#             up_to_year, 
#             total_program_credits=self.total_degree_credits,
#             passing_grade=float(self.passing_grade)
#         )

#         # 3. Update Visibility and Passing Grade for each year component
#         for year_num, component in self.year_components.items():
#             component.setVisible(year_num <= up_to_year)
#             # Ensure the individual year bar also respects the student's passing grade
#             if hasattr(component, 'set_passing_grade'):
#                 component.set_passing_grade(self.passing_grade)

#         # 4. Update Main Stats Cards
#         # Weighted Average
#         self.media_card.findChild(QLabel, "CardValue").setText(f"{stats['weighted_avg']:.2f}")
        
#         # Credits Earned
#         self.credits_card.findChild(QLabel, "CardValue").setText(str(stats['credits']))
        
#         # Use f-string with the dynamic total_degree_credits
#         self.credits_card.findChild(QLabel, "CardSub").setText(f"out of {self.total_degree_credits} possible")
        
#         # Degree Progress
#         prog_int = int(stats['progress'])
#         self.progress_card.findChild(QLabel, "CardValue").setText(f"{prog_int}%")
#         self.main_progress_bar.setValue(prog_int)

#     def on_screen_shown(self):
#         # Triggered by Router to refresh from DB
#         self.update_dashboard(self.current_view_year)

#     def _get_logged_in_user_info(self):
#         user = Session.get_current_user() if hasattr(Session, 'get_current_user') else None
#         uni_name = "University of Bucharest"
#         major_name = "Computer Science"

#         if user and "university_id" in user:
#             try:
#                 # Use self.UNI_DATA_PATH
#                 with open(self.UNI_DATA_PATH, "r") as f:
#                     universities = json.load(f)
#                     for uni in universities:
#                         if uni["id"] == user["university_id"]:
#                             uni_name = uni["name"]
#                             break
#             except Exception:
#                 pass
#         return {"university": uni_name, "major": major_name}

#     def _handle_logout(self):
#         Session.logout() # Using Person A's method
#         self.router.navigate("login")

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt
from ui.components.collapsible_year import CollapsibleYear
from ui.styles import DASHBOARD_STYLE 
from services.dashboard_service import DashboardService
from models.session import Session
import json
import os

class DashboardScreen(QWidget):
    UNI_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "universities.json")

    def __init__(self, router):
        super().__init__()
        self.router = router
        self.current_view_year = 1
        self.all_data = {}
        self.year_buttons = []
        self.year_components = {}
        self.setStyleSheet(DASHBOARD_STYLE)
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
        self.subtitle = QLabel("Welcome")
        self.subtitle.setObjectName("HeaderSubtitle")
        
        title_container.addWidget(self.header_title)
        title_container.addWidget(self.subtitle)
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        
        # New Add Grades Button
        add_data_btn = QPushButton("+ Add Grades")
        add_data_btn.setFixedWidth(120)
        add_data_btn.setStyleSheet("background-color: #A8C686; color: #0A0D08;") 
        # add_data_btn.clicked.connect(lambda: self.router.navigate("year_setup"))
        add_data_btn.clicked.connect(lambda: self.router.navigate("subject_setup"))
        
        logout_btn = QPushButton("Log Out")
        logout_btn.setFixedWidth(100)
        logout_btn.clicked.connect(self._handle_logout)
        
        header_layout.addWidget(add_data_btn)
        header_layout.addWidget(logout_btn)
        self.main_layout.addLayout(header_layout)

        # 2. Filter Bar
        self.filter_widget = QWidget()
        self.filter_layout = QHBoxLayout(self.filter_widget)
        self.filter_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.filter_widget)

        # 3. Main Stats Cards
        stats_layout = QHBoxLayout()
        self.media_card = self._create_stat_card("WEIGHTED AVERAGE", "0.00", "all graded subjects")
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

    def on_screen_shown(self):
        """Called automatically when the router switches to this screen."""
        user_info = self._get_logged_in_user_info()
        self.passing_grade = user_info.get('passing_grade', 5.0)
        self.total_degree_credits = user_info.get('total_degree_credits', 180)
        self.subtitle.setText(f"{user_info['university']} | {user_info['major']}")

        try:
            user_id = Session.get_current_user_id()
            print(f"DEBUG: Loading dashboard for User ID: {user_id}") 
            self.all_data = DashboardService.get_user_dashboard_data(user_id)
        except Exception as e:
            print(f"ERROR: Could not load dashboard data: {e}")
            self.all_data = {}
        
        self._rebuild_dynamic_ui()
        
        if self.all_data:
            self.current_view_year = max(self.all_data.keys())
        else:
            self.current_view_year = 1
            
        self.update_dashboard(self.current_view_year)

    def _rebuild_dynamic_ui(self):
        # Clear old filters
        for i in reversed(range(self.filter_layout.count())): 
            widget = self.filter_layout.itemAt(i).widget()
            if widget: widget.deleteLater()
        self.year_buttons.clear()

        # Rebuild filters
        filter_label = QLabel("View up to:")
        filter_label.setStyleSheet("font-weight: bold; color: #555;")
        self.filter_layout.addWidget(filter_label)
        
        for year_num in sorted(self.all_data.keys()):
            btn = QPushButton(f"Year {year_num}")
            btn.setObjectName("FilterButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, y=year_num: self.update_dashboard(y))
            self.year_buttons.append(btn)
            self.filter_layout.addWidget(btn)
        self.filter_layout.addStretch()

        # Clear old years
        for i in reversed(range(self.years_container.count())): 
            widget = self.years_container.itemAt(i).widget()
            if widget: widget.deleteLater()
        self.year_components.clear()

        # Rebuild years
        for year_num, data in self.all_data.items():
            collapsible = CollapsibleYear(f"Year {year_num}")
            collapsible.set_subjects(data['subjects'], data['target_credits'])
            self.years_container.addWidget(collapsible)
            self.year_components[year_num] = collapsible

    def _create_stat_card(self, title, value, subtitle):
        card = QFrame()
        card.setObjectName("StatCard")
        layout = QVBoxLayout(card)
        t_label = QLabel(title)
        t_label.setObjectName("CardTitle")
        v_label = QLabel(value)
        v_label.setObjectName("CardValue")
        s_label = QLabel(subtitle)
        s_label.setObjectName("CardSub")
        layout.addWidget(t_label)
        layout.addWidget(v_label)
        layout.addWidget(s_label)
        return card

    def update_dashboard(self, up_to_year):
        self.current_view_year = up_to_year
        
        for btn in self.year_buttons:
            is_active = btn.text() == f"Year {up_to_year}"
            btn.setProperty("active", is_active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        stats = DashboardService.calculate_stats(
            self.all_data, 
            up_to_year, 
            total_program_credits=self.total_degree_credits,
            passing_grade=float(self.passing_grade)
        )

        for year_num, component in self.year_components.items():
            component.setVisible(year_num <= up_to_year)
            if hasattr(component, 'set_passing_grade'):
                component.set_passing_grade(self.passing_grade)

        self.media_card.findChild(QLabel, "CardValue").setText(f"{stats['weighted_avg']:.2f}")
        self.credits_card.findChild(QLabel, "CardValue").setText(str(stats['credits']))
        self.credits_card.findChild(QLabel, "CardSub").setText(f"out of {self.total_degree_credits} possible")
        
        prog_int = int(stats['progress'])
        self.progress_card.findChild(QLabel, "CardValue").setText(f"{prog_int}%")
        self.main_progress_bar.setValue(prog_int)

    def _get_logged_in_user_info(self):
        try:
            user = Session.get_user()
        except RuntimeError:
            user = None
        
        uni_name = "University of Bucharest"
        major_name = "Computer Science"
        
        if user and "university_id" in user:
            try:
                with open(self.UNI_DATA_PATH, "r") as f:
                    universities = json.load(f)
                    for uni in universities:
                        if uni["id"] == user["university_id"]:
                            uni_name = uni["name"]
                            break
            except Exception:
                pass
        return {"university": uni_name, "major": major_name, "passing_grade": 5.0, "total_degree_credits": 180}

    def _handle_logout(self):
        Session.logout()
        self.router.navigate("login")