import sys
from PyQt6.QtWidgets import QApplication, QStackedWidget, QMainWindow

class AppRouter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UniGrade")
        self.resize(1000, 750) # Slightly larger for breathing room
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.screens = {}

    def register(self, name: str, screen):
        self.screens[name] = screen
        self.stack.addWidget(screen)

    def navigate(self, name: str):
        screen = self.screens.get(name)
        if screen:
            self.stack.setCurrentWidget(screen)
            # CRITICAL: Tell the screen to refresh its data
            if hasattr(screen, "on_screen_shown"):
                screen.on_screen_shown()