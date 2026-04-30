import sys
from PyQt6.QtWidgets import QApplication, QStackedWidget, QMainWindow

class AppRouter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grade Tracker")
        self.resize(900, 650)
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