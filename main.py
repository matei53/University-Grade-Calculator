import sys
from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow

load_dotenv()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agent App")
        self.setCentralWidget(QLabel("Environment ready ✓"))
        self.resize(1280, 720)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())