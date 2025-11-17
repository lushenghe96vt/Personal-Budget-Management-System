"""
Subscriptions Analytics
Personal Budget Management System – Subscription Transaction Analysis

Provides functions for identifying and analyzing subscription transactions.
"""

from typing import List
from datetime import datetime, timedelta

from core.models import Transaction


def get_subscription_transactions(transactions: List[Transaction]) -> List[Transaction]:
    """
    Identify subscription transactions from a list of transactions.
    
    Subscriptions are identified by:
    1. Category contains "subscription" (case-insensitive)
    2. Description contains common subscription keywords
    3. Recurring pattern (same amount, same merchant, monthly)
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        List of Transaction objects identified as subscriptions
    """
    subscriptions = []
    subscription_keywords = [
        "subscription", "subscription", "recurring", "monthly",
        "netflix", "spotify", "amazon prime", "disney", "hulu",
        "gym", "membership", "premium", "pro", "plus"
    ]
    
    for t in transactions:
        # Check category
        if t.category and "subscription" in t.category.lower():
            subscriptions.append(t)
            continue
        
        # Check description
        desc_lower = (t.description or "").lower()
        if any(keyword in desc_lower for keyword in subscription_keywords):
            subscriptions.append(t)
            continue
        
        # Check for recurring pattern (same amount, same merchant, monthly)
        # This is a simple heuristic - could be enhanced
        if _is_likely_recurring(t, transactions):
            subscriptions.append(t)
    
    return subscriptions


def _is_likely_recurring(transaction: Transaction, all_transactions: List[Transaction]) -> bool:
    """
    Heuristic to identify if a transaction is likely recurring.
    
    Checks if there are similar transactions (same amount, same merchant) 
    in previous months.
    """
    if transaction.amount >= 0:  # Only spending transactions
        return False
    
    # Look for similar transactions in the past 3 months
    cutoff_date = transaction.date - timedelta(days=90)
    similar = [
        t for t in all_transactions
        if t.date >= cutoff_date
        and t.date < transaction.date
        and abs(t.amount - transaction.amount) < 0.01  # Same amount (within 1 cent)
        and t.description == transaction.description  # Same description
    ]
    
    # If we find at least one similar transaction, it's likely recurring
    return len(similar) >= 1


def calculate_subscription_totals(transactions: List[Transaction]) -> dict:
    """
    Calculate total subscription spending.
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        Dictionary containing:
        - 'total': Decimal total subscription spending
        - 'count': int number of subscription transactions
        - 'monthly_average': Decimal average monthly subscription cost
    """
    from decimal import Decimal
    
    subs = get_subscription_transactions(transactions)
    total = sum(abs(t.amount) for t in subs)
    count = len(subs)
    
    # Calculate monthly average (simple average of all subscriptions)
    monthly_avg = total / count if count > 0 else Decimal("0.00")
    
    return {
        "total": total,
        "count": count,
        "monthly_average": monthly_avg
    }
