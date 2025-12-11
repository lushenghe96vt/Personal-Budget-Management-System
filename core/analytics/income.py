"""
Author: Sheng Lu

Income Analytics
Personal Budget Management System – Income Calculations & Analysis

Provides functions for calculating and analyzing income:
- Total income calculations
- Net balance calculations
- Income summaries
"""

from decimal import Decimal
from typing import List

from core.models import Transaction


def calculate_total_income(transactions: List[Transaction]) -> Decimal:
    """
    Calculate total income from transactions (positive amounts).
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        Total income as Decimal
    """
    total = Decimal("0.00")
    for t in transactions:
        if t.amount > 0:
            total += t.amount
    return total


def calculate_net_balance(transactions: List[Transaction]) -> Decimal:
    """
    Calculate net balance (income - spending).
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        Net balance as Decimal (positive = surplus, negative = deficit)
    """
    income = calculate_total_income(transactions)
    spending = sum(abs(t.amount) for t in transactions if t.amount < 0)
    return income - spending


def income_summary(transactions: List[Transaction]) -> List[dict]:
    """
    Generate income vs spending summary.
    
    This function matches the interface from core.view_spending.income_summary()
    for backward compatibility.
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        List of dictionaries with keys: category, amount, percent
        Categories are "Income" and "Spending"
    """
    total_income = calculate_total_income(transactions)
    total_spending = sum(abs(t.amount) for t in transactions if t.amount < 0)
    total = total_income + total_spending
    
    if total == 0:
        return []
    
    income_pct = (total_income / total * Decimal("100")) if total > 0 else Decimal("0.00")
    spending_pct = (total_spending / total * Decimal("100")) if total > 0 else Decimal("0.00")
    
    return [
        {"category": "Income", "amount": total_income, "percent": income_pct},
        {"category": "Spending", "amount": total_spending, "percent": spending_pct}
    ]
