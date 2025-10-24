"""
Filename:       exportWin.py
Version:        1.0
Authors:        Jason Huang, ECE4574_F25_Team8
Description:    This file deals with exporting windows to pdf/png format. This is mainly for users to save their transaction summaries.
"""

from PyQt6.QtWidgets import QApplication, QPushButton, QLineEdit, QVBoxLayout, QWidget, QFileDialog
from PyQt6.QtGui import QPixmap
import sys

def save_window_dialog(window: QWidget) -> None:
    """
    File save dialog that opens up a windows explorer for users to choose how to save the window
    """
    window_pic = window.grab()
    filename, _ = QFileDialog.getSaveFileName(None, "Save File", "", "PNG Files (*.png);;PDF Files (*.pdf)")
    
    if filename:    # Checks to see if user did not cancel file dialog. Then chooses the save function depending on filetype
        if filename.lower().endswith(".png"):
            save_window_as_png(window_pic, filename)
        elif filename.lower().endswith(".pdf"):
            save_window_as_pdf(window_pic, filename)

def save_window_as_png(window: QPixmap, filename: str) -> None:
    """
    Saves the specified window as a png
    """
    window.save(filename, "png")

def save_window_as_pdf(window: QPixmap, filename: str) -> None:
    """
    Saves the specified window as a pdf
    """

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
    save_button.pressed.connect(lambda: save_window_dialog(window))
    layout.addWidget(save_button)

    window.setLayout(layout)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
