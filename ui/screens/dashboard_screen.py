from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, QProgressBar)
from PyQt6.QtCore import Qt
from ui.components.collapsible_year import CollapsibleYear
from ui.styles import DASHBOARD_STYLE
from services.dashboard_service import DashboardService
from models.session import Session
import json, os

class DashboardScreen(QWidget):
    UNI_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "universities.json")
    
    def __init__(self, router):
        super().__init__()
        self.router = router
        self.all_data = {}
        self.year_buttons = []
        self.year_components = {}
        self.setStyleSheet(DASHBOARD_STYLE)
        self._build_ui()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 20, 40, 20)
        
        # Header cu Butoane Separate
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        self.header_title = QLabel("UniGrade")
        self.header_title.setObjectName("HeaderTitle")
        self.subtitle = QLabel("Welcome")
        self.subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(self.header_title)
        title_box.addWidget(self.subtitle)
        header.addLayout(title_box)
        header.addStretch()

        # Buton Adaugă Materie Simplificat
        add_subject_btn = QPushButton("+ Adaugă Materie")
        add_subject_btn.setFixedWidth(140)
        add_subject_btn.setStyleSheet("background-color: #A8C686; font-weight: bold; border-radius: 6px; padding: 6px; color: #0A0D08;")
        add_subject_btn.clicked.connect(lambda: self.router.navigate("subject_setup"))
        
        logout_btn = QPushButton("Log Out")
        logout_btn.setFixedWidth(90)
        logout_btn.setStyleSheet("background-color: #ffffff; border: 1px solid #ccc; border-radius: 6px; padding: 6px;")
        logout_btn.clicked.connect(self._handle_logout)

        header.addWidget(add_subject_btn)
        header.addWidget(logout_btn)
        self.main_layout.addLayout(header)

        # Restul UI-ului (Filtre, Stats, Scroll)
        self.filter_layout = QHBoxLayout()
        self.main_layout.addLayout(self.filter_layout)
        
        stats_layout = QHBoxLayout()
        self.media_card = self._create_stat_card("MEDIA PONDERATĂ", "0.00")
        self.credits_card = self._create_stat_card("CREDITE", "0")
        self.progress_card = self._create_stat_card("PROGRES", "0%")
        self.main_progress_bar = QProgressBar()
        self.main_progress_bar.setFixedHeight(10)
        self.main_progress_bar.setTextVisible(False)
        self.progress_card.layout().addWidget(self.main_progress_bar)
        
        stats_layout.addWidget(self.media_card)
        stats_layout.addWidget(self.credits_card)
        stats_layout.addWidget(self.progress_card)
        self.main_layout.addLayout(stats_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.years_container = QVBoxLayout(self.scroll_content)
        self.years_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(scroll)

    def on_screen_shown(self):
        """Această metodă este apelată automat de router când te întorci pe dashboard."""
        user_info = self._get_logged_in_user_info()
        self.subtitle.setText(f"{user_info['university']} | {user_info['major']}")
        
        try:
            uid = Session.get_current_user_id()
            self.all_data = DashboardService.get_user_dashboard_data(uid)
        except Exception: 
            self.all_data = {}
            
        self._rebuild_dynamic_ui()
        
        # Dacă există date, afișăm automat cel mai mare an (ex: Anul 2 în loc de Anul 1)
        if self.all_data: 
            self.update_dashboard(max(self.all_data.keys()))

    def _rebuild_dynamic_ui(self):
        # 1. Ștergem complet și SIGUR filtrele vechi (Metoda Corectă PyQt)
        while self.filter_layout.count():
            item = self.filter_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        self.year_buttons = []
        
        # Refacem filtrele
        filter_label = QLabel("Filtrează până la:")
        filter_label.setStyleSheet("font-weight: bold; color: #555;")
        self.filter_layout.addWidget(filter_label)
        
        for y in sorted(self.all_data.keys()):
            btn = QPushButton(f"Anul {y}")
            btn.setObjectName("FilterButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda ch, yr=y: self.update_dashboard(yr))
            self.year_buttons.append(btn)
            self.filter_layout.addWidget(btn)
            
        self.filter_layout.addStretch()
        
        # 2. Ștergem complet și SIGUR componentele anilor vechi
        while self.years_container.count():
            item = self.years_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        self.year_components = {}
        
        # Refacem anii cu datele proaspăt luate din DB
        for y, data in self.all_data.items():
            comp = CollapsibleYear(f"Anul {y}")
            comp.set_subjects(data['subjects'], data['target_credits'])
            
            # Deschidem cardul automat
            comp.toggle_button.setChecked(True)
            comp._toggle()
            
            self.years_container.addWidget(comp)
            self.year_components[y] = comp

    def _create_stat_card(self, title, val):
        card = QFrame()
        card.setObjectName("StatCard")
        l = QVBoxLayout(card)
        t = QLabel(title); t.setObjectName("CardTitle")
        v = QLabel(val); v.setObjectName("CardValue")
        l.addWidget(t); l.addWidget(v)
        return card

    def update_dashboard(self, up_to_yr):
        # Actualizăm butoanele de filtru active
        for b in self.year_buttons: 
            b.setProperty("active", b.text() == f"Anul {up_to_yr}")
            b.style().unpolish(b)
            b.style().polish(b)
            
        # Calculăm mediile și progresul
        stats = DashboardService.calculate_stats(self.all_data, up_to_yr)
        
        for y, comp in self.year_components.items(): 
            comp.setVisible(y <= up_to_yr)
            
        self.media_card.findChild(QLabel, "CardValue").setText(f"{stats['weighted_avg']:.2f}")
        self.credits_card.findChild(QLabel, "CardValue").setText(str(stats['credits']))
        
        p = int(stats['progress'])
        self.progress_card.findChild(QLabel, "CardValue").setText(f"{p}%")
        self.main_progress_bar.setValue(p)

    def _get_logged_in_user_info(self):
        return {"university": "Universitatea Curentă", "major": "Specializare", "passing_grade": 5.0, "total_degree_credits": 180}

    def _handle_logout(self):
        Session.logout()
        self.router.navigate("login")