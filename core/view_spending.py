# this file provides functions for:
# 1. Viewing spending summary in a pie graph
# 2. Viewing spending summary  in a table
# for now just returns a lsit of spendng category and $amount as well as percentage

from decimal import Decimal
from core.models import Transaction

#imports for pie chart gui
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtChart import QChart, QChartView, QPieSeries
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt

def show_pie(data: list[dict]) -> None:
    if not data:
        return
    app = QApplication(sys.argv)
    series = QPieSeries()
    for row in data:
        # label shows category + percent; value uses amount
        series.append(f"{row['category']} ({row['percent']:.2f}%)", float(row['amount']))

    chart = QChart()
    chart.addSeries(series)
    chart.setTitle("Spending Summary")

    view = QChartView(chart)
    view.setRenderHint(QPainter.Antialiasing)
    view.resize(640, 480)
    view.show()
    app.exec_()

def show_table(data: list[dict]) -> None:
    if not data:
        return
    
    # create an app, if already exists then join
    app = QApplication.instance()
    created_app = False
    if app is None:
        app = QApplication(sys.argv)
        created_app = True

    # setting up table
    rows = len(data)
    cols = 3
    table = QTableWidget(rows, cols)
    table.setHorizontalHeaderLabels(["Category", "Amount", "Percent"])

    for r, row in enumerate(data):
        # category
        cat_item = QTableWidgetItem(str(row.get("category", "")))
        cat_item.setFlags(cat_item.flags() ^ Qt.ItemIsEditable)  # make read-only
        table.setItem(r, 0, cat_item)

        # amount (Decimal) — formatted to 2 decimal places, keep sign
        amt = row.get("amount", Decimal("0.00"))
        try:
            amt_str = format(amt, ".2f")
        except Exception:
            # fallback if not Decimal
            amt_str = f"{float(amt):.2f}"

        amt_item = QTableWidgetItem(amt_str)
        amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        amt_item.setFlags(amt_item.flags() ^ Qt.ItemIsEditable)
        table.setItem(r, 1, amt_item)

        # percent (Decimal) — format and append '%'
        pct = row.get("percent", Decimal("0.00"))
        try:
            pct_str = f"{format(pct, '.2f')}%"
        except Exception:
            pct_str = f"{float(pct):.2f}%"
        pct_item = QTableWidgetItem(pct_str)
        pct_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pct_item.setFlags(pct_item.flags() ^ Qt.ItemIsEditable)
        table.setItem(r, 2, pct_item)

    # nice sizing and appearance
    header = table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.Stretch)
    header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
    header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

    table.setWindowTitle("Spending Summary — Table")
    table.resize(640, 480)
    table.show()

    if created_app:
        app.exec_()
    

# accepts a list of Transactions
# returns a list of dictionaries consisting of category, amount, and percentage 
def spending_summary(transactions) -> list[dict]:

    # loop through to calculate total amount spent
    total = Decimal("0.00")
    for t in transactions:
        if(t.amount < 0): total += t.amount
    total = total * -1

    # if no money has been spent 
    if total == 0:
        return []
    
    # total for each category
    category_totals: dict[str, Decimal] = {}
    for t in transactions:
        if(t.amount < 0): 
            category = t.category
            category_totals[category] = category_totals.get(category, Decimal("0.00")) + (t.amount * -1)

    # loop through and fill list
    graph_info = []
    for category, amount in category_totals.items():
        percent = amount / total * Decimal("100")
        graph_info.append({
            "category": category,
            "amount": amount,
            "percent": percent
        })
    
    # sorts from greatest to lowest amount
    graph_info.sort(key = lambda row: row["amount"], reverse = True)

    return graph_info

"""
def main():

    # some transactions for testing
    t0 = Transaction("id", "description", Decimal("1000"), "luxury", "notes", False)
    t1 = Transaction("id", "description", Decimal("100"), "food", "notes", False)
    t2 = Transaction("id", "description", Decimal("150"), "clothes", "notes", False)
    t3 = Transaction("id", "description", Decimal("650"), "rent", "notes", False)
    t4 = Transaction("id", "description", Decimal("50"), "food", "notes", False)
    t5 = Transaction("id", "description", Decimal("50"), "clothes", "notes", False)

    #list of Transactions
    list_of_transactions = [t0, t1, t2, t3, t4, t5]

    # create class Transaction that has all data ready for graphing
    list_of_percents = spending_summary_graph(list_of_transactions)

    for row in list_of_percents:
        print(row)

    # displays pie chart
    show_pie(list_of_percents)

if __name__ == "__main__":
    main()

"""