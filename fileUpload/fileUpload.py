"""
Filename:       fileUpload.py
Version:        1.0
Authors:        ECE4574_F25_Team8
Description:    This file deals with uploading cvs bank statements to python data structures.
"""

import csv
import tkinter as tk
from tkinter import filedialog


def get_filename() -> str:
    """
    Get the filename through a simple TKinter GUI prompt.
    Does not check for invalid filetypes.
    """
    filename = filedialog.askopenfilename()
    print(filename)
    return filename


def upload_statement(filename: str) -> list:
    """
    Takes in a filename and converts it into a dict.
    Able to take in an absolute path or current directory file.
    Gives a terminal error message and returns None on invalid filetypes/filepaths
    """
    transaction_list = []
    col_names = ["Date", "Amount", "[FILLER1]", "[FILLER2]",
                 "Description"]  # CSV format for Wells Fargo bank statements

    # Returns None if no filetype/filepath was specified
    if filename == "":
        print("No valid filetype or filepath specified.")
        return None

    # Returns None if the filetype is incorrect
    if not filename.lower().endswith(".csv"):
        print("Incorrect filetype specified.")
        return None

    with open(filename, "r") as csv_file:
        for transaction in csv.DictReader(csv_file, fieldnames=col_names):
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
    transaction_list = upload_statement(absolute_path)
    print_statement(transaction_list)


if __name__ == "__main__":
    main()