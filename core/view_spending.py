# ===============================================================
# File Name:       view_spending.py
# Author:          Sheng Lu
# Created:         10/03/2025
# Last Modified:   10/24/2025
# ===============================================================
# Description: contains functons to generate spending summary 
# data and display it in pie chart or table format.
#
# Usage:
# - call spendnig_summary() to generate a list of dictionaries containing category, amount, and percentage
# - call show_pie(spendnig_summary()) or show_table(spending_summary) to display the data in pie chart or table format respectively.
# - call income_summary() to generate a list of dictionaries containing the total spendings vs. total income. Income and spending is 
#   returned as a categroy so show_pie and show_table can be used to display it.

# Notes:
# - show_pie and show_table subject to change when finally integrated with rest of GUI
# - For forecast_spending(), we should probably add a panel somewhere to notify how many previous statements are needed before a forecast is made
#   also we could switch algorithm to linear regression
#
# ===============================================================

from decimal import Decimal
from core.models import Transaction
from datetime import datetime

#imports for chart guis
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QLineSeries, QValueAxis, QScatterSeries, QCategoryAxis
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt

# ===============================================================
# Function: show_pie
# Description: displays a pie chart based on provided data list.
# each row in the list is a dictionary containing: "category", 
# "amount", and "percent".
#
# Parameters:
# data - list of dictionaries
#
# Returns:
# None
# ===============================================================

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
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    view.resize(640, 480)
    view.show()
    app.exec()


# ===============================================================
# Function: show_table
# Description: displays the data list in a table format using
# PyQt5. each row corresponds to a category with amount and percent.
#
# Parameters: 
# data - list of dictionaries containing "category", "amount", and "percent"
#
# Returns:
# None
# ===============================================================

def show_table(data: list[dict]) -> None:

    if not data:
        return

    app = QApplication.instance() # create an app, if already exists then join
    created_app = False
    if app is None:
        app = QApplication(sys.argv)
        created_app = True

    rows = len(data) # setting up table
    cols = 3
    table = QTableWidget(rows, cols)
    table.setHorizontalHeaderLabels(["Category", "Amount", "Percent"])

    for r, row in enumerate(data):
        # category
        cat_item = QTableWidgetItem(str(row.get("category", "")))
        cat_item.setFlags(cat_item.flags() ^ Qt.ItemIsEditable)  # make read-only
        table.setItem(r, 0, cat_item)

        amt = row.get("amount", Decimal("0.00")) # number amount (left column)
        try:
            amt_str = format(amt, ".2f")
        except Exception:
            # fallback if not Decimal
            amt_str = f"{float(amt):.2f}"

        amt_item = QTableWidgetItem(amt_str)
        amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        amt_item.setFlags(amt_item.flags() ^ Qt.ItemIsEditable)
        table.setItem(r, 1, amt_item)

        pct = row.get("percent", Decimal("0.00")) # decimial amount (right column)
        try:
            pct_str = f"{format(pct, '.2f')}%"
        except Exception:
            pct_str = f"{float(pct):.2f}%"
        pct_item = QTableWidgetItem(pct_str)
        pct_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        pct_item.setFlags(pct_item.flags() ^ Qt.ItemIsEditable)
        table.setItem(r, 2, pct_item)

    # nice sizing and appearance
    header = table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
    header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
    header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

    table.setWindowTitle("Spending Summary — Table")
    table.resize(640, 480)
    table.show()

    if created_app:
        app.exec()
    
# ===============================================================
# Function: spending_summary
# Description: generates a list of dictionaries containing category,
# total spending amount, and its percentage of total spending. only 
# negative (spending) transactions are included.
#
# Parameters:
# transactions - list of Transaction objects
#
# Returns:
# list of dictionaries with keys: category, amount, percent
# ===============================================================

def spending_summary(transactions) -> list[dict]:
    
    total = Decimal("0.00")
    for t in transactions: # loop through to calculate total amount spent
        if(t.amount < 0): total += t.amount
    total = total * -1

    if total == 0: # no money spend, return
        return []
    
    category_totals: dict[str, Decimal] = {} # total for each category
    for t in transactions:
        if(t.amount < 0): 
            category = t.category
            category_totals[category] = category_totals.get(category, Decimal("0.00")) + (t.amount * -1)
    
    graph_info = []
    for category, amount in category_totals.items(): # loop through and fill list
        percent = amount / total * Decimal("100")
        graph_info.append({
            "category": category,
            "amount": amount,
            "percent": percent
        })
    
    # sorts from greatest to lowest amount
    graph_info.sort(key = lambda row: row["amount"], reverse = True)

    return graph_info

