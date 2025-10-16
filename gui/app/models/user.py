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
from typing import Optional, List
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
            'transactions': [self._transaction_to_dict(txn) for txn in self.transactions]
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
            last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None
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
            'posted_date': txn.posted_date.isoformat() if txn.posted_date else None,
            'description_raw': txn.description_raw,
            'merchant': txn.merchant,
            'currency': txn.currency,
            'txn_type': txn.txn_type,
            'balance': str(txn.balance) if txn.balance else None,
            'category': txn.category,
            'notes': txn.notes,
            'user_override': txn.user_override,
            'source_name': txn.source_name,
            'source_upload_id': txn.source_upload_id,
            'raw': txn.raw
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
            posted_date=datetime.fromisoformat(data['posted_date']) if data.get('posted_date') else None,
            description_raw=data.get('description_raw', ''),
            merchant=data.get('merchant', ''),
            currency=data.get('currency', 'USD'),
            txn_type=data.get('txn_type', ''),
            balance=Decimal(data['balance']) if data.get('balance') else None,
            category=data.get('category', 'Uncategorized'),
            notes=data.get('notes', ''),
            user_override=data.get('user_override', False),
            source_name=data.get('source_name', ''),
            source_upload_id=data.get('source_upload_id', ''),
            raw=data.get('raw', {})
        )


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
                    return {username: User.from_dict(user_data) for username, user_data in data.items()}
            except (json.JSONDecodeError, KeyError):
                return {}
        return {}
    
    def _save_users(self):
        """Save users to storage"""
        data = {username: user.to_dict() for username, user in self._users.items()}
        with open(self.users_file, 'w') as f:
            json.dump(data, f, indent=2)
    
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
        """Add transactions to a user's account"""
        if not self.user_exists(username):
            return False, "User not found"
        
        user = self._users[username]
        user.transactions.extend(transactions)
        self._save_users()
        return True, f"Added {len(transactions)} transactions successfully!"
    
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
        
        self._save_users()
        return True, "Transaction updated successfully!"
    
    def get_user_transactions(self, username: str) -> List[Transaction]:
        """Get all transactions for a user"""
        if not self.user_exists(username):
            return []
        
        return self._users[username].transactions
    
    def get_spending_by_category(self, username: str) -> dict:
        """Get spending totals by category for a user"""
        if not self.user_exists(username):
            return {}
        
        category_totals = {}
        for txn in self._users[username].transactions:
            if txn.amount < 0:  # Only spending (negative amounts)
                category = txn.category
                if category not in category_totals:
                    category_totals[category] = 0
                category_totals[category] += abs(txn.amount)
        
        return category_totals
