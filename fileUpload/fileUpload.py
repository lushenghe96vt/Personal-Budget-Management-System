"""
Filename:       fileUpload.py
Version:        1.1
Authors:        Jason Huang, ECE4574_F25_Team8
Description:    This file deals with uploading cvs bank statements to python data structures.
"""

import csv
import tkinter as tk
from tkinter import filedialog
from enum import Enum

class Banks(Enum):
    # TODO: Add more bank types if needed
    WELLS_FARGO = 1
    CHASE       = 2

def get_filename() -> str:
    """
    Get the filename through a simple TKinter GUI prompt.
    Does not check for invalid filetypes.
    """
    filename = filedialog.askopenfilename()
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

    # Returns None if no filetype/filepath was specified or is invalid
    if not is_valid_file(filename):
        return None

    transaction_list = []

    with open(filename, "r") as csv_file:
        if bank == Banks.WELLS_FARGO:
            WF_cols = ["Date", "Amount", "[FILLER1]", "[FILLER2]", "Description"] # CSV format for Wells Fargo bank statements
            for transaction in csv.DictReader(csv_file, fieldnames = WF_cols):
                transaction_list.append(transaction)

        elif bank == Banks.CHASE:
            for transaction in csv.DictReader(csv_file): # Chase CSV Statements already provide column headers
                transaction_list.append(transaction)

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