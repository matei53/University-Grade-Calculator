import sys
import os
from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication

# Internal Imports
from database.db import initialize_db
from ui.app import AppRouter
from ui.screens.login_screen import LoginScreen
from ui.screens.signup_screen import SignupScreen
from ui.screens.dashboard_screen import DashboardScreen
from ui.screens.subject_screen import SubjectScreen 

load_dotenv()

def main():
    initialize_db()
    app = QApplication(sys.argv)
    app.setApplicationName("UniGrade")
    router = AppRouter()

    # Screens
    login = LoginScreen(router)
    signup = SignupScreen(router)
    dashboard = DashboardScreen(router)
    subject_setup = SubjectScreen(router) 

    # Routes
    router.register("login", login)
    router.register("signup", signup)
    router.register("dashboard", dashboard)
    router.register("subject_setup", subject_setup) 

    # Initial View
    router.navigate("dashboard")
    
    router.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()