"""
Filename:       exportWin.py
Version:        1.0
Authors:        Jason Huang, ECE4574_F25_Team8
Description:    This file deals with exporting windows to pdf/png format. This is mainly for users to save their transaction summaries.
"""

from PyQt6.QtWidgets import QApplication, QPushButton, QLineEdit, QVBoxLayout, QWidget, QFileDialog
from PyQt6.QtGui import QPixmap, QPainter, QPageSize
from PyQt6.QtPrintSupport import QPrinter
import sys

def save_window_dialog(window: QWidget) -> None:
    """
    File save dialog that opens up a windows explorer for users to choose how to save the window
    """
    filename, _ = QFileDialog.getSaveFileName(None, "Save File", "", "PNG Files (*.png);;PDF Files (*.pdf)")
    
    if filename:    # Checks to see if user did not cancel file dialog. Then chooses the save function depending on filetype
        window_pic = window.grab()
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
    print_settings = QPrinter(QPrinter.PrinterMode.HighResolution)
    print_settings.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    print_settings.setOutputFileName(filename)
    print_settings.setPageSize(QPageSize(window.size()))

    # Fixes the scaling issue where the window would be super small in the pdf
    window_size = window.size()
    x_scale = print_settings.width() / window_size.width()
    y_scale = print_settings.height() / window_size.height()

    window_pic = QPainter(print_settings)
    window_pic.scale(x_scale, y_scale)
    window_pic.drawPixmap(window.rect(), window)
    # TODO: Save sometimes asks for printer connection?? Not sure why. Fix if have time.
    window_pic.end()

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
