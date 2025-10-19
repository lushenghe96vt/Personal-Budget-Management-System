"""
Filename:       fileUpload.py
Version:        1.2
Authors:        Jason Huang, ECE4574_F25_Team8
Description:    This file deals with uploading cvs bank statements to python data structures.
"""

import csv
import tkinter as tk
from tkinter import filedialog
from enum import Enum

class Banks(Enum):
    WELLS_FARGO = 1
    CHASE       = 2
    TRUIST      = 3

def get_filename() -> str:
    """
    Get the filename through a simple TKinter GUI prompt.
    Does not check for invalid filetypes.
    """
    filename = filedialog.askopenfilename(filetypes = [("CSV Files", "*.csv")])
    return filename

def is_valid_file(filename: str) -> bool:
    """
    Determines if the filename/path is valid
    Gives a terminal error message and returns False if no file was chosen
    """
    if filename == "":
        print("No valid filetype or filepath specified.")
        return False
    
    return True

def upload_statement(filename: str, bank: Banks = Banks.WELLS_FARGO) -> list:
    """
    Takes in a bank statement and converts it into a list of dicts (transactions)
    """

    # Returns a blank list if no filetype/filepath was specified or is invalid
    if not is_valid_file(filename):
        return []
    
    transaction_list = []

    with open(filename, "r") as csv_file:
        if bank == Banks.WELLS_FARGO:
            WF_cols = ["Date", "Amount", "[FILLER1]", "[FILLER2]", "Description"] # CSV format for Wells Fargo bank statements
            for transaction in csv.DictReader(csv_file, fieldnames = WF_cols):
                transaction_list.append(transaction)
        
        elif bank == Banks.CHASE or bank == Banks.TRUIST:
            for transaction in csv.DictReader(csv_file): # Chase and Truist CSV Statements already provide column headers
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
    bank_Type = input("Enter your bank type (WF, Chase, Truist): ").lower()
    if bank_Type == "wf":
        bank_Type = Banks.WELLS_FARGO
    elif bank_Type == "chase":
        bank_Type = Banks.CHASE
    elif bank_Type == "truist":
        bank_Type = Banks.TRUIST
    else:
        return  # No valid bank type specified
    # NOTE: There's some issue with the file explorer window opening in the background in some cases.
    absolute_path = get_filename()
    transaction_list = upload_statement(absolute_path, bank_Type)
    print_statement(transaction_list)

if __name__ == "__main__":
    main()