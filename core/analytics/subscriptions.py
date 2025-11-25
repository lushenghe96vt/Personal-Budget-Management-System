"""
Subscriptions Analytics
Personal Budget Management System – Subscription Transaction Analysis

Provides functions for identifying and analyzing subscription transactions.
"""

from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict

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


def annotate_subscription_metadata(transactions: List[Transaction]) -> None:
    """
    Detect subscriptions and populate Transaction flags (is_subscription, next_due_date, etc.)
    so the UI can surface Luke's subscription fields.
    """
    if not transactions:
        return

    subs = get_subscription_transactions(transactions)
    subs_set = {id(t) for t in subs}

    # Reset flags to avoid stale values
    for txn in transactions:
        txn.is_subscription = id(txn) in subs_set
        if not txn.is_subscription:
            txn.next_due_date = None
            txn.alert_sent = False

    groups: Dict[Tuple[str, float], List[Transaction]] = defaultdict(list)
    for txn in transactions:
        if not txn.is_subscription or not getattr(txn, "date", None):
            continue
        key = _subscription_group_key(txn)
        if key:
            groups[key].append(txn)

    for txns in groups.values():
        txns.sort(key=lambda t: t.date)
        interval_days = _estimate_interval_days(txns)
        interval_type, interval_value = _map_interval(interval_days)

        for txn in txns:
            txn.renewal_interval_type = interval_type
            if interval_type == "custom_days":
                txn.custom_interval_days = interval_value
            elif interval_type == "monthly":
                txn.custom_interval_days = 30
            elif interval_type == "weekly":
                txn.custom_interval_days = 7
            elif interval_type == "annual":
                txn.custom_interval_days = 365

            if txn.date:
                next_interval = interval_value if interval_type == "custom_days" else txn.custom_interval_days
                txn.next_due_date = txn.date + timedelta(days=next_interval)


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


def _subscription_group_key(transaction: Transaction) -> Optional[Tuple[str, float]]:
    desc = (transaction.merchant or transaction.description or "").strip().lower()
    if not desc:
        return None
    amount = abs(float(transaction.amount)) if transaction.amount is not None else None
    if amount is None:
        return None
    return (desc, round(amount, 2))


def _estimate_interval_days(transactions: List[Transaction]) -> int:
    if len(transactions) < 2:
        return 30
    deltas = []
    for prev, curr in zip(transactions[:-1], transactions[1:]):
        diff = (curr.date - prev.date).days if curr.date and prev.date else None
        if diff and diff > 0:
            deltas.append(diff)
    if not deltas:
        return 30
    return int(sum(deltas) / len(deltas))


def _map_interval(days: int) -> Tuple[str, int]:
    if 25 <= days <= 35:
        return "monthly", 30
    if 6 <= days <= 8:
        return "weekly", 7
    if 350 <= days <= 380:
        return "annual", 365
    return "custom_days", max(days, 1)


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
