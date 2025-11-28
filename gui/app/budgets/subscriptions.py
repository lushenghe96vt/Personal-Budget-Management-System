"""
Subscriptions Tab Component
Personal Budget Management System – Subscriptions Analysis

Provides the subscriptions tab showing subscription transactions and upcoming due dates.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QScrollArea
)
from typing import List

from core.models import Transaction
from core.analytics.subscriptions import get_subscription_transactions
from core.analytics.months import filter_transactions_by_month
from gui.widgets.month_filter import MonthFilter
from gui.app.style import Styles


class SubscriptionsTab(QWidget):
    """Subscriptions tab showing subscription transactions."""
    
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
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Subscriptions")
        title.setStyleSheet(Styles.LABEL_SECTION)
        layout.addWidget(title)
        
        # Month filter
        self.month_filter = MonthFilter()
        self.month_filter.filter_changed.connect(self._on_filter_changed)
        layout.addWidget(self.month_filter)
        
        # Subscriptions table
        self.subs_table = QTableWidget(0, 5)
        self.subs_table.setHorizontalHeaderLabels([
            "Date", "Description", "Amount", "Next Due", "Notes"
        ])
        self.subs_table.setAlternatingRowColors(True)
        self.subs_table.setStyleSheet(Styles.TABLE)
        
        header = self.subs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.subs_table)

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
        """Update subscriptions table based on current filter."""
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
        
        # Get subscription transactions
        subs = get_subscription_transactions(filtered)
        
        # Update table
        self.subs_table.setRowCount(len(subs))
        for r, t in enumerate(subs):
            self.subs_table.setItem(r, 0, QTableWidgetItem(t.date.strftime('%Y-%m-%d')))
            self.subs_table.setItem(r, 1, QTableWidgetItem(t.description))
            self.subs_table.setItem(r, 2, QTableWidgetItem(f"${abs(t.amount):.2f}"))
            
            next_due = getattr(t, 'next_due_date', None)
            self.subs_table.setItem(
                r, 3, QTableWidgetItem(next_due.strftime('%Y-%m-%d') if next_due else "-")
            )
            self.subs_table.setItem(r, 4, QTableWidgetItem(t.notes or ""))
