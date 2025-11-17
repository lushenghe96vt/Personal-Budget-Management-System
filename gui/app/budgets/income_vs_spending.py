"""
Income vs Spending Tab Component
Personal Budget Management System – Income vs Spending Analysis

Provides the income vs spending tab with table and pie chart visualization.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
)
from PyQt6.QtCharts import QChartView, QChart
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import Qt
from typing import List

from core.models import Transaction
from core.analytics.income import income_summary
from core.analytics.months import filter_transactions_by_month
from core.view_spending import build_pie_chart, show_pie, show_table
from gui.widgets.month_filter import MonthFilter
from gui.app.style import Styles


class IncomeVsSpendingTab(QWidget):
    """Income vs spending tab with table and pie chart."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.transactions: List[Transaction] = []
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Income vs Spending")
        title.setStyleSheet(Styles.LABEL_SECTION)
        layout.addWidget(title)
        
        # Month filter
        self.month_filter = MonthFilter()
        self.month_filter.filter_changed.connect(self._on_filter_changed)
        layout.addWidget(self.month_filter)
        
        # Content layout (pie chart and table - 50-50 split)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Pie chart group (left side - 50%)
        chart_group = QGroupBox("Income vs Spending Breakdown")
        chart_group.setStyleSheet(Styles.GROUPBOX)
        
        chart_layout = QVBoxLayout()
        
        # Use Sheng's pie chart function with QChartView for embedding
        self.pie_chart_view = QChartView()
        self.pie_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Initialize with empty chart (legend on side)
        empty_chart = build_pie_chart([], "Income vs Spending", show_legend_side=True)
        self.pie_chart_view.setChart(empty_chart)
        chart_layout.addWidget(self.pie_chart_view)
        
        # View Full Chart button
        view_full_btn = QPushButton("View Full Chart")
        view_full_btn.setStyleSheet(Styles.BUTTON_SECONDARY)
        view_full_btn.clicked.connect(self._open_full_chart)
        chart_layout.addWidget(view_full_btn)
        
        chart_group.setLayout(chart_layout)
        content_layout.addWidget(chart_group, 1)  # 50% width
        
        # Table group (right side - 50%)
        table_group = QGroupBox("Detailed Breakdown")
        table_group.setStyleSheet(Styles.GROUPBOX)
        
        table_layout = QVBoxLayout()
        
        self.ivs_table = QTableWidget(0, 3)
        self.ivs_table.setHorizontalHeaderLabels(["Category", "Amount", "Percent"])
        header = self.ivs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.ivs_table.setStyleSheet(Styles.TABLE)
        table_layout.addWidget(self.ivs_table)
        
        # Print Table button
        print_table_btn = QPushButton("Print Table")
        print_table_btn.setStyleSheet(Styles.BUTTON_SECONDARY)
        print_table_btn.clicked.connect(self._print_table)
        table_layout.addWidget(print_table_btn)
        
        table_group.setLayout(table_layout)
        content_layout.addWidget(table_group, 1)  # 50% width
        
        layout.addLayout(content_layout)
    
    def set_transactions(self, transactions: List[Transaction]):
        """Update transactions and refresh display."""
        self.transactions = transactions
        self.month_filter.populate_from_transactions(transactions)
        self._update_display()
    
    def _on_filter_changed(self, filter_text: str):
        """Handle month filter change."""
        self._update_display()
    
    def _update_display(self):
        """Update income vs spending table."""
        # Get filtered transactions
        filter_info = self.month_filter.get_filter_info()
        if filter_info is None:
            filtered = self.transactions
        else:
            filter_type, filter_value = filter_info
            if filter_type == "date":
                year, month = map(int, filter_value.split("-"))
                filtered = filter_transactions_by_month(self.transactions, year=year, month=month)
            elif filter_type == "statement":
                filtered = filter_transactions_by_month(self.transactions, statement_month=filter_value)
            else:
                filtered = self.transactions
        
        # Get income summary using Sheng's data format
        summary = income_summary(filtered)
        
        # Update pie chart using Sheng's build_pie_chart function (legend on side)
        chart = build_pie_chart(summary, "Income vs Spending", show_legend_side=True)
        self.pie_chart_view.setChart(chart)
        
        # Update table
        self.ivs_table.setRowCount(len(summary))
        for row, item in enumerate(summary):
            self.ivs_table.setItem(row, 0, QTableWidgetItem(item["category"]))
            self.ivs_table.setItem(row, 1, QTableWidgetItem(f"${item['amount']:.2f}"))
            self.ivs_table.setItem(row, 2, QTableWidgetItem(f"{item['percent']:.1f}%"))
    
    def _open_full_chart(self):
        """Open full chart in dialog using Sheng's show_pie() function."""
        try:
            # Get current filtered transactions
            filter_info = self.month_filter.get_filter_info()
            if filter_info is None:
                filtered = self.transactions
            else:
                filter_type, filter_value = filter_info
                if filter_type == "date":
                    year, month = map(int, filter_value.split("-"))
                    filtered = filter_transactions_by_month(self.transactions, year=year, month=month)
                elif filter_type == "statement":
                    filtered = filter_transactions_by_month(self.transactions, statement_month=filter_value)
                else:
                    filtered = self.transactions
            
            # Get income summary and show in dialog
            summary = income_summary(filtered)
            if summary:
                show_pie(summary)
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "No Data", "No income/spending data available to display.")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Chart Error", f"Failed to open chart: {e}")
    
    def _print_table(self):
        """Print table in separate window using Sheng's show_table() function."""
        try:
            # Get current filtered transactions
            filter_info = self.month_filter.get_filter_info()
            if filter_info is None:
                filtered = self.transactions
            else:
                filter_type, filter_value = filter_info
                if filter_type == "date":
                    year, month = map(int, filter_value.split("-"))
                    filtered = filter_transactions_by_month(self.transactions, year=year, month=month)
                elif filter_type == "statement":
                    filtered = filter_transactions_by_month(self.transactions, statement_month=filter_value)
                else:
                    filtered = self.transactions
            
            # Get income summary and show in dialog
            summary = income_summary(filtered)
            if summary:
                show_table(summary)
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "No Data", "No income/spending data available to display.")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Table Error", f"Failed to open table: {e}")
