from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Personal Budget Management System — Welcome")
        self.resize(800, 600)
        label = QLabel("Welcome to Team 8's Personal Budget Management System!")
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        layout = QVBoxLayout()
        layout.addWidget(label)
        container = QWidget(); container.setLayout(layout)
        self.setCentralWidget(container)

def main():
    app = QApplication(sys.argv)
    win = MainWindow(); win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
