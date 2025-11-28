# ===============================================================
# File Name:       view_spending.py
# Author:          Sheng Lu
# Created:         10/03/2025
# Last Modified:   11/12/2025
# ===============================================================
# Description: contains functons to generate spending summary 
# data and display it in pie chart or table format.
#
# Usage:
# - call spendnig_summary() to generate a list of dictionaries containing category, amount, and percentage
# - call show_pie(spendnig_summary()) or show_table(spending_summary) to display the data in pie chart or table format respectively.
# - call income_summary() to generate a list of dictionaries containing the total spendings vs. total income. Income and spending is 
#   returned as a categroy so show_pie and show_table can be used to display it.
# - call forecast_spenging() to generate a list of dictionaries containing each past month's total spending and a forecast for next month as the last entry

# Notes:
# - show_pie and show_table subject to change when finally integrated with rest of GUI
# - For forecast_spending(), we should probably add a panel somewhere to notify how many previous statements are needed before a forecast is made
#   also we could switch algorithm to linear regression?
#
# ===============================================================

from decimal import Decimal
from core.models import Transaction
from datetime import datetime

#imports for chart guis
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout
from PyQt6.QtCharts import (
    QChart,
    QChartView,
    QPieSeries,
    QLineSeries,
    QValueAxis,
    QScatterSeries,
    QCategoryAxis,
    QPieSlice,
)
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt

# ===============================================================
# Function: build_pie_chart
# Description: builds a pie chart QChart object based on provided data list.
# each row in the list is a dictionary containing: "category", 
# "amount", and "percent". This function returns the chart for embedding.
#
# Parameters:
# data - list of dictionaries
# title - optional chart title (default: "Spending Summary")
#
# Returns:
# QChart object ready to be embedded in a QChartView
# ===============================================================

def build_pie_chart(
    data: list[dict],
    title: str = "Spending Summary",
    show_legend_side: bool = True,
) -> QChart:
    """
    Build a pie chart QChart object from data.
    Returns the chart for embedding in UI (does not show dialog).

    Args:
        data: List of dictionaries with 'category', 'amount', 'percent' keys
        title: Chart title
        show_legend_side: If True, show legend on the right side (vertical). If False, show on top.
    """
    chart = QChart()
    chart.setTitle(title)

    if not data:
        return chart

    series = QPieSeries()
    for row in data:
        amount = float(row["amount"])
        if amount <= 0:
            continue
        label = f"{row['category']} ({row['percent']:.2f}%)"
        slice_obj = series.append(label, amount)
        slice_obj.setExploded(False)
        slice_obj.setLabelVisible(False)
        slice_obj.setPen(QColor("black"))
        slice_obj.setBorderWidth(1)

    if series.count() == 0:
        chart.setTitle(f"{title} (No spendings to display)")
        return chart

    chart.addSeries(series)

    if show_legend_side:
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
    else:
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignTop)

    markers = chart.legend().markers(series)

    def make_hover_handler(s: QPieSlice, marker):
        def _hover(hovered: bool):
            s.setExploded(hovered)
            if hovered:
                marker.setBrush(QBrush(QColor("#0078D7")))
                marker.setLabelBrush(QBrush(QColor("green")))
                marker.setPen(QPen(QColor("black")))
            else:
                marker.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                marker.setLabelBrush(QBrush(QColor("black")))
                marker.setPen(QPen(Qt.PenStyle.NoPen))

        return _hover

    for slice_obj, marker in zip(series.slices(), markers):
        slice_obj.hovered.connect(make_hover_handler(slice_obj, marker))

    return chart

# ===============================================================
# Function: build_monthly_trends_pie_chart
# Description: builds a pie chart showing spending by month from monthly trends data.
# Uses the same logic as build_pie_chart but formats data for monthly trends.
#
# Parameters:
# trends_data - list of dictionaries from get_monthly_trends() with keys:
#   'month', 'income', 'spending', 'net'
# title - optional chart title (default: "Monthly Spending Trends")
# show_legend_side - if True, show legend on right side (vertical)
#
# Returns:
# QChart object ready to be embedded in a QChartView
# ===============================================================

