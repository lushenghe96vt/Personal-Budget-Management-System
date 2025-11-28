"""
Forecast Tab Component
Personal Budget Management System – Spending Forecast Analysis

Provides the forecast tab with chart and table visualization.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QPushButton, QScrollArea
)
from PyQt6.QtCharts import QChart, QChartView
from PyQt6.QtGui import QPainter
from typing import List

from core.models import Transaction
from core.analytics.forecasting import forecast_spending
from core.view_spending import show_forecast
from .charts import build_forecast_chart
from gui.app.style import Styles


class ForecastTab(QWidget):
    """Forecast tab showing spending forecast chart and table."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.transactions: List[Transaction] = []
        self._build_ui()
    
    def _build_ui(self):
        outer_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Monthly Spend Forecast")
        title.setStyleSheet(Styles.LABEL_SECTION)
        layout.addWidget(title)
        
        # Content layout (chart left, table right)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Forecast chart group (left side)
        chart_group = QGroupBox("Forecast Chart")
        chart_group.setStyleSheet(Styles.GROUPBOX)
        
        chart_layout = QVBoxLayout()
        
        self.forecast_chart_view = QChartView()
        self.forecast_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Initialize with empty chart
        empty_chart = QChart()
        empty_chart.setTitle("Monthly Spending Forecast\n(Upload transactions to see forecast)")
        self.forecast_chart_view.setChart(empty_chart)
        chart_layout.addWidget(self.forecast_chart_view)
        
        # View Full Forecast button
        view_full_btn = QPushButton("View Full Forecast")
        view_full_btn.setStyleSheet(Styles.BUTTON_SECONDARY)
        view_full_btn.clicked.connect(self._open_full_forecast)
        chart_layout.addWidget(view_full_btn)
        
        chart_group.setLayout(chart_layout)
        content_layout.addWidget(chart_group, 1)  # 50% width
        
        # Forecast data table group (right side)
        table_group = QGroupBox("Forecast Data")
        table_group.setStyleSheet(Styles.GROUPBOX)
        
        table_layout = QVBoxLayout()
        
        self.forecast_table = QTableWidget(0, 2)
        self.forecast_table.setHorizontalHeaderLabels(["Month", "Spending / Forecast ($)"])
        header = self.forecast_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.forecast_table.setStyleSheet(Styles.TABLE)
        table_layout.addWidget(self.forecast_table)
        
        # Print Table button (forecast data doesn't fit show_table format, so skip for now)
        # Forecast table has different structure (month, spending) vs (category, amount, percent)
        
        table_group.setLayout(table_layout)
        content_layout.addWidget(table_group, 1)  # 50% width
        
        layout.addLayout(content_layout)

        scroll.setWidget(content_widget)
        outer_layout.addWidget(scroll)
    
    def set_transactions(self, transactions: List[Transaction]):
        """Update transactions and refresh display."""
        self.transactions = transactions
        self._update_display()
    
    def _update_display(self):
        """Update forecast chart and table."""
        # Get forecast data
        forecast_data = forecast_spending(self.transactions)
        
        if not forecast_data:
            # Show empty chart
            empty_chart = QChart()
            empty_chart.setTitle("Monthly Spending Forecast\n(No data available)")
            self.forecast_chart_view.setChart(empty_chart)
            self.forecast_table.setRowCount(0)
            return
        
        # Build and display chart
        chart = build_forecast_chart(forecast_data)
        self.forecast_chart_view.setChart(chart)
        
        # Update table
        self.forecast_table.setRowCount(len(forecast_data))
        for row, item in enumerate(forecast_data):
            if "forecast_next_month" in item:
                self.forecast_table.setItem(row, 0, QTableWidgetItem("Forecast (Next Month)"))
                self.forecast_table.setItem(row, 1, QTableWidgetItem(f"${item['forecast_next_month']:.2f}"))
            elif "month" in item:
                self.forecast_table.setItem(row, 0, QTableWidgetItem(item["month"]))
                self.forecast_table.setItem(row, 1, QTableWidgetItem(f"${item['spending']:.2f}"))
    
    def _open_full_forecast(self):
        """Open full forecast chart in dialog using Sheng's show_forecast() function."""
        try:
            forecast_data = forecast_spending(self.transactions)
            if forecast_data:
                show_forecast(forecast_data)
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "No Data", "No forecast data available to display.")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Forecast Error", f"Failed to open forecast: {e}")
