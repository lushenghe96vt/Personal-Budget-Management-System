"""
Author: Sheng Lu

Months Analytics
Personal Budget Management System – Month-based Filtering & Grouping

Provides functions for filtering and grouping transactions by month:
- Month-based filtering
- Transaction grouping by month
- Available months extraction
- Monthly trends calculation
"""

from typing import List, Dict, Optional, Tuple, Any
from decimal import Decimal
from datetime import datetime
from collections import defaultdict

from core.models import Transaction


def filter_transactions(
    transactions: List[Transaction],
    filter_type: Optional[str] = None,
    filter_value: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    statement_month: Optional[str] = None
) -> List[Transaction]:
    """
    Universal transaction filtering function.
    Supports filtering by date, statement month, or "All Time".
    
    This is the single source of truth for transaction filtering across the application.
    
    Args:
        transactions: List of Transaction objects to filter
        filter_type: Optional filter type ("date", "statement", or None for "All Time")
        filter_value: Optional filter value (YYYY-MM for date, statement label for statement)
        year: Optional year to filter by (alternative to filter_type/filter_value)
        month: Optional month to filter by (alternative to filter_type/filter_value)
        statement_month: Optional statement month label (alternative to filter_type/filter_value)
        
    Returns:
        Filtered list of Transaction objects
        
    Examples:
        # Filter by date using filter_type/filter_value
        filtered = filter_transactions(txns, "date", "2025-01")
        
        # Filter by statement month
        filtered = filter_transactions(txns, "statement", "Month 1")
        
        # Filter by year/month directly
        filtered = filter_transactions(txns, year=2025, month=1)
        
        # Get all transactions
        filtered = filter_transactions(txns)  # Returns all
    """
    if not transactions:
        return []
    
    # If no filter specified, return all transactions
    if filter_type is None and filter_value is None and year is None and month is None and statement_month is None:
        return transactions
    
    filtered = transactions
    
    # Handle filter_type/filter_value pattern (from month filter dropdowns)
    if filter_type == "date" and filter_value:
        try:
            year, month = map(int, filter_value.split("-"))
            filtered = [
                t for t in filtered
                if hasattr(t, "date") and isinstance(t.date, datetime)
                and t.date.year == year and t.date.month == month
            ]
        except (ValueError, AttributeError):
            pass
    elif filter_type == "statement" and filter_value:
        filtered = [
            t for t in filtered
            if hasattr(t, "statement_month") and t.statement_month == filter_value
        ]
    
    # Handle direct year/month parameters (alternative API)
    if year is not None and month is not None:
        filtered = [
            t for t in filtered
            if hasattr(t, "date") and isinstance(t.date, datetime)
            and t.date.year == year and t.date.month == month
        ]
    
    # Handle direct statement_month parameter (alternative API)
    if statement_month:
        filtered = [
            t for t in filtered
            if hasattr(t, "statement_month") and t.statement_month == statement_month
        ]
    
    return filtered


def filter_transactions_by_month(
    transactions: List[Transaction],
    year: Optional[int] = None,
    month: Optional[int] = None,
    statement_month: Optional[str] = None
) -> List[Transaction]:
    """
    Filter transactions by month criteria.
    
    DEPRECATED: Use filter_transactions() instead for consistency.
    Kept for backward compatibility.
    
    Args:
        transactions: List of Transaction objects
        year: Optional year to filter by
        month: Optional month to filter by (1-12)
        statement_month: Optional statement month label to filter by
        
    Returns:
        Filtered list of Transaction objects
    """
    return filter_transactions(transactions, year=year, month=month, statement_month=statement_month)


def group_transactions_by_month(transactions: List[Transaction]) -> Dict[str, List[Transaction]]:
    """
    Group transactions by month (YYYY-MM format).
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        Dictionary mapping month strings (YYYY-MM) to lists of transactions
    """
    monthly_groups: Dict[str, List[Transaction]] = defaultdict(list)
    
    for t in transactions:
        if not hasattr(t, "date") or not isinstance(t.date, datetime):
            continue
        
        month_key = t.date.strftime("%Y-%m")
        monthly_groups[month_key].append(t)
    
    return dict(monthly_groups)