# ===============================================================
# Function: income_summary
# Description: generates a list of dictionaries containing total 
# income and total spendings as two categories. the data format
# matches that of spending_summary() so that show_pie() and
# show_table() can be used to display it.
#
# Parameters:
# transactions - list of Transaction objects
#
# Returns:
# list of dictionaries with keys: category, amount, percent
# ===============================================================

def income_summary(transactions) -> list[dict]:

    total_income = Decimal("0.00")
    total_spending = Decimal("0.00")
    for t in transactions: # separate income and spending
        if(t.amount > 0):
            total_income += t.amount
        elif(t.amount < 0):
            total_spending += (t.amount * -1)

    if(total_income == 0 and total_spending == 0): # cut off early if no data
        return []

    combined_total = total_income + total_spending
    if(combined_total == 0):
        return []

    graph_info = [] # build return lst
    if(total_income > 0):
        percent_income = (total_income / combined_total) * Decimal("100")
        graph_info.append({
            "category": "Income",
            "amount": total_income,
            "percent": percent_income
        })

    if(total_spending > 0):
        percent_spending = (total_spending / combined_total) * Decimal("100")
        graph_info.append({
            "category": "Spending",
            "amount": total_spending,
            "percent": percent_spending
        })

    # sorts from greatest to lowest amount
    graph_info.sort(key = lambda row: row["amount"], reverse = True)

    return graph_info

# ===============================================================
# Function: forecast_spending
# Description: Estimates next month's spending based on previous
# months total spending amounts. Uses a weighted average where more
# recent months have greater weight.
#
# Parameters:
# transactions - list of Transaction objects
#
# Returns:
# list of dictionary containing each past month's total spending 
# and a forecast for next month for plotting.
# ===============================================================

def forecast_spending(transactions) -> list[dict]:
    monthly_totals = {}

    # loop through all transactions
    for t in transactions:

        # skip invalid or income transactions
        if not hasattr(t, "date"):
            continue
        if not isinstance(t.date, datetime):
            continue
        if t.amount >= 0:
            continue

        # format key "YYYY-MM"
        year = t.date.year
        month = t.date.month
        key = f"{year}-{month:02d}"

        # manually handle missing keys
        if key not in monthly_totals:
            monthly_totals[key] = Decimal("0.00")

        # accumulate spending (make positive)
        monthly_totals[key] += (t.amount * -1)

    # handle case: no valid spending
    if len(monthly_totals) == 0:
        result = []
        result.append({"forecast_next_month": Decimal("0.00")})
        return result

    # sort the months chronologically
    sorted_months = sorted(monthly_totals.keys())

    # compute weighted average manually
    total_weight = Decimal("0.00")
    weighted_sum = Decimal("0.00")
    count = 1
    for month in sorted_months:
        weight = Decimal(count)
        weighted_sum += monthly_totals[month] * weight
        total_weight += weight
        count += 1

    if total_weight == 0:
        forecast_value = Decimal("0.00")
    else:
        forecast_value = weighted_sum / total_weight

    # build output list
    result = []
    for month in sorted_months:
        row = {
            "month": month,
            "spending": monthly_totals[month]
        }
        result.append(row)

    forecast_row = {"forecast_next_month": forecast_value.quantize(Decimal("0.01"))}
    result.append(forecast_row)

    return result

# ===============================================================
# Function: show_forecast
# Description: displays a line graph of monthly total spending 
# and highlights the predicted next month's forecast in yellow. 
# previous months are shown in blue.
#
# Parameters:
# forecast_data - list of dictionaries returned from 
# forecast_spending(). example entry:
#   {"month": "YYYY-MM", "spending": Decimal()}
#   {"forecast_next_month": Decimal()}
#
# Returns:
# None
# ===============================================================

