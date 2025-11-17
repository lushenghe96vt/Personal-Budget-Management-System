"""
Goals Analytics
Personal Budget Management System – Budget Goals & Limits Tracking

Provides functions for tracking spending limits and savings goals.
"""

from decimal import Decimal
from typing import List, Dict, Optional, Any
from datetime import datetime
from collections import defaultdict

from core.models import Transaction
from .spending import calculate_total_spending
from .income import calculate_total_income, calculate_net_balance
from .months import filter_transactions_by_month, group_transactions_by_month


def check_spending_limit(
    transactions: List[Transaction],
    limit: Optional[Decimal],
    year: Optional[int] = None,
    month: Optional[int] = None
) -> Dict[str, Any]:
    """
    Check spending against monthly spending limit.
    
    Args:
        transactions: List of Transaction objects
        limit: Optional spending limit amount
        year: Optional year to filter by
        month: Optional month to filter by
        
    Returns:
        Dictionary containing:
        - 'spent': Decimal amount spent
        - 'limit': Decimal limit (or None)
        - 'remaining': Decimal remaining (or None)
        - 'used_percent': int percentage used (0-100+)
        - 'over_limit': bool whether over limit
    """
    # Filter transactions if period specified
    if year is not None and month is not None:
        filtered = filter_transactions_by_month(transactions, year=year, month=month)
    else:
        filtered = transactions
    
    spent = calculate_total_spending(filtered)
    
    if limit is None:
        return {
            "spent": spent,
            "limit": None,
            "remaining": None,
            "used_percent": 0,
            "over_limit": False
        }
    
    # Ensure limit is Decimal for type consistency
    if not isinstance(limit, Decimal):
        limit = Decimal(str(limit))
    
    remaining = limit - spent
    # Calculate percentage - don't cap it, let it show over 100% if over limit
    used_percent = int((spent / limit * Decimal("100")) if limit > 0 else 0)
    over_limit = spent > limit
    
    return {
        "spent": spent,
        "limit": limit,
        "remaining": remaining,
        "used_percent": used_percent,  # Don't cap - show actual percentage even if over 100%
        "over_limit": over_limit
    }


def check_savings_goal(
    transactions: List[Transaction],
    goal: Optional[Decimal],
    year: Optional[int] = None,
    month: Optional[int] = None
) -> Dict[str, Any]:
    """
    Check savings progress against monthly savings goal.
    
    Args:
        transactions: List of Transaction objects
        goal: Optional savings goal amount
        year: Optional year to filter by
        month: Optional month to filter by
        
    Returns:
        Dictionary containing:
        - 'saved': Decimal amount saved (net balance)
        - 'goal': Decimal goal (or None)
        - 'progress_percent': int percentage of goal achieved (0-100+)
        - 'met_goal': bool whether goal is met
    """
    # Filter transactions if period specified
    if year is not None and month is not None:
        filtered = filter_transactions_by_month(transactions, year=year, month=month)
    else:
        filtered = transactions
    
    saved = calculate_net_balance(filtered)  # Net = income - spending
    
    if goal is None:
        return {
            "saved": saved,
            "goal": None,
            "progress_percent": 0,
            "met_goal": False
        }
    
    # Ensure goal is Decimal for type consistency
    if not isinstance(goal, Decimal):
        goal = Decimal(str(goal))
    
    progress_percent = int((saved / goal * Decimal("100")) if goal > 0 else 0)
    met_goal = saved >= goal
    
    return {
        "saved": saved,
        "goal": goal,
        "progress_percent": min(progress_percent, 100),  # Cap at 100 for display
        "met_goal": met_goal
    }


def get_per_category_limits_status(
    transactions: List[Transaction],
    per_category_limits: Dict[str, Decimal],
    year: Optional[int] = None,
    month: Optional[int] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Check spending against per-category limits.
    
    Args:
        transactions: List of Transaction objects
        per_category_limits: Dictionary mapping category names to limits
        year: Optional year to filter by
        month: Optional month to filter by
        
    Returns:
        Dictionary mapping category names to status dictionaries:
        - 'limit': Decimal limit
        - 'spent': Decimal amount spent
        - 'remaining': Decimal remaining
        - 'used_percent': int percentage used (0-100+)
        - 'over_limit': bool whether over limit
    """
    # Filter transactions if period specified
    if year is not None and month is not None:
        filtered = filter_transactions_by_month(transactions, year=year, month=month)
    else:
        filtered = transactions
    
    # Calculate spending per category
    from .spending import calculate_spending_by_category
    category_spending = calculate_spending_by_category(filtered)
    
    # Build status for each category with a limit
    status = {}
    for category, limit in per_category_limits.items():
        # Ensure limit is Decimal for type consistency
        if not isinstance(limit, Decimal):
            limit = Decimal(str(limit))
        
        spent = category_spending.get(category, Decimal("0.00"))
        remaining = limit - spent
        used_percent = int((spent / limit * Decimal("100")) if limit > 0 else 0)
        over_limit = spent > limit
        
        status[category] = {
            "limit": limit,
            "spent": spent,
            "remaining": remaining,
            "used_percent": min(used_percent, 100),  # Cap at 100 for display
            "over_limit": over_limit
        }
    
    return status


def compute_goal_streak(
    transactions: List[Transaction],
    monthly_savings_goal: Optional[Decimal]
) -> int:
    """
    Compute consecutive month savings-goal streak up to current month.
    A month counts if (income - spending) >= monthly_savings_goal (if set).
    
    Args:
        transactions: List of Transaction objects
        monthly_savings_goal: Optional savings goal amount
        
    Returns:
        Number of consecutive months meeting the goal (starting from most recent)
    """
    if not monthly_savings_goal or monthly_savings_goal <= 0:
        return 0
    
    # Group transactions by month
    monthly_data = group_transactions_by_month(transactions)
    
    if not monthly_data:
        return 0
    
    # Calculate income and spending per month
    months = {}
    for month_key, month_transactions in monthly_data.items():
        income = calculate_total_income(month_transactions)
        spending = calculate_total_spending(month_transactions)
        months[month_key] = {
            "income": income,
            "spending": spending,
            "net": income - spending
        }
    
    # Sort months chronologically
    ordered = sorted(months.items())
    if not ordered:
        return 0
    
    # Start from latest month and count backwards
    streak = 0
    goal = monthly_savings_goal
    
    # Get latest month
    latest_key = ordered[-1][0]
    year, month = map(int, latest_key.split("-"))
    
    def prev_month(y: int, m: int) -> tuple:
        """Get previous month."""
        return (y - 1, 12) if m == 1 else (y, m - 1)
    
    lookup = {k: v for k, v in ordered}
    y, m = year, month
    
    while True:
        key = f"{y:04d}-{m:02d}"
        if key not in lookup:
            break
        net = lookup[key]["net"]
        if net >= goal:
            streak += 1
            y, m = prev_month(y, m)
            continue
        break
    
    return streak
