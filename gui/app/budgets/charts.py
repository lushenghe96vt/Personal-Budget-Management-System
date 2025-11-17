"""
Charts Component
Personal Budget Management System – Forecast Chart Building

Provides functions for building forecast charts from analytics data.
"""

from PyQt6.QtCharts import (
    QChart, QChartView, QLineSeries, QScatterSeries,
    QCategoryAxis, QValueAxis
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor
from typing import List, Dict
from decimal import Decimal


def build_forecast_chart(forecast_data: List[Dict]) -> QChart:
    """
    Build a forecast chart from forecast data.
    
    Args:
        forecast_data: List of dictionaries from forecast_spending()
        
    Returns:
        QChart object ready to be displayed
    """
    months = []
    values = []
    forecast_value = Decimal("0.00")
    
    for row in forecast_data:
        if "forecast_next_month" in row:
            forecast_value = row["forecast_next_month"]
        elif "month" in row and "spending" in row:
            months.append(row["month"])
            values.append(float(row["spending"]))
    
    if len(months) == 0:
        chart = QChart()
        chart.setTitle("Monthly Spending Forecast\n(No historical data available)")
        return chart
    
    # Create line series for past data
    line_series = QLineSeries()
    for i, val in enumerate(values):
        line_series.append(i, val)
    line_series.append(len(values), float(forecast_value))
    
    # Create scatter series for actual spending (blue points)
    scatter_actual = QScatterSeries()
    scatter_actual.setName("Previous Spending")
    scatter_actual.setMarkerShape(QScatterSeries.MarkerShape.MarkerShapeCircle)
    scatter_actual.setColor(QColor("blue"))
    scatter_actual.setBorderColor(QColor("blue"))
    scatter_actual.setMarkerSize(10)
    for i, val in enumerate(values):
        scatter_actual.append(i, val)
    
    # Create scatter series for forecast (yellow point)
    scatter_forecast = QScatterSeries()
    scatter_forecast.setName("Forecast For Next Month")
    scatter_forecast.setMarkerShape(QScatterSeries.MarkerShape.MarkerShapeCircle)
    scatter_forecast.setColor(QColor("yellow"))
    scatter_forecast.setBorderColor(QColor("orange"))
    scatter_forecast.setMarkerSize(12)
    scatter_forecast.append(len(values), float(forecast_value))
    
    # Create chart
    chart = QChart()
    chart.addSeries(line_series)
    if chart.legend().markers(line_series):
        chart.legend().markers(line_series)[0].setVisible(False)
    chart.addSeries(scatter_actual)
    chart.addSeries(scatter_forecast)
    chart.setTitle("Monthly Spending Forecast")
    
    # X axis (category axis with month labels)
    axis_x = QCategoryAxis()
    axis_x.setTitleText("Month")
    for i, month in enumerate(months):
        axis_x.append(month, i)
    axis_x.append("Forecast", len(values))
    chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
    
    # Y axis (value axis for spending)
    axis_y = QValueAxis()
    axis_y.setTitleText("Spending ($)")
    y_min = min(values + [float(forecast_value)]) * 0.9
    y_max = max(values + [float(forecast_value)]) * 1.1
    if y_min < 0:
        y_min = 0
    axis_y.setRange(y_min, y_max)
    chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
    
    # Attach series to axes
    line_series.attachAxis(axis_x)
    line_series.attachAxis(axis_y)
    scatter_actual.attachAxis(axis_x)
    scatter_actual.attachAxis(axis_y)
    scatter_forecast.attachAxis(axis_x)
    scatter_forecast.attachAxis(axis_y)
    
    return chart