def show_forecast(forecast_data: list[dict]) -> None:

    if not forecast_data:
        return
    
    months = []  # separate historical months and forecast value
    values = []
    forecast_value = Decimal("0.00")

    for row in forecast_data:
        if "forecast_next_month" in row:
            forecast_value = row["forecast_next_month"]
        elif "month" in row and "spending" in row:
            months.append(row["month"])
            values.append(float(row["spending"]))

    if len(months) == 0:  # if no historical data
        return
    
    app = QApplication.instance()  # create an app if not already running
    created_app = False
    if app is None:
        app = QApplication(sys.argv)
        created_app = True

    line_series = QLineSeries()  # line for past data
    for i, val in enumerate(values):
        line_series.append(i, val)
    line_series.append(len(values), float(forecast_value))  # connect forecast

    scatter_actual = QScatterSeries()  # blue points for actual spending
    scatter_actual.setName("Previous Spending")
    scatter_actual.setMarkerShape(QScatterSeries.MarkerShape.MarkerShapeCircle)
    scatter_actual.setColor(QColor("blue"))
    scatter_actual.setBorderColor(QColor("blue"))
    scatter_actual.setMarkerSize(10)
    for i, val in enumerate(values):
        scatter_actual.append(i, val)

    scatter_forecast = QScatterSeries()  # yellow point for forecast
    scatter_forecast.setName("Forecast For Next Month")
    scatter_forecast.setMarkerShape(QScatterSeries.MarkerShape.MarkerShapeCircle)
    scatter_forecast.setColor(QColor("yellow"))
    scatter_forecast.setBorderColor(QColor("orange"))
    scatter_forecast.setMarkerSize(12)
    scatter_forecast.append(len(values), float(forecast_value))

    chart = QChart()  # chart setup
    chart.addSeries(line_series)
    chart.legend().markers(line_series)[0].setVisible(False) # hide legend for line
    chart.addSeries(scatter_actual)
    chart.addSeries(scatter_forecast)
    chart.setTitle("Monthly Spending Forecast")
    axis_x = QCategoryAxis()  # x axis setup (string labels)
    axis_x.setTitleText("Month")
    for i, month in enumerate(months):
        axis_x.append(month, i)
    axis_x.append("Forecast", len(values))
    # In PyQt6, default labels position is sufficient for category axis; explicit
    # setLabelsPosition call (used in PyQt5) is not needed and causes errors.
    chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)

    axis_y = QValueAxis()  # y axis setup
    axis_y.setTitleText("Spending ($)")
    y_min = min(values + [float(forecast_value)]) * 0.9  # pad range
    y_max = max(values + [float(forecast_value)]) * 1.1
    axis_y.setRange(y_min, y_max)
    chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
 
    line_series.attachAxis(axis_x)  # attach all series to both axes
    line_series.attachAxis(axis_y)
    scatter_actual.attachAxis(axis_x)
    scatter_actual.attachAxis(axis_y)
    scatter_forecast.attachAxis(axis_x)
    scatter_forecast.attachAxis(axis_y)
    
    view = QChartView(chart)  # finalize chart
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    view.resize(800, 480)
    view.show()

    if created_app:
        app.exec()

def main():

    # create some transactions with correct field order
    t0 = Transaction(id="t0", date=datetime.now(), description="salary", amount=Decimal("1000.00"), category="Income",)
    t1 = Transaction(id="t1", date=datetime.now(), description="food", amount=Decimal("-100.00"), category="Food")
    t2 = Transaction(id="t2", date=datetime.now(), description="clothes", amount=Decimal("-150.00"), category="Clothes")
    t3 = Transaction(id="t3", date=datetime.now(), description="rent", amount=Decimal("-650.00"), category="Rent")
    t4 = Transaction(id="t1", date=datetime(2025, 6, 5), description="Rent", amount=Decimal("-1000"), category="Rent")
    t5 = Transaction(id="t2", date=datetime(2025, 6, 10), description="Food", amount=Decimal("-200"), category="Food")
    t6 = Transaction(id="t3", date=datetime(2025, 8, 10), description="Rent", amount=Decimal("-1000"), category="Rent")
    t7 = Transaction(id="t4", date=datetime(2025, 8, 20), description="Groceries", amount=Decimal("-150"), category="Food")
    t8 = Transaction(id="t5", date=datetime(2025, 9, 5), description="Rent", amount=Decimal("-1000"), category="Rent")
    t9 = Transaction(id="t6", date=datetime(2025, 9, 12), description="Gas", amount=Decimal("-100"), category="Gas")

    #list of Transactions
    list_of_transactions = [t0, t1, t2, t3 ,t4, t5, t6, t7, t8, t9]

    # create list of percents for the pie chart and table
    spending = spending_summary(list_of_transactions)
    for row in spending:
        print(row)

    # displays pie chart
    show_pie(spending)

    # display table
    show_table(spending)

    #create income vs. spending summary
    spending_vs_income = income_summary(list_of_transactions)
    for row in spending_vs_income:
        print(row)

    #display pie chart
    show_pie(spending_vs_income)

    #display table 
    show_table(spending_vs_income)

    #display forecasted spending
    next_month = forecast_spending(list_of_transactions)
    for row in next_month:
        print(row)

    show_forecast(next_month)

if __name__ == "__main__":
    main()