def build_monthly_trends_pie_chart(trends_data: list[dict], title: str = "Monthly Spending Trends", show_legend_side: bool = True) -> QChart:
    """
    Build a pie chart showing spending by month from monthly trends data.
    Uses Sheng's pie chart logic.
    
    Args:
        trends_data: List of dictionaries from get_monthly_trends()
        title: Chart title
        show_legend_side: If True, show legend on the right side (vertical)
        
    Returns:
        QChart object ready to be embedded
    """
    if not trends_data:
        chart = QChart()
        chart.setTitle(title)
        return chart
    
    # Calculate total spending across all months
    total_spending = sum(float(trend['spending']) for trend in trends_data)
    
    if total_spending == 0:
        chart = QChart()
        chart.setTitle(title)
        return chart
    
    # Build pie chart data in Sheng's format
    pie_data = []
    for trend in trends_data:
        spending = float(trend['spending'])
        if spending > 0:
            percent = (spending / total_spending) * 100
            pie_data.append({
                'category': trend['month'],
                'amount': spending,
                'percent': percent
            })
    
    # Use build_pie_chart with the formatted data
    return build_pie_chart(pie_data, title, show_legend_side)


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
    """
    Display a pie chart in a dialog window.
    Works both standalone and within an existing QApplication.
    """
    if not data:
        return
    
    # Get existing QApplication instance (should always exist in our app)
    app = QApplication.instance()
    if app is None:
        return  # Cannot show dialog without QApplication
    
    # Create a modal dialog to hold the chart
    dialog = QDialog()
    dialog.setWindowTitle("Spending Summary - Pie Chart")
    dialog.resize(800, 600)
    dialog.setModal(True)
    
    layout = QVBoxLayout()
    dialog.setLayout(layout)
    
    # Use build_pie_chart to create the chart
    chart = build_pie_chart(data, "Spending Summary")

    view = QChartView(chart)
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    layout.addWidget(view)
    
    # Show dialog as modal (blocks until closed)
    dialog.exec()


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
    """
    Display data in a table format using a modal dialog.
    Works both standalone and within an existing QApplication.
    """
    if not data:
        return

    # Get existing QApplication instance (should always exist in our app)
    app = QApplication.instance()
    if app is None:
        return  # Cannot show dialog without QApplication

    # Create a modal dialog to hold the table
    dialog = QDialog()
    dialog.setWindowTitle("Spending Summary - Table")
    dialog.resize(800, 600)
    dialog.setModal(True)
    
    layout = QVBoxLayout()
    dialog.setLayout(layout)

    rows = len(data)  # setting up table
    cols = 3
    table = QTableWidget(rows, cols)
    table.setHorizontalHeaderLabels(["Category", "Amount", "Percent"])

    for r, row in enumerate(data):
        # category
        cat_item = QTableWidgetItem(str(row.get("category", "")))
        # Make read-only by removing ItemIsEditable flag
        flags = cat_item.flags()
        flags &= ~Qt.ItemFlag.ItemIsEditable
        cat_item.setFlags(flags)
        table.setItem(r, 0, cat_item)

        amt = row.get("amount", Decimal("0.00"))  # number amount (left column)
        try:
            amt_str = format(amt, ".2f")
        except Exception:
            # fallback if not Decimal
            amt_str = f"{float(amt):.2f}"

        amt_item = QTableWidgetItem(amt_str)
        amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        # Make read-only by removing ItemIsEditable flag
        flags = amt_item.flags()
        flags &= ~Qt.ItemFlag.ItemIsEditable
        amt_item.setFlags(flags)
        table.setItem(r, 1, amt_item)

        pct = row.get("percent", Decimal("0.00"))  # decimal amount (right column)
        try:
            pct_str = f"{format(pct, '.2f')}%"
        except Exception:
            pct_str = f"{float(pct):.2f}%"
        pct_item = QTableWidgetItem(pct_str)
        pct_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        # Make read-only by removing ItemIsEditable flag
        flags = pct_item.flags()
        flags &= ~Qt.ItemFlag.ItemIsEditable
        pct_item.setFlags(flags)
        table.setItem(r, 2, pct_item)

    # nice sizing and appearance
    header = table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
    header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
    header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

    layout.addWidget(table)
    
    # Show dialog as modal (blocks until closed)
    dialog.exec()
    
# ===============================================================
# NOTE: The following functions have been moved to core.analytics module:
# - spending_summary() -> core.analytics.spending.spending_summary()
# - income_summary() -> core.analytics.income.income_summary()
# - forecast_spending() -> core.analytics.forecasting.forecast_spending()
#
# These duplicates have been removed to avoid confusion.
# Please use the analytics module versions instead.
# ===============================================================

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
    
    # Get existing QApplication instance (should always exist in our app)
    app = QApplication.instance()
    if app is None:
        return  # Cannot show dialog without QApplication

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
    chart.legend().markers(line_series)[0].setVisible(False)  # hide legend for line
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
    
    # Create a modal dialog to hold the chart
    dialog = QDialog()
    dialog.setWindowTitle("Monthly Spending Forecast")
    dialog.resize(800, 600)
    dialog.setModal(True)
    
    layout = QVBoxLayout()
    dialog.setLayout(layout)
    
    view = QChartView(chart)  # finalize chart
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    layout.addWidget(view)
    
    # Show dialog as modal (blocks until closed)
    dialog.exec()

# NOTE: main() test function removed - use analytics module functions for data generation
# Example usage:
#   from core.analytics.spending import spending_summary
#   from core.analytics.income import income_summary
#   from core.analytics.forecasting import forecast_spending
#   from core.view_spending import show_pie, show_table, show_forecast