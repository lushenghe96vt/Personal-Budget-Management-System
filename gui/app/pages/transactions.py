"""
transactions.py
Personal Budget Management System - Transaction Management Module
Author: Ankush
Date: 10/11/25

Description:
  Comprehensive transaction management interface with search, filter, and edit capabilities.
  Displays all user transactions in a sortable table format.

Implements:
  - Transaction table with sortable columns
  - Search and filter functionality
  - Category editing (integrates Luke's set_category)
  - Notes editing (integrates Luke's set_notes)
  - Individual transaction deletion
  - Bulk transaction clearing
  - Transaction export functionality
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QTextEdit, QDialog, QFormLayout,
    QGroupBox, QFrame, QSplitter, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QSortFilterProxyModel, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QFont, QColor
from pathlib import Path
import sys
from datetime import datetime
from decimal import Decimal

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.categorize_edit import set_category, set_notes, CategoryRules
from core.models import Transaction
from models import User


class TransactionEditDialog(QDialog):
    """Dialog for editing transaction category and notes"""
    
    def __init__(self, transaction: Transaction, available_categories: list, parent=None):
        super().__init__(parent)
        self.transaction = transaction
        self.available_categories = available_categories
        self.setup_ui()
        self.load_transaction_data()
    
    def setup_ui(self):
        """Setup the edit dialog UI"""
        self.setWindowTitle("Edit Transaction")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Edit Transaction")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Transaction details (read-only)
        details_group = QGroupBox("Transaction Details")
        details_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        details_layout = QFormLayout()
        details_layout.setSpacing(10)
        
        # Date
        date_label = QLabel(self.transaction.date.strftime("%Y-%m-%d"))
        date_label.setStyleSheet("color: #7f8c8d;")
        details_layout.addRow("Date:", date_label)
        
        # Description
        desc_label = QLabel(self.transaction.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #2c3e50;")
        details_layout.addRow("Description:", desc_label)
        
        # Amount
        amount_color = "#e74c3c" if self.transaction.amount < 0 else "#27ae60"
        amount_sign = "-" if self.transaction.amount < 0 else "+"
        amount_label = QLabel(f"{amount_sign}${abs(self.transaction.amount):.2f}")
        amount_label.setStyleSheet(f"color: {amount_color}; font-weight: bold;")
        details_layout.addRow("Amount:", amount_label)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Editable fields
        edit_group = QGroupBox("Edit Fields")
        edit_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        edit_layout = QFormLayout()
        edit_layout.setSpacing(15)
        
        # Category selection
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.available_categories)
        self.category_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
        """)
        edit_layout.addRow("Category:", self.category_combo)
        
        # Notes
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(100)
        self.notes_text.setStyleSheet("""
            QTextEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #3498db;
            }
        """)
        edit_layout.addRow("Notes:", self.notes_text)
        
        edit_group.setLayout(edit_layout)
        layout.addWidget(edit_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        self.save_button = QPushButton("Save Changes")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.save_button.clicked.connect(self.accept)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_transaction_data(self):
        """Load current transaction data into the form"""
        # Set current category
        current_index = self.category_combo.findText(self.transaction.category)
        if current_index >= 0:
            self.category_combo.setCurrentIndex(current_index)
        
        # Set current notes
        self.notes_text.setPlainText(self.transaction.notes)
    
    def get_updated_data(self):
        """Get the updated category and notes"""
        return {
            'category': self.category_combo.currentText(),
            'notes': self.notes_text.toPlainText().strip()
        }


class TransactionsPage(QWidget):
    """Transaction management page"""
    
    transaction_updated = pyqtSignal()  # Signal when a transaction is updated
    go_back_to_dashboard = pyqtSignal()  # Signal to go back to dashboard
    
    def __init__(self, user: User, user_manager=None):
        super().__init__()
        self.user = user
        self.user_manager = user_manager
        self.available_categories = self.load_available_categories()
        self.setup_ui()
        self.populate_table()
    
    def setup_ui(self):
        """Setup the transactions page UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Transaction Management")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Summary stats
        stats_layout = QHBoxLayout()
        
        # Total transactions
        total_txns = len(self.user.transactions)
        total_label = QLabel(f"Total Transactions: {total_txns}")
        total_label.setStyleSheet("""
            QLabel {
                background-color: #3498db;
                color: white;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
            }
        """)
        stats_layout.addWidget(total_label)
        
        # Total spending
        total_spending = sum(abs(t.amount) for t in self.user.transactions if t.amount < 0)
        spending_label = QLabel(f"Total Spending: ${total_spending:.2f}")
        spending_label.setStyleSheet("""
            QLabel {
                background-color: #e74c3c;
                color: white;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
            }
        """)
        stats_layout.addWidget(spending_label)
        
        # Total income
        total_income = sum(t.amount for t in self.user.transactions if t.amount > 0)
        income_label = QLabel(f"Total Income: ${total_income:.2f}")
        income_label.setStyleSheet("""
            QLabel {
                background-color: #27ae60;
                color: white;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
            }
        """)
        stats_layout.addWidget(income_label)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Search and filter section
        filter_layout = QHBoxLayout()
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search transactions...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        self.search_input.textChanged.connect(self.filter_transactions)
        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.search_input)
        
        # Category filter
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.category_filter.addItems(sorted(self.available_categories))
        self.category_filter.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        self.category_filter.currentTextChanged.connect(self.filter_transactions)
        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addWidget(self.category_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Transactions table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Date", "Description", "Amount", "Category", "Notes", "Source", "Actions"
        ])
        
        # Configure table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Description
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Amount
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Category
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Notes
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Source
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Actions
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.table)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.back_button = QPushButton("🏠 Back to Dashboard")
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.back_button.clicked.connect(self.go_back_to_dashboard)
        button_layout.addWidget(self.back_button)
        
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_table)
        button_layout.addWidget(self.refresh_button)
        
        button_layout.addStretch()
        
        self.export_button = QPushButton("📊 Export Data")
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        self.export_button.clicked.connect(self.export_transactions)
        button_layout.addWidget(self.export_button)
        
        # Clear all transactions button
        self.clear_all_button = QPushButton("🗑️ Clear All Transactions")
        self.clear_all_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.clear_all_button.clicked.connect(self.clear_all_transactions)
        button_layout.addWidget(self.clear_all_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_available_categories(self):
        """Load available categories from rules.json"""
        try:
            rules_path = project_root / "data" / "rules.json"
            if rules_path.exists():
                rules = CategoryRules.from_json(rules_path)
                # Extract categories from the rules
                categories = set()
                for category, _ in rules._compiled:
                    categories.add(category)
                return sorted(list(categories))
        except Exception as e:
            print(f"Error loading categories: {e}")
        
        # Default categories if rules file not found
        return [
            "Uncategorized", "Groceries", "Dining", "Gas", "Utilities", 
            "Entertainment", "Shopping", "Healthcare", "Transportation", 
            "Income", "Transfers", "Subscriptions"
        ]
    
    def populate_table(self):
        """Populate the table with user's transactions"""
        transactions = self.user.transactions
        
        # Sort by date (newest first)
        transactions = sorted(transactions, key=lambda t: t.date, reverse=True)
        
        self.table.setRowCount(len(transactions))
        
        for row, txn in enumerate(transactions):
            # Date
            date_item = QTableWidgetItem(txn.date.strftime("%Y-%m-%d"))
            self.table.setItem(row, 0, date_item)
            
            # Description
            desc_item = QTableWidgetItem(txn.description)
            desc_item.setToolTip(txn.description_raw)  # Show raw description on hover
            self.table.setItem(row, 1, desc_item)
            
            # Amount
            amount_color = QColor("#e74c3c") if txn.amount < 0 else QColor("#27ae60")
            amount_sign = "-" if txn.amount < 0 else "+"
            amount_item = QTableWidgetItem(f"{amount_sign}${abs(txn.amount):.2f}")
            amount_item.setForeground(amount_color)
            self.table.setItem(row, 2, amount_item)
            
            # Category
            category_item = QTableWidgetItem(txn.category)
            if txn.user_override:
                category_item.setBackground(QColor("#fff3cd"))  # Light yellow for manual overrides
            self.table.setItem(row, 3, category_item)
            
            # Notes
            notes_item = QTableWidgetItem(txn.notes)
            self.table.setItem(row, 4, notes_item)
            
            # Source
            source_item = QTableWidgetItem(txn.source_name or "Unknown")
            self.table.setItem(row, 5, source_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(5)
            
            edit_button = QPushButton("Edit")
            edit_button.setStyleSheet("""
                QPushButton {
                    background-color: #f39c12;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #e67e22;
                }
            """)
            edit_button.clicked.connect(lambda checked, t=txn: self.edit_transaction(t))
            actions_layout.addWidget(edit_button)
            
            delete_button = QPushButton("Delete")
            delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            delete_button.clicked.connect(lambda checked, t=txn: self.delete_transaction(t))
            actions_layout.addWidget(delete_button)
            
            actions_widget.setLayout(actions_layout)
            self.table.setCellWidget(row, 6, actions_widget)
    
    def filter_transactions(self):
        """Filter transactions based on search and category"""
        search_text = self.search_input.text().lower()
        category_filter = self.category_filter.currentText()
        
        for row in range(self.table.rowCount()):
            should_show = True
            
            # Search filter
            if search_text:
                desc = self.table.item(row, 1).text().lower()
                notes = self.table.item(row, 4).text().lower()
                if search_text not in desc and search_text not in notes:
                    should_show = False
            
            # Category filter
            if category_filter != "All Categories":
                category = self.table.item(row, 3).text()
                if category != category_filter:
                    should_show = False
            
            # Show/hide row
            self.table.setRowHidden(row, not should_show)
    
    def edit_transaction(self, transaction: Transaction):
        """Open dialog to edit transaction"""
        dialog = TransactionEditDialog(transaction, self.available_categories, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_updated_data()
            
            # Update transaction using Luke's functions
            set_category(transaction, updated_data['category'], mark_override=True)
            set_notes(transaction, updated_data['notes'])
            
            # Save to user manager if available
            if self.user_manager:
                success, message = self.user_manager.update_transaction(
                    self.user.username, 
                    transaction.id,
                    category=updated_data['category'],
                    notes=updated_data['notes']
                )
                
                if success:
                    QMessageBox.information(self, "Success", "Transaction updated successfully!")
                    self.refresh_table()
                    self.transaction_updated.emit()
                else:
                    QMessageBox.warning(self, "Error", f"Failed to update transaction: {message}")
            else:
                # Just update locally
                self.refresh_table()
                self.transaction_updated.emit()
    
    def refresh_table(self):
        """Refresh the transactions table"""
        self.populate_table()
        self.filter_transactions()
    
    def delete_transaction(self, transaction):
        """Delete a transaction"""
        reply = QMessageBox.question(
            self,
            "Delete Transaction",
            f"Are you sure you want to delete this transaction?\n\n"
            f"Date: {transaction.date.strftime('%Y-%m-%d')}\n"
            f"Description: {transaction.description}\n"
            f"Amount: ${transaction.amount}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from user's transactions
            if transaction in self.user.transactions:
                self.user.transactions.remove(transaction)
                
                # Save to user manager if available
                if self.user_manager:
                    # Update the user in the manager
                    self.user_manager._users[self.user.username] = self.user
                    self.user_manager._save_users()
                
                # Refresh the table
                self.refresh_table()
                
                # Emit signal to update other pages
                self.transaction_updated.emit()
                
                QMessageBox.information(self, "Success", "Transaction deleted successfully!")
            else:
                QMessageBox.warning(self, "Error", "Transaction not found in user's data.")
    
    def clear_all_transactions(self):
        """Clear all transactions for the user"""
        if not self.user.transactions:
            QMessageBox.information(self, "No Transactions", "No transactions to clear.")
            return
            
        reply = QMessageBox.question(
            self,
            "Clear All Transactions",
            f"Are you sure you want to delete ALL {len(self.user.transactions)} transactions?\n\n"
            "This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear all transactions
            self.user.transactions.clear()
            
            # Save to user manager if available
            if self.user_manager:
                self.user_manager._users[self.user.username] = self.user
                self.user_manager._save_users()
            
            # Refresh the table
            self.refresh_table()
            
            # Emit signal to update other pages
            self.transaction_updated.emit()
            
            QMessageBox.information(self, "Success", "All transactions cleared successfully!")
    
    def export_transactions(self):
        """Export transactions to CSV"""
        QMessageBox.information(
            self,
            "Export Feature",
            "Transaction export feature will be implemented in future sprints.\n\n"
            "This will include:\n"
            "- Export to CSV format\n"
            "- Filter by date range\n"
            "- Include/exclude specific categories\n"
            "- Custom field selection"
        )
