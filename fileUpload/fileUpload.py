"""
Filename:       fileUpload.py
Version:        1.1
Authors:        Jason Huang, ECE4574_F25_Team8
Description:    This file deals with uploading cvs bank statements to python data structures.
"""

import csv
from enum import Enum

# Try to import tkinter, fallback to PyQt6 if not available
try:
    import tkinter as tk
    from tkinter import filedialog
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False
    try:
        from PyQt6.QtWidgets import QFileDialog, QApplication
    except ImportError:
        QFileDialog = None
        QApplication = None

class Banks(Enum):
    # TODO: Add more bank types if needed
    WELLS_FARGO = 1
    CHASE       = 2

def get_filename() -> str:
    """
    Get the filename through a GUI prompt (tkinter or PyQt6).
    Does not check for invalid filetypes.
    """
    if HAS_TKINTER:
        filename = filedialog.askopenfilename()
    else:
        # Fallback to PyQt6 - don't create new app instance if one exists
        filename, _ = QFileDialog.getOpenFileName(
            None,
            "Select CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
    
    print(filename)
    return filename

def is_valid_file(filename: str) -> bool:
    """
    Determines if the filename/path is valid
    Gives a terminal error message and returns None on invalid filetypes/filepaths
    """
    if filename == "":
        print("No valid filetype or filepath specified.")
        return False
    
    if not filename.lower().endswith(".csv"):
        print("Incorrect filetype specified.")
        return False
    
    return True

def upload_statement(filename: str, bank: Banks = Banks.WELLS_FARGO) -> list:
    """
    Takes in a bank statement and converts it into a list of dicts (transactions)
    """
    print(f"upload_statement called with filename: {filename}, bank: {bank}")

    # Returns None if no filetype/filepath was specified or is invalid
    if not is_valid_file(filename):
        print("File validation failed")
        return None
    
    print("File validation passed, starting to read CSV...")
    transaction_list = []

    try:
        with open(filename, "r") as csv_file:
            print(f"File opened successfully, bank type: {bank}")
            if bank == Banks.WELLS_FARGO:
                WF_cols = ["Date", "Amount", "[FILLER1]", "[FILLER2]", "Description"] # CSV format for Wells Fargo bank statements
                print("Processing Wells Fargo format...")
                for i, transaction in enumerate(csv.DictReader(csv_file, fieldnames = WF_cols)):
                    transaction_list.append(transaction)
                    if i % 100 == 0:  # Print progress every 100 rows
                        print(f"Processed {i} rows...")
            
            elif bank == Banks.CHASE:
                print("Processing Chase format...")
                for i, transaction in enumerate(csv.DictReader(csv_file)): # Chase CSV Statements already provide column headers
                    transaction_list.append(transaction)
                    if i % 100 == 0:  # Print progress every 100 rows
                        print(f"Processed {i} rows...")
        
        print(f"CSV processing completed. Total rows: {len(transaction_list)}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

    return transaction_list

def print_statement(transaction_list: list) -> None:
    """
    Prints out the transaction list
    """
    for transaction in transaction_list:
        print(transaction)

def main():
    """
    Main to test the file functions.
    """
    absolute_path = get_filename()
    transaction_list = upload_statement(absolute_path, Banks.CHASE)
    print_statement(transaction_list)

if __name__ == "__main__":
    main()