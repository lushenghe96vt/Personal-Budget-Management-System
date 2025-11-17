"""
Monthly Trends Tab Component
Personal Budget Management System – Monthly Trends Analysis

Provides the monthly trends tab showing income, spending, and net by month.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QPushButton
)
from PyQt6.QtCharts import QChartView
from PyQt6.QtGui import QColor, QPainter
from typing import List

from core.models import Transaction
from core.analytics.months import get_monthly_trends
from core.view_spending import build_monthly_trends_pie_chart, show_pie, show_table
from gui.app.style import Styles


class MonthlyTrendsTab(QWidget):
    """Monthly trends tab showing income, spending, and net by month."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.transactions: List[Transaction] = []
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Content layout (pie chart left, table right - 50-50 split)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Pie chart group (left side - 50%)
        chart_group = QGroupBox("Monthly Spending Trends")
        chart_group.setStyleSheet(Styles.GROUPBOX)
        
        chart_layout = QVBoxLayout()
        
        # Use Sheng's pie chart logic for monthly trends
        self.pie_chart_view = QChartView()
        self.pie_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Initialize with empty chart
        empty_chart = build_monthly_trends_pie_chart([], "Monthly Spending Trends")
        self.pie_chart_view.setChart(empty_chart)
        chart_layout.addWidget(self.pie_chart_view)
        
        # View Full Chart button
        view_full_btn = QPushButton("View Full Chart")
        view_full_btn.setStyleSheet(Styles.BUTTON_SECONDARY)
        view_full_btn.clicked.connect(self._open_full_chart)
        chart_layout.addWidget(view_full_btn)
        
        chart_group.setLayout(chart_layout)
        content_layout.addWidget(chart_group, 1)  # 50% width
        
        # Monthly trends table group (right side - 50%)
        table_group = QGroupBox("Monthly Details")
        table_group.setStyleSheet(Styles.GROUPBOX)
        
        table_layout = QVBoxLayout()
        
        self.monthly_table = QTableWidget()
        self.monthly_table.setColumnCount(4)
        self.monthly_table.setHorizontalHeaderLabels(["Month", "Income", "Spending", "Net"])
        
        header = self.monthly_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self.monthly_table.setAlternatingRowColors(True)
        self.monthly_table.setStyleSheet(Styles.TABLE)
        table_layout.addWidget(self.monthly_table)
        
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
        self._update_display()
    
    def _update_display(self):
        """Update monthly trends pie chart and table."""
        trends = get_monthly_trends(self.transactions)
        
        # Update pie chart using Sheng's logic
        chart = build_monthly_trends_pie_chart(trends, "Monthly Spending Trends", show_legend_side=True)
        self.pie_chart_view.setChart(chart)
        
        # Update table
        self.monthly_table.setRowCount(len(trends))
        
        for row, trend in enumerate(trends):
            # Month
            self.monthly_table.setItem(row, 0, QTableWidgetItem(trend["month"]))
            
            # Income
            income_item = QTableWidgetItem(f"${trend['income']:.2f}")
            income_item.setForeground(QColor("#27ae60"))
            self.monthly_table.setItem(row, 1, income_item)
            
            # Spending
            spending_item = QTableWidgetItem(f"${trend['spending']:.2f}")
            spending_item.setForeground(QColor("#e74c3c"))
            self.monthly_table.setItem(row, 2, spending_item)
            
            # Net
            net = trend["net"]
            net_item = QTableWidgetItem(f"${net:.2f}")
            net_color = QColor("#27ae60") if net >= 0 else QColor("#e74c3c")
            net_item.setForeground(net_color)
            self.monthly_table.setItem(row, 3, net_item)
    
    def _open_full_chart(self):
        """Open full chart in dialog using Sheng's show_pie() function."""
        try:
            trends = get_monthly_trends(self.transactions)
            if not trends:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "No Data", "No monthly trends data available to display.")
                return
            
            # Convert trends to pie chart format
            total_spending = sum(float(trend['spending']) for trend in trends)
            if total_spending == 0:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "No Data", "No spending data available to display.")
                return
            
            pie_data = []
            for trend in trends:
                spending = float(trend['spending'])
                if spending > 0:
                    percent = (spending / total_spending) * 100
                    pie_data.append({
                        'category': trend['month'],
                        'amount': spending,
                        'percent': percent
                    })
            
            if pie_data:
                show_pie(pie_data)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Chart Error", f"Failed to open chart: {e}")
    
    def _print_table(self):
        """Print table in separate window using Sheng's show_table() function."""
        try:
            trends = get_monthly_trends(self.transactions)
            if not trends:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "No Data", "No monthly trends data available to display.")
                return
            
            # Convert trends to table format (spending by month)
            total_spending = sum(float(trend['spending']) for trend in trends)
            if total_spending == 0:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "No Data", "No spending data available to display.")
                return
            
            table_data = []
            for trend in trends:
                spending = float(trend['spending'])
                if spending > 0:
                    percent = (spending / total_spending) * 100
                    table_data.append({
                        'category': trend['month'],
                        'amount': spending,
                        'percent': percent
                    })
            
            if table_data:
                show_table(table_data)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Table Error", f"Failed to open table: {e}")
