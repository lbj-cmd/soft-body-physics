import sys
from PyQt6.QtWidgets import QApplication, QMainWindow

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Window")
        self.setGeometry(100, 100, 800, 600)

if __name__ == "__main__":
    print("Starting application...")
    app = QApplication(sys.argv)
    print("Creating window...")
    window = TestWindow()
    print("Showing window...")
    window.show()
    print("Entering event loop...")
    sys.exit(app.exec())