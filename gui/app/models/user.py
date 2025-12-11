"""
user.py
Personal Budget Management System - User Model and Management
Author: Ankush
Date: 10/11/25

Description:
  User data model and manager for authentication, registration, and data persistence.
  Handles user account creation, authentication, and transaction storage.

Implements:
  - User dataclass with transaction storage
  - UserManager for user operations
  - SHA-256 password hashing
  - JSON-based data persistence
  - Transaction management (add, update, retrieve)
  - Spending analysis by category
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
import sys

# Add the project root to the path to import core modules
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.models import Transaction
from core.analytics.goals import compute_goal_streak
from core.analytics.spending import get_spending_by_category_dict
from core.analytics.months import get_monthly_trends
from core.analytics.subscriptions import annotate_subscription_metadata


@dataclass
class User:
    """User data model"""
    username: str
    email: str
    password_hash: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    transactions: List[Transaction] = field(default_factory=list)
    # Budget/goal fields
    monthly_spending_limit: Optional[float] = None  # overall cap for monthly spend
    weekly_spending_limit: Optional[float] = None   # cap for weekly spend
    monthly_savings_goal: Optional[float] = None    # target savings per month
    per_category_limits: Dict[str, float] = field(default_factory=dict)  # optional caps
    monthly_alert_threshold_pct: Optional[int] = 75  # percentage trigger for monthly alerts
    weekly_alert_threshold_pct: Optional[int] = 75   # percentage trigger for weekly alerts
    goal_streak_count: int = 0  # number of consecutive months meeting savings goal
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_login is None:
            self.last_login = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert user to dictionary for storage"""
        return {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'transactions': [self._transaction_to_dict(txn) for txn in self.transactions],
            'monthly_spending_limit': self.monthly_spending_limit,
            'weekly_spending_limit': self.weekly_spending_limit,
            'monthly_savings_goal': self.monthly_savings_goal,
            'per_category_limits': self.per_category_limits,
            'monthly_alert_threshold_pct': self.monthly_alert_threshold_pct,
            'weekly_alert_threshold_pct': self.weekly_alert_threshold_pct,
            'goal_streak_count': self.goal_streak_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Create user from dictionary"""
        user = cls(
            username=data['username'],
            email=data['email'],
            password_hash=data['password_hash'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None,
            monthly_spending_limit=data.get('monthly_spending_limit'),
            weekly_spending_limit=data.get('weekly_spending_limit'),
            monthly_savings_goal=data.get('monthly_savings_goal'),
            per_category_limits=data.get('per_category_limits', {}),
            monthly_alert_threshold_pct=data.get('monthly_alert_threshold_pct', 75),
            weekly_alert_threshold_pct=data.get('weekly_alert_threshold_pct', 75),
            goal_streak_count=int(data.get('goal_streak_count', 0)),
        )
        
        # Load transactions if they exist
        if 'transactions' in data and data['transactions']:
            user.transactions = [cls._transaction_from_dict(txn_data) for txn_data in data['transactions']]
        
        return user
    
    @staticmethod
    def _transaction_to_dict(txn: Transaction) -> dict:
        """Convert Transaction to dictionary for JSON storage"""
        return {
            'id': txn.id,
            'date': txn.date.isoformat(),
            'description': txn.description,
            'amount': str(txn.amount),
            'description_raw': txn.description_raw,
            'currency': txn.currency,
            'category': txn.category,
            'notes': txn.notes,
            'user_override': txn.user_override,
            'statement_month': txn.statement_month,
            'source_name': txn.source_name,
            'source_upload_id': txn.source_upload_id,
            'raw': txn.raw,
            'is_subscription': txn.is_subscription,
            'next_due_date': txn.next_due_date.isoformat() if txn.next_due_date else None,
            'renewal_interval_type': txn.renewal_interval_type,
            'custom_interval_days': txn.custom_interval_days,
            'alert_sent': txn.alert_sent
        }
    
    @staticmethod
    def _transaction_from_dict(data: dict) -> Transaction:
        """Create Transaction from dictionary"""
        from decimal import Decimal
        
        return Transaction(
            id=data['id'],
            date=datetime.fromisoformat(data['date']),
            description=data['description'],
            amount=Decimal(data['amount']),
            description_raw=data.get('description_raw', ''),
            merchant=data.get('merchant', ''),
            currency=data.get('currency', 'USD'),
            category=data.get('category', 'Uncategorized'),
            notes=data.get('notes', ''),
            user_override=data.get('user_override', False),
            statement_month=data.get('statement_month', ''),
            source_name=data.get('source_name', ''),
            source_upload_id=data.get('source_upload_id', ''),
            raw=data.get('raw', {}),
            is_subscription=data.get('is_subscription', False),
            next_due_date=datetime.fromisoformat(data['next_due_date']) if data.get('next_due_date') else None,
            renewal_interval_type=data.get('renewal_interval_type', 'monthly'),
            custom_interval_days=data.get('custom_interval_days', 30),
            alert_sent=data.get('alert_sent', False)
        )
    
    def average_balance_last_3_months(self):
        """Return the average NET balance over the last 3 months."""
        if not self.transactions:
            return 0.0

        trends = get_monthly_trends(self.transactions)

        if len(trends) == 0:
            return 0.0

        last = trends[-3:]
        net_values = [t["net"] for t in last]

        return float(sum(net_values) / len(net_values))

    def monthly_goal_tracker(self):
        """Return number of consecutive months meeting savings goals."""
        if not self.transactions:
            return 0

        goal = self.monthly_savings_goal
        if not goal:
            return 0

        streak = compute_goal_streak(self.transactions, goal)
        return int(streak)


class UserManager:
    """Manages user authentication and data storage"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self._ensure_data_dir()
        self._users = self._load_users()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _load_users(self) -> dict:
        """Load users from storage"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    data = json.load(f)
                    users = {username: User.from_dict(user_data) for username, user_data in data.items()}
                    for user in users.values():
                        self._refresh_subscription_metadata(user)
                    return users
            except (json.JSONDecodeError, KeyError):
                return {}
        return {}
    
    def _save_users(self):
        """Save users to storage"""
        data = {}
        for username, user in self._users.items():
            self._refresh_subscription_metadata(user)
            data[username] = user.to_dict()
        with open(self.users_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _refresh_subscription_metadata(self, user: User) -> None:
        """Ensure subscription-related flags/dates are current."""
        try:
            annotate_subscription_metadata(user.transactions)
        except Exception:
            pass
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def validate_email(self, email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_username(self, username: str) -> bool:
        """Validate username format"""
        if len(username) < 3 or len(username) > 20:
            return False
        import re
        return re.match(r'^[a-zA-Z0-9_]+$', username) is not None
    
    def validate_password(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 6:
            return False
        return True
    
    def user_exists(self, username: str) -> bool:
        """Check if user exists"""
        return username in self._users
    
    def email_exists(self, email: str) -> bool:
        """Check if email is already registered"""
        return any(user.email == email for user in self._users.values())
    
    def create_user(self, username: str, email: str, password: str, 
                   first_name: str, last_name: str, phone: str = None) -> tuple[bool, str]:
        """Create a new user"""
        # Validation
        if not self.validate_username(username):
            return False, "Username must be 3-20 characters and contain only letters, numbers, and underscores"
        
        if not self.validate_email(email):
            return False, "Please enter a valid email address"
        
        if not self.validate_password(password):
            return False, "Password must be at least 6 characters long"
        
        if self.user_exists(username):
            return False, "Username already exists"
        
        if self.email_exists(email):
            return False, "Email address already registered"
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=self._hash_password(password),
            first_name=first_name,
            last_name=last_name,
            phone=phone
        )
        
        self._users[username] = user
        self._save_users()
        return True, "Account created successfully!"
    
    def authenticate_user(self, username: str, password: str) -> tuple[bool, str, Optional[User]]:
        """Authenticate user login"""
        if not self.user_exists(username):
            return False, "Username not found", None
        
        user = self._users[username]
        if user.password_hash != self._hash_password(password):
            return False, "Invalid password", None
        
        # Update last login
        user.last_login = datetime.now()
        self._save_users()
        
        return True, "Login successful!", user
    
    def update_user(self, username: str, **kwargs) -> tuple[bool, str]:
        """Update user information"""
        if not self.user_exists(username):
            return False, "User not found"
        
        user = self._users[username]
        
        # Update allowed fields
        if 'email' in kwargs and kwargs['email'] != user.email:
            if not self.validate_email(kwargs['email']):
                return False, "Invalid email address"
            if self.email_exists(kwargs['email']):
                return False, "Email address already registered"
            user.email = kwargs['email']
        
        if 'first_name' in kwargs:
            user.first_name = kwargs['first_name']
        
        if 'last_name' in kwargs:
            user.last_name = kwargs['last_name']
        
        if 'phone' in kwargs:
            user.phone = kwargs['phone']
        
        if 'password' in kwargs:
            if not self.validate_password(kwargs['password']):
                return False, "Password must be at least 6 characters long"
            user.password_hash = self._hash_password(kwargs['password'])
        
        self._save_users()
        return True, "Profile updated successfully!"
    
    def get_user(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self._users.get(username)
    
    def add_transactions(self, username: str, transactions: List[Transaction]) -> tuple[bool, str]:
        """Add transactions to a user's account, avoiding duplicates"""
        if not self.user_exists(username):
            return False, "User not found"
        
        user = self._users[username]
        
        # Get existing transaction IDs for duplicate detection
        existing_ids = {t.id for t in user.transactions}
        existing_keys = {
            (t.date, t.amount, t.description) 
            for t in user.transactions
        }
        
        # Filter out duplicates based on ID and (date, amount, description) tuple
        new_transactions = []
        duplicates_count = 0
        
        for txn in transactions:
            # Check if transaction ID already exists
            if txn.id in existing_ids:
                duplicates_count += 1
                continue
            
            # Check if same transaction (date, amount, description) already exists
            txn_key = (txn.date, txn.amount, txn.description)
            if txn_key in existing_keys:
                duplicates_count += 1
                continue
            
            # New transaction - add it
            new_transactions.append(txn)
            existing_ids.add(txn.id)
            existing_keys.add(txn_key)
        
        # Add only new transactions
        if new_transactions:
            user.transactions.extend(new_transactions)
            # Normalize statement months by upload grouping
            self._normalize_statement_months(username)
            self._refresh_subscription_metadata(user)
            self._save_users()
        
        # Return message with duplicate info
        if duplicates_count > 0:
            message = f"Added {len(new_transactions)} new transactions. Skipped {duplicates_count} duplicates."
        else:
            message = f"Added {len(new_transactions)} transactions successfully!"
        
        return True, message

    def _normalize_statement_months(self, username: str) -> None:
        """Assign 'Month N' per upload group based on earliest date of each upload.
        Groups transactions by source_upload_id and sorts chronologically by earliest date.
        This ensures Month 1, Month 2, etc. are assigned in chronological order of uploads.
        """
        if not self.user_exists(username):
            return
        user = self._users[username]
        from collections import defaultdict
        group_dates = defaultdict(list)
        
        # Group transactions by upload_id (each upload gets unique ID)
        for t in user.transactions:
            key = t.source_upload_id or ""
            if key:
                group_dates[key].append(t.date)
            else:
                # For transactions without upload_id, use their date as a fallback key
                # This handles legacy transactions that were uploaded before upload_id was implemented
                date_key = t.date.strftime("%Y-%m")
                group_dates[f"date_{date_key}"].append(t.date)
        
        # Build sorted groups by earliest date in each group
        ordering = []
        for key, dates in group_dates.items():
            if dates:
                earliest = min(dates)
                ordering.append((earliest, key))
        
        if not ordering:
            return
        
        # Sort by earliest date chronologically
        ordering.sort()
        
        # Create label map: Month 1, Month 2, etc. in chronological order
        label_map = {key: f"Month {i+1}" for i, (_, key) in enumerate(ordering)}
        
        # Apply labels to all transactions
        for t in user.transactions:
            key = t.source_upload_id or ""
            if key and key in label_map:
                # Has upload_id and is in our map
                t.statement_month = label_map[key]
            elif not key:
                # No upload_id, use date-based grouping
                date_key = t.date.strftime("%Y-%m")
                fallback_key = f"date_{date_key}"
                if fallback_key in label_map:
                    t.statement_month = label_map[fallback_key]
    
    def remove_duplicate_transactions(self, username: str) -> tuple[bool, str]:
        """Remove duplicate transactions from a user's account"""
        if not self.user_exists(username):
            return False, "User not found"
        
        user = self._users[username]
        original_count = len(user.transactions)
        
        # Use a set to track seen transactions by (date, amount, description, source_upload_id)
        seen = set()
        unique_transactions = []
        duplicates_removed = 0
        
        for txn in user.transactions:
            # Create a unique key for duplicate detection
            # Include source_upload_id to allow same transaction from different uploads if needed
            # But prefer keeping the one with more metadata (has upload_id, has category, etc.)
            txn_key = (txn.date, txn.amount, txn.description, txn.source_upload_id or "")
            
            if txn_key not in seen:
                seen.add(txn_key)
                unique_transactions.append(txn)
            else:
                duplicates_removed += 1
        
        # Update user's transactions
        user.transactions = unique_transactions
        self._refresh_subscription_metadata(user)
        self._save_users()
        
        return True, f"Removed {duplicates_removed} duplicate transactions. {len(unique_transactions)} unique transactions remaining."
    
    def update_transaction(self, username: str, transaction_id: str, **kwargs) -> tuple[bool, str]:
        """Update a specific transaction"""
        if not self.user_exists(username):
            return False, "User not found"
        
        user = self._users[username]
        transaction = next((t for t in user.transactions if t.id == transaction_id), None)
        
        if not transaction:
            return False, "Transaction not found"
        
        # Update allowed fields
        if 'category' in kwargs:
            transaction.category = kwargs['category']
            transaction.user_override = True  # Mark as manually set
        
        if 'notes' in kwargs:
            transaction.notes = kwargs['notes']
        
        self._refresh_subscription_metadata(user)
        self._save_users()
        return True, "Transaction updated successfully!"
    
    def get_user_transactions(self, username: str) -> List[Transaction]:
        """Get all transactions for a user"""
        if not self.user_exists(username):
            return []
        
        return self._users[username].transactions

    def recompute_goal_streak(self, username: str) -> int:
        """Compute consecutive month savings-goal streak using analytics module."""
        if not self.user_exists(username):
            return 0
        user = self._users[username]
        
        from decimal import Decimal
        goal = Decimal(str(user.monthly_savings_goal)) if user.monthly_savings_goal else None
        
        streak = compute_goal_streak(user.transactions, goal)
        user.goal_streak_count = streak
        self._save_users()
        return streak
    
    def get_spending_by_category(self, username: str) -> dict:
        """Get spending totals by category for a user using analytics module."""
        if not self.user_exists(username):
            return {}
        
        return get_spending_by_category_dict(self._users[username].transactions)
