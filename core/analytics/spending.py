"""
Spending Analytics
Personal Budget Management System – Spending Calculations & Analysis

Provides functions for calculating and analyzing spending patterns:
- Total spending calculations
- Category-based spending breakdowns
- Spending summaries with percentages
"""

from decimal import Decimal
from typing import List, Dict, Optional
from collections import defaultdict

from core.models import Transaction


def calculate_total_spending(transactions: List[Transaction]) -> Decimal:
    """
    Calculate total spending from transactions (negative amounts).
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        Total spending as Decimal (always positive)
    """
    total = Decimal("0.00")
    for t in transactions:
        if t.amount < 0:
            total += abs(t.amount)
    return total


def calculate_spending_by_category(transactions: List[Transaction]) -> Dict[str, Decimal]:
    """
    Calculate spending totals grouped by category.
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        Dictionary mapping category names to spending totals
    """
    category_totals: Dict[str, Decimal] = defaultdict(Decimal)
    
    for t in transactions:
        if t.amount < 0:
            category = t.category or "Uncategorized"
            category_totals[category] += abs(t.amount)
    
    return dict(category_totals)


def spending_summary(transactions: List[Transaction]) -> List[Dict[str, any]]:
    """
    Generate spending summary with category, amount, and percentage.
    
    This function matches the interface from core.view_spending.spending_summary()
    for backward compatibility.
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        List of dictionaries with keys: category, amount, percent
        Sorted by amount (descending)
    """
    total = calculate_total_spending(transactions)
    
    if total == 0:
        return []
    
    category_totals = calculate_spending_by_category(transactions)
    
    graph_info = []
    for category, amount in category_totals.items():
        percent = (amount / total * Decimal("100")) if total > 0 else Decimal("0.00")
        graph_info.append({
            "category": category,
            "amount": amount,
            "percent": percent
        })
    
    # Sort from greatest to lowest amount
    graph_info.sort(key=lambda row: row["amount"], reverse=True)
    
    return graph_info


def get_category_breakdown(transactions: List[Transaction]) -> Dict[str, Dict[str, any]]:
    """
    Get detailed category breakdown with totals and percentages.
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        Dictionary with category as key, containing:
        - 'amount': Decimal total for category
        - 'percent': Decimal percentage of total spending
        - 'count': int number of transactions
    """
    total = calculate_total_spending(transactions)
    category_totals = calculate_spending_by_category(transactions)
    
    breakdown = {}
    for category, amount in category_totals.items():
        count = sum(1 for t in transactions if t.amount < 0 and (t.category or "Uncategorized") == category)
        percent = (amount / total * Decimal("100")) if total > 0 else Decimal("0.00")
        
        breakdown[category] = {
            "amount": amount,
            "percent": percent,
            "count": count
        }
    
    return breakdown


def get_top_spending_categories(transactions: List[Transaction], limit: int = 5) -> List[tuple]:
    """
    Get top N spending categories by amount.
    
    Args:
        transactions: List of Transaction objects
        limit: Number of top categories to return
        
    Returns:
        List of tuples (category, amount) sorted by amount descending
    """
    category_totals = calculate_spending_by_category(transactions)
    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    return sorted_categories[:limit]


def get_spending_by_category_dict(transactions: List[Transaction]) -> Dict[str, float]:
    """
    Get spending totals by category as a dictionary with float values.
    
    This function matches the interface from UserManager.get_spending_by_category()
    for backward compatibility.
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        Dictionary mapping category names to spending totals (as float)
    """
    category_totals = calculate_spending_by_category(transactions)
    return {cat: float(amount) for cat, amount in category_totals.items()}

