"""
Analytics Module
Personal Budget Management System – Financial Analytics & Calculations

This module provides all financial, summarization, and grouping logic
for the application. It replaces scattered logic from view_spending.py
and other modules.
"""

from .spending import (
    calculate_total_spending,
    calculate_spending_by_category,
    spending_summary,
    get_category_breakdown,
    get_top_spending_categories,
    get_spending_by_category_dict
)

from .income import (
    calculate_total_income,
    calculate_net_balance,
    income_summary
)

from .forecasting import (
    forecast_spending,
    forecast_next_month_spending
)

from .goals import (
    check_spending_limit,
    check_savings_goal,
    get_per_category_limits_status,
    compute_goal_streak
)

from .subscriptions import (
    get_subscription_transactions,
    calculate_subscription_totals,
    annotate_subscription_metadata
)

from .months import (
    filter_transactions,
    filter_transactions_by_month,
    group_transactions_by_month,
    get_available_months,
    get_monthly_trends,
    get_period_summary
)

# Alias for convenience (used by filter utilities)
get_month_filter_options = get_available_months

__all__ = [
    # Spending
    'calculate_total_spending',
    'calculate_spending_by_category',
    'spending_summary',
    'get_category_breakdown',
    'get_top_spending_categories',
    'get_spending_by_category_dict',
    # Income
    'calculate_total_income',
    'calculate_net_balance',
    'income_summary',
    # Forecasting
    'forecast_spending',
    'forecast_next_month_spending',
    # Goals
    'check_spending_limit',
    'check_savings_goal',
    'get_per_category_limits_status',
    'compute_goal_streak',
    # Subscriptions
    'get_subscription_transactions',
    'calculate_subscription_totals',
    'annotate_subscription_metadata',
    # Months
    'filter_transactions',
    'filter_transactions_by_month',
    'group_transactions_by_month',
    'get_available_months',
    'get_monthly_trends',
    'get_period_summary',
    'get_month_filter_options',  # Alias for get_available_months
]
