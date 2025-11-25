"""
Categories Tab Component
Personal Budget Management System – Category Breakdown Analysis

Provides the category breakdown tab with pie chart and detailed table.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox, QPushButton, QScrollArea
)
from PyQt6.QtCharts import QChartView
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import Qt
from typing import List, Dict
from decimal import Decimal

from core.models import Transaction
from core.analytics.spending import spending_summary, get_category_breakdown
from core.analytics.months import filter_transactions_by_month
from core.view_spending import build_pie_chart, show_pie, show_table
from gui.widgets.month_filter import MonthFilter
from gui.app.style import Styles


class CategoriesTab(QWidget):
    """Category breakdown tab with pie chart and table."""
    
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
        
        # Month filter
        self.month_filter = MonthFilter()
        self.month_filter.filter_changed.connect(self._on_filter_changed)
        layout.addWidget(self.month_filter)
        
        # Content layout (pie chart and table - 50-50 split)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Pie chart group (left side - 50%)
        chart_group = QGroupBox("Spending by Category")
        chart_group.setStyleSheet(Styles.GROUPBOX)
        
        chart_layout = QVBoxLayout()
        
        # Use Sheng's pie chart function with QChartView for embedding
        self.pie_chart_view = QChartView()
        self.pie_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Initialize with empty chart (legend on side)
        empty_chart = build_pie_chart([], "Spending by Category", show_legend_side=True)
        self.pie_chart_view.setChart(empty_chart)
        chart_layout.addWidget(self.pie_chart_view)
        
        # View Full Chart button
        view_full_btn = QPushButton("View Full Chart")
        view_full_btn.setStyleSheet(Styles.BUTTON_SECONDARY)
        view_full_btn.clicked.connect(self._open_full_chart)
        chart_layout.addWidget(view_full_btn)
        
        chart_group.setLayout(chart_layout)
        content_layout.addWidget(chart_group, 1)  # 50% width
        
        # Category table group (right side - 50%)
        table_group = QGroupBox("Category Details")
        table_group.setStyleSheet(Styles.GROUPBOX)
        
        table_layout = QVBoxLayout()
        
        self.category_table = QTableWidget()
        self.category_table.setColumnCount(3)
        self.category_table.setHorizontalHeaderLabels(["Category", "Amount", "Percentage"])
        
        header = self.category_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.category_table.setAlternatingRowColors(True)
        self.category_table.setStyleSheet(Styles.TABLE)
        table_layout.addWidget(self.category_table)
        
        # Print Table button
        print_table_btn = QPushButton("Print Table")
        print_table_btn.setStyleSheet(Styles.BUTTON_SECONDARY)
        print_table_btn.clicked.connect(self._print_table)
        table_layout.addWidget(print_table_btn)
        
        table_group.setLayout(table_layout)
        content_layout.addWidget(table_group, 1)  # 50% width
        
        layout.addLayout(content_layout)

        scroll.setWidget(content_widget)
        outer_layout.addWidget(scroll)
    
    def set_transactions(self, transactions: List[Transaction]):
        """Update transactions and refresh display."""
        self.transactions = transactions
        self.month_filter.populate_from_transactions(transactions)
        self._update_display()
    
    def _on_filter_changed(self, filter_text: str):
        """Handle month filter change."""
        self._update_display()
    
    def _update_display(self):
        """Update category breakdown based on current filter."""
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
        
        # Get spending summary using Sheng's data format
        summary_data = spending_summary(filtered)
        
        # Update pie chart using Sheng's build_pie_chart function (legend on side)
        chart = build_pie_chart(summary_data, "Spending by Category", show_legend_side=True)
        self.pie_chart_view.setChart(chart)
        
        # Update table using category breakdown for detailed info
        breakdown = get_category_breakdown(filtered)
        total_spending = sum(info["amount"] for info in breakdown.values())
        self.category_table.setRowCount(len(breakdown))
        
        for row, (category, info) in enumerate(
            sorted(breakdown.items(), key=lambda x: x[1]["amount"], reverse=True)
        ):
            self.category_table.setItem(row, 0, QTableWidgetItem(category))
            self.category_table.setItem(row, 1, QTableWidgetItem(f"${info['amount']:.2f}"))
            pct = float(info["percent"])
            self.category_table.setItem(row, 2, QTableWidgetItem(f"{pct:.1f}%"))
    
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
            
            # Get spending summary and show in dialog
            summary_data = spending_summary(filtered)
            if summary_data:
                show_pie(summary_data)
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "No Data", "No spending data available to display.")
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
            
            # Get spending summary and show in dialog
            summary_data = spending_summary(filtered)
            if summary_data:
                show_table(summary_data)
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "No Data", "No spending data available to display.")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Table Error", f"Failed to open table: {e}")
