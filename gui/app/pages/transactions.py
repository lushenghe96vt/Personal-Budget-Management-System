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
from ..models.user import User
from core.exportWin import save_window_dialog
from ..style import Styles
from gui.widgets.components import PageHeader


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
        self.setMinimumSize(500, 400)
        
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
        title_label.setStyleSheet(Styles.LABEL_TITLE)
        layout.addWidget(title_label)
        
        # Transaction details (read-only)
        details_group = QGroupBox("Transaction Details")
        details_group.setStyleSheet(Styles.GROUPBOX)
        
        details_layout = QFormLayout()
        details_layout.setSpacing(10)
        
        # Date
        date_label = QLabel(self.transaction.date.strftime("%Y-%m-%d"))
        date_label.setStyleSheet(Styles.LABEL_SECONDARY)
        details_layout.addRow("Date:", date_label)
        
        # Description
        desc_label = QLabel(self.transaction.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(Styles.LABEL_BODY)
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
        edit_group.setStyleSheet(Styles.GROUPBOX)
        
        edit_layout = QFormLayout()
        edit_layout.setSpacing(15)
        
        # Category selection
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.available_categories)
        self.category_combo.setStyleSheet(Styles.COMBOBOX)
        edit_layout.addRow("Category:", self.category_combo)
        
        # Notes
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(100)
        self.notes_text.setStyleSheet(Styles.TEXT_EDIT)
        edit_layout.addRow("Notes:", self.notes_text)
        
        edit_group.setLayout(edit_layout)
        layout.addWidget(edit_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(Styles.BUTTON_NEUTRAL)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        self.save_button = QPushButton("Save Changes")
        self.save_button.setStyleSheet(Styles.BUTTON_SUCCESS)
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
        self._sort_field = "Date"
        self._sort_ascending = False
        self._display_transactions: list[Transaction] = []
        
        # Initialize with error handling
        try:
            self.available_categories = self.load_available_categories()
            self.setup_ui()
            self.populate_table()
        except Exception as e:
            # If initialization fails, show error but don't crash
            import traceback
            print(f"Error initializing TransactionsPage: {e}")
            traceback.print_exc()
            # Create a minimal UI to show error
            layout = QVBoxLayout()
            error_label = QLabel(f"Error loading transactions page: {str(e)}")
            error_label.setStyleSheet("color: red; padding: 20px;")
            layout.addWidget(error_label)
            self.setLayout(layout)
    
    def setup_ui(self):
        """Setup the transactions page UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with back button and title
        page_header = PageHeader("Transaction Management", show_back=True)
        # Connect back button signal - use lambda to prevent immediate emission
        page_header.back_clicked.connect(lambda: self.go_back_to_dashboard.emit())
        layout.addWidget(page_header)
        
        # (Title moved into header)
        
        # Summary stats
        stats_layout = QHBoxLayout()
        
        # Store labels as instance variables so we can update them
        self.total_label = QLabel("Total Transactions: 0")
        self.total_label.setStyleSheet(Styles.STAT_LABEL_BLUE)
        stats_layout.addWidget(self.total_label)
        
        self.spending_label = QLabel("Total Spending: $0.00")
        self.spending_label.setStyleSheet(Styles.STAT_LABEL_RED)
        stats_layout.addWidget(self.spending_label)
        
        self.income_label = QLabel("Total Income: $0.00")
        self.income_label.setStyleSheet(Styles.STAT_LABEL_GREEN)
        stats_layout.addWidget(self.income_label)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Update summary stats
        self._update_summary_stats()
        
        # Search and filter section + sort
        filter_layout = QHBoxLayout()
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search transactions...")
        self.search_input.setStyleSheet(Styles.LINE_EDIT)
        self.search_input.textChanged.connect(self.filter_transactions)
        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.search_input)
        
        # Category filter
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.category_filter.addItems(sorted(self.available_categories))
        self.category_filter.setStyleSheet(Styles.COMBOBOX)
        self.category_filter.currentTextChanged.connect(self.filter_transactions)
        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addWidget(self.category_filter)
        
        # Sort controls
        self.sort_field = QComboBox()
        self.sort_field.addItems(["Date", "Category", "Description"])
        self.sort_field.setStyleSheet(Styles.COMBOBOX)
        
        self.sort_dir = QComboBox()
        self.sort_dir.addItems(["Descending", "Ascending"])
        self.sort_dir.setStyleSheet(Styles.COMBOBOX)
        
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
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Date", "Description", "Category", "Amount", "Actions"
        ])
        
        # Configure table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Description
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Category
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Amount
        # Actions column: ResizeToContents but with minimum width
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Actions
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setStyleSheet(Styles.TABLE)
        
        layout.addWidget(self.table)
        # Set minimum row height instead of fixed height (increased for better button visibility)
        self.table.verticalHeader().setMinimumSectionSize(50)
        self.table.verticalHeader().setDefaultSectionSize(50)
        # Allow rows to resize based on content
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet(Styles.BUTTON_PRIMARY)
        self.refresh_button.clicked.connect(self.refresh_table)
        button_layout.addWidget(self.refresh_button)
        
        # controls remain on right
        
        self.export_button = QPushButton("Export Data")
        self.export_button.setStyleSheet(Styles.BUTTON_SECONDARY)
        self.export_button.clicked.connect(self.export_transactions)
        button_layout.addWidget(self.export_button)
        
        # Clear all transactions button
        self.clear_all_button = QPushButton("Clear All Transactions")
        self.clear_all_button.setStyleSheet(Styles.BUTTON_DANGER)
        self.clear_all_button.clicked.connect(self.clear_all_transactions)
        button_layout.addWidget(self.clear_all_button)
        
        layout.addLayout(button_layout)
        # Layout is already set via QVBoxLayout(self) constructor above
    
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
            # Error loading categories
            pass
        
        # Default categories if rules file not found
        return [
            "Uncategorized", "Groceries", "Dining", "Gas", "Utilities", 
            "Entertainment", "Shopping", "Healthcare", "Transportation", 
            "Income", "Transfers", "Subscriptions"
        ]
    
    def populate_table(self):
        """Populate the table with user's transactions"""
        # Ensure table exists
        if not hasattr(self, 'table') or self.table is None:
            return
            
        if not self.user or not hasattr(self.user, 'transactions'):
            self._display_transactions = []
            self.table.setRowCount(0)
            return
        
        transactions = self.user.transactions or []
        self._display_transactions = self._get_sorted_transactions(transactions)
        
        self.table.setRowCount(len(self._display_transactions))
        
        for row, txn in enumerate(self._display_transactions):
            # Date - with error handling
            try:
                date_str = txn.date.strftime("%Y-%m-%d") if hasattr(txn, 'date') and txn.date else "N/A"
            except Exception:
                date_str = "N/A"
            date_item = QTableWidgetItem(date_str)
            self.table.setItem(row, 0, date_item)
            
            # Description - with error handling
            desc = getattr(txn, 'description', '') or 'N/A'
            desc_item = QTableWidgetItem(desc)
            if hasattr(txn, 'description_raw') and txn.description_raw:
                desc_item.setToolTip(txn.description_raw)
            self.table.setItem(row, 1, desc_item)
            
            # Category - with error handling
            category = getattr(txn, 'category', '') or 'Uncategorized'
            category_item = QTableWidgetItem(category)
            if hasattr(txn, 'user_override') and txn.user_override:
                category_item.setBackground(QColor("#fff3cd"))
            self.table.setItem(row, 2, category_item)
            
            # Amount - with error handling and color coding
            try:
                amount = getattr(txn, 'amount', 0) or 0
                amount_value = float(amount)
                amount_sign = "-" if amount_value < 0 else "+"
                amount_str = f"{amount_sign}${abs(amount_value):.2f}"
                amount_item = QTableWidgetItem(amount_str)
                
                # Color code: red for expenses, green for income
                if amount_value < 0:
                    amount_item.setForeground(QColor("#e74c3c"))  # Red for expenses
                else:
                    amount_item.setForeground(QColor("#27ae60"))  # Green for income
                
                # Right align for better readability
                amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                amount_item.setFont(QFont("", -1, QFont.Weight.Bold))
            except Exception:
                amount_item = QTableWidgetItem("N/A")
                amount_item.setForeground(QColor("#7f8c8d"))
            self.table.setItem(row, 3, amount_item)
            
            # Actions - Use simple QPushButton for better performance
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Simple edit button
            edit_button = QPushButton("📝")
            edit_button.setToolTip("Edit transaction")
            edit_button.setMaximumSize(32, 32)
            edit_button.setStyleSheet("""
                QPushButton {
                    border: none;
                    background-color: transparent;
                    color: #555555;
                    font-size: 16px;
                    padding: 4px;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                    color: #3498db;
                }
            """)
            edit_button.clicked.connect(lambda checked, t=txn: self.edit_transaction(t))
            actions_layout.addWidget(edit_button)
            
            # Simple delete button
            delete_button = QPushButton("✕")
            delete_button.setToolTip("Delete transaction")
            delete_button.setMaximumSize(32, 32)
            delete_button.setStyleSheet("""
                QPushButton {
                    border: none;
                    background-color: transparent;
                    color: #555555;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 4px;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                    color: #e74c3c;
                }
            """)
            delete_button.clicked.connect(lambda checked, t=txn: self.delete_transaction(t))
            actions_layout.addWidget(delete_button)
            
            actions_widget.setLayout(actions_layout)
            self.table.setCellWidget(row, 4, actions_widget)
        
        # Set appropriate width for Amount and Actions columns
        self.table.setColumnWidth(3, 120)  # Amount column
        self.table.setColumnWidth(4, 100)  # Actions column
        # Standard row height
        self.table.verticalHeader().setDefaultSectionSize(40)

        # Interactions
        self.table.cellDoubleClicked.connect(self.open_details_dialog)
        self.table.cellClicked.connect(self.handle_cell_click)

    def _get_sorted_transactions(self, transactions: list[Transaction]) -> list[Transaction]:
        """Return transactions sorted according to the current sort selection."""
        if not transactions:
            return []

        field = getattr(self, "_sort_field", "Date")
        ascending = getattr(self, "_sort_ascending", False)

        def safe_date(txn: Transaction):
            if hasattr(txn, "date") and txn.date:
                return txn.date
            return datetime.min

        def safe_category(txn: Transaction):
            return (getattr(txn, "category", "") or "").lower()

        def safe_description(txn: Transaction):
            return (getattr(txn, "description", "") or "").lower()

        key_map = {
            "Date": safe_date,
            "Category": safe_category,
            "Description": safe_description,
        }
        key_func = key_map.get(field, safe_date)

        try:
            return sorted(transactions, key=key_func, reverse=not ascending)
        except Exception:
            # Fall back to original order if sorting fails
            return list(transactions)

    def handle_cell_click(self, row: int, col: int):
        # Single-click edit via dialog
        self.open_edit_dialog_for_row(row)

    def open_edit_dialog_for_row(self, row: int):
        if row < 0:
            return
        if not self._display_transactions:
            return
        if row >= len(self._display_transactions):
            return
        txn = self._display_transactions[row]
        try:
            self.edit_transaction(txn)
        except Exception:
            QMessageBox.warning(self, "Error", "Unable to load transaction for editing.")

    def open_details_dialog(self, row: int, col: int):
        if row < 0:
            return
        if not self._display_transactions:
            return
        if row >= len(self._display_transactions):
            return
        t = self._display_transactions[row]
        try:
            date_str = t.date.strftime('%Y-%m-%d') if hasattr(t, 'date') and t.date else "N/A"
        except Exception:
            date_str = "N/A"
        dlg = QDialog(self)
        dlg.setWindowTitle("Transaction Details")
        dlg.setMinimumSize(520, 420)
        box = QVBoxLayout()
        box.setContentsMargins(16, 16, 16, 16)
        box.setSpacing(8)
        def add(label, value):
            h = QHBoxLayout()
            h.addWidget(QLabel(f"{label}:"))
            v = QLabel(value)
            v.setStyleSheet(Styles.LABEL_BODY)
            h.addWidget(v)
            h.addStretch()
            box.addLayout(h)
        add("Date", date_str)
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
        if not hasattr(self, "_display_transactions") or not self._display_transactions:
            return

        search_text = (self.search_input.text() or "").lower()
        category_filter = self.category_filter.currentText()

        total_rows = self.table.rowCount()
        for row in range(total_rows):
            if row >= len(self._display_transactions):
                self.table.setRowHidden(row, True)
                continue

            txn = self._display_transactions[row]
            should_show = True

            if search_text:
                desc = (getattr(txn, 'description', '') or '').lower()
                if search_text not in desc:
                    should_show = False

            if category_filter != "All Categories":
                txn_category = getattr(txn, 'category', None) or "Uncategorized"
                if txn_category != category_filter:
                    should_show = False

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
    
    def _update_summary_stats(self):
        """Update the summary statistics labels"""
        if not self.user:
            return
        
        # Get transactions with error handling
        transactions = getattr(self.user, 'transactions', []) or []
        total_txns = len(transactions)
        
        # Total spending - with error handling
        try:
            total_spending = sum(abs(t.amount) for t in transactions if hasattr(t, 'amount') and t.amount and t.amount < 0)
        except Exception:
            total_spending = 0.0
        
        # Total income - with error handling
        try:
            total_income = sum(t.amount for t in transactions if hasattr(t, 'amount') and t.amount and t.amount > 0)
        except Exception:
            total_income = 0.0
        
        # Update labels
        if hasattr(self, 'total_label'):
            self.total_label.setText(f"Total Transactions: {total_txns}")
        if hasattr(self, 'spending_label'):
            self.spending_label.setText(f"Total Spending: ${total_spending:.2f}")
        if hasattr(self, 'income_label'):
            self.income_label.setText(f"Total Income: ${total_income:.2f}")
    
    def refresh_table(self):
        """Refresh the transactions table"""
        # Reload user data to get latest transactions
        if self.user_manager and self.user:
            self.user = self.user_manager.get_user(self.user.username)
        self.populate_table()
        # Also update summary stats
        self._update_summary_stats()
        self.filter_transactions()

    def sort_transactions(self):
        field = self.sort_field.currentText()
        ascending = self.sort_dir.currentText() == "Ascending"

        # Persist preferences and refresh the table display
        self._sort_field = field
        self._sort_ascending = ascending
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
        """Export the current page view as PNG/PDF using Jason's export utility."""
        try:
            save_window_dialog(self)
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Unable to export: {e}")
