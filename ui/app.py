from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from ui.styles import DASHBOARD_STYLE


class AppRouter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UniGrade")
        self.resize(1000, 700)

        self.setStyleSheet(DASHBOARD_STYLE)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.routes = {}

    def register(self, name, widget):
        self.routes[name] = widget
        self.stacked_widget.addWidget(widget)

    def navigate(self, name):
        if name in self.routes:
            widget = self.routes[name]
            self.stacked_widget.setCurrentWidget(widget)
            # This line forces the dashboard to refresh its data from the DB!
            if hasattr(widget, "on_screen_shown"):
                widget.on_screen_shown()
        else:
            print(f"Ruta '{name}' nu este inregistrata.")
