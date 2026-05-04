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
from ui.screens.year_setup_screen import YearSetupScreen 

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
    year_setup = YearSetupScreen(router) 

    # Routes
    router.register("login", login)
    router.register("signup", signup)
    router.register("dashboard", dashboard)
    router.register("year_setup", year_setup) 

    # Initial View
    router.navigate("login")
    
    router.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()