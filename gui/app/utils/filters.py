"""
Filter Utilities
Personal Budget Management System – Unified Filtering Logic

Provides a single source of truth for transaction filtering across the application.
"""

from typing import List, Dict, Optional, Tuple
from core.models import Transaction
from core.analytics.months import get_available_months, filter_transactions_by_month


def get_month_filter_options(transactions: List[Transaction]) -> Dict[str, Tuple[Optional[str], Optional[str]]]:
    """
    Get month filter options for dropdown population.
    
    Returns:
        Dictionary mapping display names to (filter_type, filter_value) tuples
    """
    if not transactions:
        return {}
    
    return get_available_months(transactions)


def populate_month_filter(combo_widget, transactions: List[Transaction]):
    """
    Populate a QComboBox with month filter options.
    
    Args:
        combo_widget: QComboBox to populate
        transactions: List of transactions to extract months from
    """
    combo_widget.clear()
    combo_widget.addItem("All Time")
    
    if not transactions:
        return
    
    month_options = get_available_months(transactions)
    
    # Add date-based months (sorted, most recent first)
    date_months = [(k, v) for k, v in month_options.items() if v[0] == "date"]
    date_months.sort(key=lambda x: x[1][1] if x[1][1] else "", reverse=True)
    for month_name, _ in date_months:
        combo_widget.addItem(month_name)
    
    # Add statement-based months (sorted, most recent first)
    stmt_months = [(k, v) for k, v in month_options.items() if v[0] == "statement"]
    stmt_months.sort(key=lambda x: x[1][1] if x[1][1] else "", reverse=True)
    for stmt_name, _ in stmt_months:
        combo_widget.addItem(stmt_name)


def apply_month_filter(
    transactions: List[Transaction],
    filter_text: str,
    month_options: Optional[Dict[str, Tuple[Optional[str], Optional[str]]]] = None
) -> List[Transaction]:
    """
    Apply month filter to transactions.
    
    Args:
        transactions: List of transactions to filter
        filter_text: Selected filter text from dropdown
        month_options: Optional pre-computed month options (for efficiency)
        
    Returns:
        Filtered list of transactions
    """
    if filter_text == "All Time" or not transactions:
        return transactions
    
    # Get month options if not provided
    if month_options is None:
        month_options = get_available_months(transactions)
    
    filter_info = month_options.get(filter_text)
    if not filter_info:
        return transactions
    
    filter_type, filter_value = filter_info
    
    # Apply filter using analytics function
    if filter_type == "date" and filter_value:
        try:
            year, month = map(int, filter_value.split("-"))
            return filter_transactions_by_month(transactions, year=year, month=month)
        except (ValueError, AttributeError):
            return transactions
    elif filter_type == "statement" and filter_value:
        return filter_transactions_by_month(transactions, statement_month=filter_value)
    
    return transactions

