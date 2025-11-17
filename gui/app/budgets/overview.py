"""
Overview Tab Component
Personal Budget Management System – Budget Overview Analysis

Provides the overview tab with key metrics and insights.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox
)
from typing import List
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

from core.models import Transaction
from core.analytics.spending import calculate_total_spending, get_top_spending_categories
from core.analytics.income import calculate_total_income, calculate_net_balance
from core.analytics.months import filter_transactions_by_month
from gui.widgets.month_filter import MonthFilter
from gui.widgets.metric_card import MetricCard
from gui.app.style import Styles


class OverviewTab(QWidget):
    """Overview tab with key metrics and insights."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.transactions: List[Transaction] = []
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Month filter
        self.month_filter = MonthFilter()
        self.month_filter.filter_changed.connect(self._on_filter_changed)
        layout.addWidget(self.month_filter)
        
        # Key metrics
        metrics_layout = QHBoxLayout()
        
        # Create metric cards
        self.spending_card = MetricCard("Total Spending", "$0.00", "danger")
        self.income_card = MetricCard("Total Income", "$0.00", "success")
        self.net_card = MetricCard("Net Balance", "$0.00", "info")
        self.count_card = MetricCard("Transactions", "0", "purple")
        
        metrics_layout.addWidget(self.spending_card)
        metrics_layout.addWidget(self.income_card)
        metrics_layout.addWidget(self.net_card)
        metrics_layout.addWidget(self.count_card)
        
        layout.addLayout(metrics_layout)
        
        # Recent insights
        insights_group = QGroupBox("Recent Insights")
        insights_group.setStyleSheet(Styles.GROUPBOX)
        
        self.insights_label = QLabel("No insights available. Upload transactions to see analysis.")
        self.insights_label.setWordWrap(True)
        self.insights_label.setStyleSheet(Styles.LABEL_SECONDARY)
        
        insights_layout = QVBoxLayout()
        insights_layout.addWidget(self.insights_label)
        insights_group.setLayout(insights_layout)
        layout.addWidget(insights_group)
    
    def set_transactions(self, transactions: List[Transaction]):
        """Update transactions and refresh display."""
        self.transactions = transactions
        self.month_filter.populate_from_transactions(transactions)
        self._update_display()
    
    def _on_filter_changed(self, filter_text: str):
        """Handle month filter change."""
        self._update_display()
    
    def _update_display(self):
        """Update overview metrics and insights."""
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
        
        # Calculate metrics
        total_spending = calculate_total_spending(filtered)
        total_income = calculate_total_income(filtered)
        net_balance = calculate_net_balance(filtered)
        count = len(filtered)
        
        # Update cards
        self.spending_card.set_value(f"${total_spending:.2f}")
        self.income_card.set_value(f"${total_income:.2f}")
        self.net_card.set_value(f"${net_balance:.2f}")
        self.count_card.set_value(str(count))
        
        # Generate insights
        insights = self._generate_insights(filtered)
        self.insights_label.setText(insights)
    
    def _generate_insights(self, transactions: List[Transaction]) -> str:
        """Generate insights from transaction data."""
        if not transactions:
            return "No insights available. Upload transactions to see analysis."
        
        insights = []
        
        # Most expensive category
        top_categories = get_top_spending_categories(transactions, limit=1)
        if top_categories:
            top_category, amount = top_categories[0]
            insights.append(f"Top expense category: <b>{top_category}</b> — ${amount:.2f}")
        
        # Recent spending trend
        recent_transactions = [
            t for t in transactions 
            if t.date >= datetime.now() - timedelta(days=30)
        ]
        if recent_transactions:
            recent_spending = calculate_total_spending(recent_transactions)
            insights.append(f"Last 30 days spending: ${recent_spending:.2f}")
        
        # Income vs spending
        total_spending = calculate_total_spending(transactions)
        total_income = calculate_total_income(transactions)
        if total_income > 0:
            spending_ratio = (total_spending / total_income) * 100
            insights.append(f"Spending {spending_ratio:.1f}% of income")
        
        # Transaction frequency
        if len(transactions) > 0:
            days_range = max(1, (datetime.now() - min(t.date for t in transactions)).days)
            avg_per_day = len(transactions) / days_range
            insights.append(f"Average {avg_per_day:.1f} transactions per day")
        
        return "<br>".join(insights) if insights else "Upload more transactions to see detailed insights!"
