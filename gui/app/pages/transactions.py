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
    QGroupBox, QFrame, QSplitter, QTabWidget, QToolButton, QStyle, QSizePolicy
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
from core.exportWin import save_window_dialog


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
        
        # Header row with back icon and title
        header = QHBoxLayout()
        self.back_button = QToolButton()
        self.back_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack))
        self.back_button.setAutoRaise(True)
        self.back_button.setStyleSheet("QToolButton { padding-right: 8px; } QToolButton:hover { color: #245add; }")
        self.back_button.clicked.connect(self.go_back_to_dashboard)
        header.addWidget(self.back_button)
        title_label = QLabel("Transaction Management")
        title_font = QFont()
        title_font.setPointSize(26)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50;")
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)
        
        # (Title moved into header)
        
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
        
        # Search and filter section + sort
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
        
        # Common dropdown styling
        dropdown_style = """
            QComboBox {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #ddd;
                border-radius: 6px;
                selection-background-color: #3498db;
                selection-color: white;
            }
        """
        
        # Category filter
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.category_filter.addItems(sorted(self.available_categories))
        self.category_filter.setStyleSheet(dropdown_style)
        self.category_filter.currentTextChanged.connect(self.filter_transactions)
        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addWidget(self.category_filter)
        
        # Sort controls
        self.sort_field = QComboBox()
        self.sort_field.addItems(["Date", "Category", "Description"])
        self.sort_field.setStyleSheet(dropdown_style)
        
        self.sort_dir = QComboBox()
        self.sort_dir.addItems(["Descending", "Ascending"])
        self.sort_dir.setStyleSheet(dropdown_style)
        
        sort_btn = QPushButton("Sort")
        sort_btn.clicked.connect(self.sort_transactions)
        filter_layout.addWidget(QLabel("Sort by:"))
        filter_layout.addWidget(self.sort_field)
        filter_layout.addWidget(self.sort_dir)
        filter_layout.addWidget(sort_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Transactions table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Date", "Description", "Category", "Actions"
        ])
        
        # Configure table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Description
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Category
        # Actions column: ResizeToContents but with minimum width
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Actions
        
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
        self.table.setStyleSheet("QTableWidget::item { padding: 10px; }")
        # Set minimum row height instead of fixed height (increased for better button visibility)
        self.table.verticalHeader().setMinimumSectionSize(50)
        self.table.verticalHeader().setDefaultSectionSize(50)
        # Allow rows to resize based on content
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.refresh_button = QPushButton("Refresh")
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
        
        # controls remain on right
        
        self.export_button = QPushButton("Export Data")
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
        self.clear_all_button = QPushButton("Clear All Transactions")
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
            desc_item.setToolTip(txn.description_raw)
            self.table.setItem(row, 1, desc_item)
            
            # Category
            category_item = QTableWidgetItem(txn.category)
            if txn.user_override:
                category_item.setBackground(QColor("#fff3cd"))
            self.table.setItem(row, 2, category_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            # Increased margins for better padding and centering
            actions_layout.setContentsMargins(10, 6, 10, 6)
            # Increased spacing between buttons to prevent collision
            actions_layout.setSpacing(12)
            # Center both horizontally and vertically
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            
            edit_button = QPushButton("Edit")
            edit_button.setStyleSheet("""
                QPushButton {
                    background-color: #f39c12;
                    color: white;
                    border: none;
                    padding: 8px 14px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #e67e22;
                }
            """)
            edit_button.setMinimumHeight(30)
            edit_button.setMinimumWidth(75)
            edit_button.setMaximumWidth(75)
            edit_button.clicked.connect(lambda checked, t=txn: self.edit_transaction(t))
            actions_layout.addWidget(edit_button)
            
            delete_button = QPushButton("Delete")
            delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    padding: 8px 14px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            delete_button.setMinimumHeight(30)
            delete_button.setMinimumWidth(75)
            delete_button.setMaximumWidth(75)
            delete_button.clicked.connect(lambda checked, t=txn: self.delete_transaction(t))
            actions_layout.addWidget(delete_button)
            
            actions_widget.setLayout(actions_layout)
            # Set minimum and preferred height for better vertical centering
            actions_widget.setMinimumHeight(44)
            actions_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            self.table.setCellWidget(row, 3, actions_widget)
        
        # Set minimum width for Actions column after populating
        actions_col_width = self.table.columnWidth(3)
        if actions_col_width < 160:
            self.table.setColumnWidth(3, 160)
        
        # Ensure rows have flexible height with minimum (enough for action buttons)
        for row in range(self.table.rowCount()):
            height = self.table.rowHeight(row)
            if height < 50:
                self.table.setRowHeight(row, 50)

        # Interactions
        from functools import partial
        self.table.cellDoubleClicked.connect(self.open_details_dialog)
        self.table.cellClicked.connect(self.handle_cell_click)

    def handle_cell_click(self, row: int, col: int):
        # Single-click edit via dialog
        self.open_edit_dialog_for_row(row)

    def open_edit_dialog_for_row(self, row: int):
        if row < 0:
            return
        txns = sorted(self.user.transactions, key=lambda t: t.date, reverse=True)
        if row >= len(txns):
            return
        self.edit_transaction(txns[row])

    def open_details_dialog(self, row: int, col: int):
        if row < 0:
            return
        txns = sorted(self.user.transactions, key=lambda t: t.date, reverse=True)
        if row >= len(txns):
            return
        t = txns[row]
        dlg = QDialog(self)
        dlg.setWindowTitle("Transaction Details")
        dlg.resize(520, 420)
        box = QVBoxLayout()
        box.setContentsMargins(16, 16, 16, 16)
        box.setSpacing(8)
        def add(label, value):
            h = QHBoxLayout()
            h.addWidget(QLabel(f"{label}:"))
            v = QLabel(value)
            v.setStyleSheet("font-weight: 600; color: #2c3e50;")
            h.addWidget(v)
            h.addStretch()
            box.addLayout(h)
        add("Date", t.date.strftime('%Y-%m-%d'))
        add("Description", t.description)
        add("Raw", t.description_raw or "-")
        add("Amount", f"{'-' if t.amount < 0 else '+'}${abs(t.amount):.2f}")
        add("Category", t.category)
        add("Notes", t.notes or "-")
        add("Source", t.source_name or "-")
        add("Statement", t.statement_month or "-")
        if getattr(t, 'is_subscription', False):
            nd = getattr(t, 'next_due_date', None)
            add("Subscription", "Yes")
            add("Next Due", nd.strftime('%Y-%m-%d') if nd else "-")
        btn = QPushButton("Close")
        btn.clicked.connect(dlg.accept)
        box.addStretch()
        box.addWidget(btn)
        dlg.setLayout(box)
        dlg.exec()
    
    def filter_transactions(self):
        """Filter transactions based on search and category"""
        search_text = self.search_input.text().lower()
        category_filter = self.category_filter.currentText()
        
        # Get sorted transactions to match table order
        transactions = sorted(self.user.transactions, key=lambda t: t.date, reverse=True)
        
        for row in range(self.table.rowCount()):
            should_show = True
            
            if row >= len(transactions):
                should_show = False
                self.table.setRowHidden(row, True)
                continue
            
            txn = transactions[row]
            
            # Search filter - search in description
            if search_text:
                desc = (self.table.item(row, 1).text() if self.table.item(row, 1) else "").lower()
                if search_text not in desc:
                    should_show = False
            
            # Category filter - check category column (column 2)
            if category_filter != "All Categories":
                category_item = self.table.item(row, 2)
                category = category_item.text() if category_item else ""
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

    def sort_transactions(self):
        field = self.sort_field.currentText()
        ascending = self.sort_dir.currentText() == "Ascending"
        keyf = None
        if field == "Date":
            keyf = lambda t: t.date
        elif field == "Category":
            keyf = lambda t: (t.category or "")
        elif field == "Description":
            keyf = lambda t: (t.description or "")
        if keyf is None:
            return
        self.user.transactions = sorted(self.user.transactions, key=keyf, reverse=not ascending)
        if self.user_manager:
            self.user_manager._users[self.user.username] = self.user
            self.user_manager._save_users()
        self.refresh_table()
    
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
        """Export the current page view as PNG/PDF using Jason's export utility."""
        try:
            save_window_dialog(self)
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Unable to export: {e}")
