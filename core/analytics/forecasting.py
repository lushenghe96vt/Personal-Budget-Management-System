"""
Author: Sheng Lu

Forecasting Analytics
Personal Budget Management System – Spending Forecasts

Provides functions for forecasting future spending based on historical data.
"""

from decimal import Decimal
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from core.models import Transaction
from .months import group_transactions_by_month


def forecast_spending(transactions: List[Transaction]) -> List[Dict[str, Any]]:
    """
    Generate spending forecast based on historical monthly spending.
    
    This function matches the interface from core.view_spending.forecast_spending()
    for backward compatibility.
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        List of dictionaries containing:
        - Historical months: {"month": "YYYY-MM", "spending": Decimal}
        - Forecast entry: {"forecast_next_month": Decimal}
        Sorted by month (most recent last)
    """
    # Group transactions by month
    monthly_groups = group_transactions_by_month(transactions)
    
    # Calculate spending per month
    monthly_spending = []
    for month_key in sorted(monthly_groups.keys()):
        month_transactions = monthly_groups[month_key]
        spending = sum(abs(t.amount) for t in month_transactions if t.amount < 0)
        monthly_spending.append({
            "month": month_key,
            "spending": spending
        })
    
    # Calculate forecast (simple average of last 3 months, or all if less than 3)
    forecast_value = Decimal("0.00")
    if monthly_spending:
        recent_months = monthly_spending[-3:] if len(monthly_spending) >= 3 else monthly_spending
        total = sum(m["spending"] for m in recent_months)
        forecast_value = total / len(recent_months)
    
    # Build result list
    result = monthly_spending.copy()
    result.append({"forecast_next_month": forecast_value})
    
    return result


def forecast_next_month_spending(transactions: List[Transaction], lookback_months: int = 3) -> Decimal:
    """
    Forecast next month's spending using a simple moving average.
    
    Args:
        transactions: List of Transaction objects
        lookback_months: Number of recent months to average (default: 3)
        
    Returns:
        Forecasted spending amount as Decimal
    """
    monthly_groups = group_transactions_by_month(transactions)
    
    if not monthly_groups:
        return Decimal("0.00")
    
    # Get spending for each month
    monthly_totals = []
    for month_key in sorted(monthly_groups.keys()):
        month_transactions = monthly_groups[month_key]
        spending = sum(abs(t.amount) for t in month_transactions if t.amount < 0)
        monthly_totals.append(spending)
    
    # Average the last N months
    recent = monthly_totals[-lookback_months:] if len(monthly_totals) >= lookback_months else monthly_totals
    if not recent:
        return Decimal("0.00")
    
    return sum(recent) / len(recent)