def get_available_months(transactions: List[Transaction]) -> Dict[str, Tuple[str, Optional[str]]]:
    """
    Extract available months from transactions for filtering.
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        Dictionary mapping display names to filter info tuples:
        - Key: Display name (e.g., "January 2025" or "Statement: Month 1")
        - Value: Tuple of (filter_type, filter_value)
          - filter_type: "date" or "statement"
          - filter_value: "YYYY-MM" for date, statement label for statement
    """
    month_options: Dict[str, Tuple[str, Optional[str]]] = {"All Time": (None, None)}
    
    # Extract date-based months
    date_months = set()
    for t in transactions:
        if hasattr(t, "date") and isinstance(t.date, datetime):
            month_key = t.date.strftime("%Y-%m")
            month_name = t.date.strftime("%B %Y")
            date_months.add((month_key, month_name))
    
    # Extract statement months
    statement_months = {t.statement_month for t in transactions if t.statement_month}
    
    # Add date-based months
    sorted_date = sorted(date_months, key=lambda x: x[0], reverse=True)
    for month_key, month_name in sorted_date:
        month_options[month_name] = ("date", month_key)
    
    # Add statement-based months
    for stmt in sorted(statement_months, reverse=True):
        display = f"Statement: {stmt}"
        month_options[display] = ("statement", stmt)
    
    return month_options


def get_monthly_trends(transactions: List[Transaction]) -> List[Dict[str, Any]]:
    """
    Calculate monthly trends (income, spending, net) for all months.
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        List of dictionaries, one per month, containing:
        - 'month': str month key (YYYY-MM)
        - 'income': Decimal total income
        - 'spending': Decimal total spending
        - 'net': Decimal net balance (income - spending)
        Sorted by month descending (most recent first)
    """
    monthly_data: Dict[str, Dict[str, Decimal]] = defaultdict(
        lambda: {"income": Decimal("0"), "spending": Decimal("0")}
    )
    
    for t in transactions:
        if not hasattr(t, "date") or not isinstance(t.date, datetime):
            continue
        
        key = t.date.strftime("%Y-%m")
        if t.amount > 0:
            monthly_data[key]["income"] += t.amount
        else:
            monthly_data[key]["spending"] += abs(t.amount)
    
    # Convert to list and calculate net
    trends = []
    for month, data in sorted(monthly_data.items(), reverse=True):
        net = data["income"] - data["spending"]
        trends.append({
            "month": month,
            "income": data["income"],
            "spending": data["spending"],
            "net": net
        })
    
    return trends


def get_period_summary(
    transactions: List[Transaction],
    year: Optional[int] = None,
    month: Optional[int] = None,
    statement_month: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get summary statistics for a specific period.
    
    Args:
        transactions: List of Transaction objects
        year: Optional year to filter by
        month: Optional month to filter by
        statement_month: Optional statement month to filter by
        
    Returns:
        Dictionary containing:
        - 'period': str period description
        - 'total_income': Decimal
        - 'total_spending': Decimal
        - 'net_balance': Decimal
        - 'transaction_count': int
        - 'category_count': int
    """
    filtered = filter_transactions_by_month(transactions, year, month, statement_month)
    
    total_income = Decimal("0.00")
    total_spending = Decimal("0.00")
    categories = set()
    
    for t in filtered:
        if t.amount > 0:
            total_income += t.amount
        else:
            total_spending += abs(t.amount)
        if t.category:
            categories.add(t.category)
    
    net = total_income - total_spending
    
    # Build period description
    if statement_month:
        period = f"Statement: {statement_month}"
    elif year and month:
        period = datetime(year, month, 1).strftime("%B %Y")
    else:
        period = "All Time"
    
    return {
        "period": period,
        "total_income": total_income,
        "total_spending": total_spending,
        "net_balance": net,
        "transaction_count": len(filtered),
        "category_count": len(categories)
    }

