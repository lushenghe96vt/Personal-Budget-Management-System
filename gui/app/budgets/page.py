"""
Budget Analysis Page
Personal Budget Management System – Main Budget Analysis Controller

Main controller that orchestrates all budget analysis tabs and components.
This is the refactored version of the monolithic budgets.py.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget as QWidgetType
)
from PyQt6.QtCore import pyqtSignal
from typing import Optional

from ..models.user import User
from .overview import OverviewTab
from .categories import CategoriesTab
from .monthly import MonthlyTrendsTab
from .goals import GoalsTab
from .income_vs_spending import IncomeVsSpendingTab
from .forecast import ForecastTab
from .subscriptions import SubscriptionsTab
from ..style import Styles
from gui.widgets.components import PageHeader
from core.exportWin import save_window_dialog


class BudgetAnalysisPage(QWidget):
    """Budget analysis and spending insights page - main controller."""
    
    go_back_to_dashboard = pyqtSignal()  # Signal to go back to dashboard
    
    def __init__(self, user: User, user_manager=None):
        super().__init__()
        self.user = user
        self.user_manager = user_manager
        self._build_ui()
        
        # Update all tabs with initial data
        if self.user and self.user.transactions:
            self.update_analysis()
    
    def _build_ui(self):
        """Setup the budget analysis page UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with back button and title - use common PageHeader
        page_header = PageHeader("Budget Analysis & Insights", show_back=True)
        page_header.back_clicked.connect(self.go_back_to_dashboard.emit)
        
        # Add export button to header
        header_layout = QHBoxLayout()
        header_layout.addWidget(page_header)
        header_layout.addStretch()
        
        export_btn = QPushButton("Export Page (PNG/PDF)")
        export_btn.setStyleSheet(Styles.BUTTON_SECONDARY)
        export_btn.clicked.connect(lambda: save_window_dialog(self))
        header_layout.addWidget(export_btn)
        
        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        layout.addWidget(header_widget)
        
        # Create tab widget for different analysis views
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(Styles.TAB_WIDGET)
        
        # Create all tabs
        self.overview_tab = OverviewTab()
        self.tab_widget.addTab(self.overview_tab, "Overview")
        
        self.categories_tab = CategoriesTab()
        self.tab_widget.addTab(self.categories_tab, "Categories")
        
        self.trends_tab = MonthlyTrendsTab()
        self.tab_widget.addTab(self.trends_tab, "Monthly Trends")
        
        self.goals_tab = GoalsTab()
        self.tab_widget.addTab(self.goals_tab, "Budget Goals")
        
        self.income_vs_spending_tab = IncomeVsSpendingTab()
        self.tab_widget.addTab(self.income_vs_spending_tab, "Income vs Spending")
        
        self.forecast_tab = ForecastTab()
        self.tab_widget.addTab(self.forecast_tab, "Forecast")
        
        self.subscriptions_tab = SubscriptionsTab()
        self.tab_widget.addTab(self.subscriptions_tab, "Subscriptions")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def update_analysis(self):
        """Update all tabs with current user transactions."""
        if not self.user or not self.user.transactions:
            return
        
        if self.user_manager:
            try:
                self.user_manager.recompute_goal_streak(self.user.username)
                self.user = self.user_manager.get_user(self.user.username) or self.user
            except Exception:
                pass
        
        transactions = self.user.transactions
        
        # Update all tabs
        self.overview_tab.set_transactions(transactions)
        self.categories_tab.set_transactions(transactions)
        self.trends_tab.set_transactions(transactions)
        self.goals_tab.set_user_and_transactions(self.user, transactions)
        self.income_vs_spending_tab.set_transactions(transactions)
        self.forecast_tab.set_transactions(transactions)
        self.subscriptions_tab.set_transactions(transactions)
    
    def set_user(self, user: User) -> None:
        """Update the current user and refresh all tabs."""
        self.user = user
        self.update_analysis()

