"""
Budgets Package
Personal Budget Management System – Budget Analysis Components

Contains refactored budget analysis components split from the monolithic budgets.py.
"""

from .page import BudgetAnalysisPage
from .overview import OverviewTab
from .categories import CategoriesTab
from .monthly import MonthlyTrendsTab
from .goals import GoalsTab
from .income_vs_spending import IncomeVsSpendingTab
from .forecast import ForecastTab
from .subscriptions import SubscriptionsTab

__all__ = [
    'BudgetAnalysisPage',
    'OverviewTab',
    'CategoriesTab',
    'MonthlyTrendsTab',
    'GoalsTab',
    'IncomeVsSpendingTab',
    'ForecastTab',
    'SubscriptionsTab',
]
