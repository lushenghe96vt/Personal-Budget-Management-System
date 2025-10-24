"""
Filename:       exportWin.py
Version:        1.0
Authors:        Jason Huang, ECE4574_F25_Team8
Description:    This file deals with exporting windows to pdf/png format. This is mainly for users to save their transaction summaries.
"""

from PyQt6.QtWidgets import QApplication, QPushButton, QLineEdit, QVBoxLayout, QWidget, QFileDialog
import sys

def save_window(window: QWidget) -> None:
    """
    Saves the specified QWidget.
    The user chooses the filepath through a file dialog.
    """
    # TODO: Possibly set up functionality to save as pdf as well?
    window_pic = window.grab()
    save_settings, _ = QFileDialog.getSaveFileName(None, "Save File", "", "PNG Files (*.png)")

    if save_settings:   # User did not cancel the file save
        window_pic.save(save_settings)

def main():
    """
    Demo to show window saving feature
    """
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("Save File Demo")
    window.setGeometry(500, 500, 500, 500)

    layout = QVBoxLayout()

    line_edit = QLineEdit()
    line_edit.setPlaceholderText("Enter text to be saved...")
    layout.addWidget(line_edit)

    save_button = QPushButton()
    save_button.setText("Save Window")
    save_button.pressed.connect(lambda: save_window(window))
    layout.addWidget(save_button)

    window.setLayout(layout)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
