import sys

from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication, QMessageBox

# Internal Imports
from ui.app import AppRouter
from ui.screens.dashboard_screen import DashboardScreen
from ui.screens.login_screen import LoginScreen
from ui.screens.signup_screen import SignupScreen
from ui.screens.subject_screen import SubjectScreen

load_dotenv()


def check_server_connection():
    """Verify that the API server is running"""
    try:
        import requests

        # Try accessing a public endpoint (uni list doesn't require auth)
        response = requests.get(
            "http://localhost:8000/profile/universities", timeout=2
        )
        return response.status_code == 200
    except Exception:
        # Server is likely not running
        return False


def main():
    # Check if server is running
    if not check_server_connection():
        # Create a QApplication to show the error dialog
        app = QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "Server Error",
            "Cannot connect to the API server.\n\n"
            "Make sure the FastAPI server is running:\n"
            "python server/main.py\n\n"
            "Or run: uvicorn server.main:app --reload",
        )
        sys.exit(1)

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
    router.navigate("login")

    router.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
