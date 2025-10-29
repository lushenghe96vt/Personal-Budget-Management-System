"""
core/models.py
Shared data models.
Author - Luke Graham
Date - 10/6/25
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional


@dataclass
class Transaction:
    # identity
    id: str                                  # stable id (e.g., file:line or hash)

    # required core fields
    date: datetime                           # primary transaction date
    description: str                         # normalized merchant/memo for matching
    amount: Decimal                          # negative = spend, positive = income

    # optional/bank-specific details (fill when available)
    posted_date: Optional[datetime] = None   # posted date if different
    description_raw: str = ""                # original bank description
    merchant: str = ""                       # optional canonical merchant
    currency: str = "USD"                    # currency code
    txn_type: str = ""                       # e.g., "DEBIT", "CREDIT", "ACH", "CARD"
    balance: Optional[Decimal] = None        # running balance if provided

    # user/app fields
    category: str = "Uncategorized"          # set by rules or user
    notes: str = ""                          # user notes
    user_override: bool = False              # if True, don't overwrite category
    statement_month: str = ""                 # user-friendly label like "January 2025", "Month 1", etc.

    # provenance/debug
    source_name: str = ""                    # e.g., "wells-fargo"
    source_upload_id: str = ""               # link back to upload
    raw: Dict[str, Any] = field(default_factory=dict)  # original row for debugging/export
