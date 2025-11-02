"""
dashboard.py
Personal Budget Management System - Dashboard Module
Author: Ankush
Date: 10/11/25

Description:
  Main dashboard page displaying user statistics and quick actions.
  Integrates backend CSV processing and categorization pipeline.

Implements:
  - Real-time transaction statistics (spending, income, budget remaining)
  - Bank statement upload with progress tracking
  - CSV parsing integration (Jason's fileUpload)
  - Transaction categorization integration (Luke's categorize_edit)
  - Recent activity display
  - Quick action buttons for navigation
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QMenu, QMenuBar, QFileDialog, QMessageBox, QFrame, QProgressDialog,
    QScrollArea, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QAction, QPixmap, QIcon
from pathlib import Path
import sys
from datetime import datetime
from decimal import Decimal

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.categorize_edit import dicts_to_transactions, auto_categorize, CategoryRules
from core.fileUpload import upload_statement
from models import User


class DashboardPage(QWidget):
    """Main dashboard page widget"""
    
    # Signals for communication with main window
    show_spending_analysis = pyqtSignal()
    show_transactions = pyqtSignal()
    show_budget_settings = pyqtSignal()
    show_profile = pyqtSignal()  # Signal to show profile page
    transactions_updated = pyqtSignal()  # Signal when transactions are updated
    notify = pyqtSignal(str, str)  # text, level
    
    def __init__(self, current_user=None, user_manager=None):
        super().__init__()
        self.current_user = current_user
        self.user_manager = user_manager
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dashboard UI"""
        # Create scroll area for the entire dashboard
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create main widget for scroll area
        main_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Welcome section with user name + streak badge
        welcome_text = "Welcome!"
        if self.current_user:
            name = (getattr(self.current_user, 'first_name', '') or '').strip()
            if not name:
                name = (getattr(self.current_user, 'username', '') or '').strip()
            if name:
                welcome_text = f"Welcome, {name}!"
        
        self.welcome_label = QLabel(welcome_text)
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_font = QFont()
        welcome_font.setPointSize(26)
        welcome_font.setBold(True)
        self.welcome_label.setFont(welcome_font)
        self.welcome_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px; font-size: 26px;")
        layout.addWidget(self.welcome_label)
        
        # Month filter dropdown
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Period:"))
        self.month_filter = QComboBox()
        self.month_filter.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                min-width: 200px;
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
        """)
        self.month_filter.currentTextChanged.connect(self._on_month_filter_changed)
        filter_layout.addWidget(self.month_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Streak badge (shown if > 0)
        self.streak_label = QLabel("")
        self.streak_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.streak_label.setStyleSheet("color: #2c3e50; font-size: 13px; margin-top: -10px;")
        layout.addWidget(self.streak_label)
        
        # Quick stats section (expanded)
        stats_layout = QHBoxLayout()
        
        # Total Spending Card
        self.spending_card = self.create_stat_card("Total Spending", "$0.00", "#e74c3c")
        stats_layout.addWidget(self.spending_card)
        
        # Budget Remaining Card
        self.budget_card = self.create_stat_card("Budget Remaining", "$0.00", "#27ae60")
        stats_layout.addWidget(self.budget_card)
        
        # Transactions Card
        self.transactions_card = self.create_stat_card("Transactions", "0", "#3498db")
        stats_layout.addWidget(self.transactions_card)
        
        layout.addLayout(stats_layout)

        # Add secondary metrics row
        secondary = QHBoxLayout()
        self.income_card = self.create_stat_card("Total Income", "$0.00", "#2f6fed")
        secondary.addWidget(self.income_card)
        self.net_card = self.create_stat_card("Net Balance", "$0.00", "#2c3e50")
        secondary.addWidget(self.net_card)
        self.categories_card = self.create_stat_card("Categories", "0", "#16a085")
        secondary.addWidget(self.categories_card)
        layout.addLayout(secondary)
        
        # Update stats with current user data
        self.update_dashboard_stats()
        
        # Actions condensed
        actions_layout = QHBoxLayout()
        upload_button = QPushButton("Upload Bank Statement")
        upload_button.clicked.connect(self.upload_bank_statement)
        actions_layout.addWidget(upload_button)
        # Export dashboard snapshot
        export_btn = QPushButton("Export Dashboard")
        from core.exportWin import save_window_dialog
        export_btn.clicked.connect(lambda: save_window_dialog(self))
        actions_layout.addWidget(export_btn)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
        # Recent activity section
        activity_label = QLabel("Recent Activity")
        activity_font = QFont()
        activity_font.setPointSize(18)
        activity_font.setBold(True)
        activity_label.setFont(activity_font)
        activity_label.setStyleSheet("color: #2c3e50; margin-top: 30px;")
        layout.addWidget(activity_label)
        
        # Create recent activity frame
        self.activity_frame = QFrame()
        self.activity_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        activity_layout = QVBoxLayout()
        
        # Recent transactions placeholder
        self.recent_transactions_label = QLabel("""
        <h4 style="color: #6c757d;">No recent transactions</h4>
        <p style="color: #6c757d;">Upload your first bank statement to start tracking your spending!</p>
        <p style="color: #6c757d; font-size: 12px;">Supported formats: CSV, PDF, TXT</p>
        """)
        self.recent_transactions_label.setWordWrap(True)
        activity_layout.addWidget(self.recent_transactions_label)
        
        # View all transactions button
        view_all_button = QPushButton("View All Transactions")
        view_all_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        view_all_button.clicked.connect(self.show_transactions.emit)
        activity_layout.addWidget(view_all_button)
        
        self.activity_frame.setLayout(activity_layout)
        layout.addWidget(self.activity_frame)
        
        # (Removed legacy Coming Soon section)
        
        layout.addStretch()
        main_widget.setLayout(layout)
        
        # Set the scroll area's widget
        scroll_area.setWidget(main_widget)
        
        # Set the scroll area as the main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
    
    def create_stat_card(self, title: str, value: str, color: str) -> QWidget:
        """Create a statistics card widget"""
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 20px;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 24px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        return card
    
    def create_navigation_menu(self, parent_layout):
        """Create navigation menu bar"""
        nav_layout = QHBoxLayout()
        
        # Menu button (hamburger style)
        menu_button = QPushButton("☰ Menu")
        menu_button.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
        """)
        
        # Create menu
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
        # Add menu actions
        dashboard_action = QAction("📊 Dashboard", self)
        dashboard_action.triggered.connect(lambda: self.switch_to_page("dashboard"))
        menu.addAction(dashboard_action)
        
        transactions_action = QAction("💳 Transactions", self)
        transactions_action.triggered.connect(self.show_transactions.emit)
        menu.addAction(transactions_action)
        
        budget_action = QAction("💰 Budget", self)
        budget_action.triggered.connect(self.show_budget_settings.emit)
        menu.addAction(budget_action)
        
        analysis_action = QAction("📈 Analysis", self)
        analysis_action.triggered.connect(self.show_spending_analysis.emit)
        menu.addAction(analysis_action)
        
        menu.addSeparator()
        
        settings_action = QAction("⚙️ Settings", self)
        settings_action.triggered.connect(lambda: self.switch_to_page("settings"))
        menu.addAction(settings_action)
        
        menu_button.setMenu(menu)
        nav_layout.addWidget(menu_button)
        nav_layout.addStretch()
        
        parent_layout.addLayout(nav_layout)
    
    def upload_bank_statement(self):
        """Handle bank statement upload using teammates' processing pipeline"""
        if not self.current_user or not self.user_manager:
            QMessageBox.warning(self, "Error", "User not logged in")
            return
        
        # Ask bank type (Auto, Wells Fargo, Chase, Truist)
        bank_options = ["Auto-detect", "Wells Fargo", "Chase", "Truist"]
        bank_choice, ok_bank = QInputDialog.getItem(self, "Bank Type", "Select bank for parsing:", bank_options, 0, False)
        if not ok_bank:
            return

        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Bank Statement", 
            "", 
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Show progress dialog
            progress = QProgressDialog("Processing bank statement...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()
            
            # Step 1: Parse CSV using Jason's upload_statement function
            progress.setLabelText("Reading CSV file...")
            progress.setValue(10)
            
            print(f"Attempting to process file: {file_path}")
            # Select bank enum if chosen explicitly
            from core.fileUpload import Banks
            selected_bank = None
            if bank_choice == "Wells Fargo":
                selected_bank = Banks.WELLS_FARGO
            elif bank_choice == "Chase":
                selected_bank = Banks.CHASE
            elif bank_choice == "Truist":
                selected_bank = Banks.TRUIST

            rows = upload_statement(file_path, bank=selected_bank or Banks.WELLS_FARGO if bank_choice != "Auto-detect" else Banks.WELLS_FARGO)
            print(f"CSV processing completed. Found {len(rows) if rows else 0} rows")
            
            if not rows:
                progress.close()
                QMessageBox.warning(self, "Error", "Failed to read CSV file or file is empty")
                self.notify.emit("Failed to read CSV file or file is empty", "error")
                return
            
            # Step 2: Convert to Transaction objects using Luke's dicts_to_transactions
            progress.setLabelText("Converting to transactions...")
            # Generate unique upload ID for this upload
            upload_id = f"upload-{datetime.now().isoformat(timespec='seconds')}"
            # Statement month will be auto-calculated, so pass empty string
            transactions = dicts_to_transactions(
                rows,
                source_name="user-upload",
                source_upload_id=upload_id,
                statement_month=""  # Will be auto-calculated by _normalize_statement_months
            )
            
            # Step 3: Load categorization rules
            progress.setLabelText("Loading categorization rules...")
            rules_path = project_root / "data" / "rules.json"
            if not rules_path.exists():
                progress.close()
                QMessageBox.critical(self, "Error", f"Rules file not found: {rules_path}")
                return
            
            rules = CategoryRules.from_json(rules_path)
            
            # Step 4: Auto-categorize transactions
            progress.setLabelText("Categorizing transactions...")
            auto_categorize(transactions, rules, overwrite=False)
            
            # Step 5: Add to user's account
            progress.setLabelText("Saving transactions...")
            success, message = self.user_manager.add_transactions(self.current_user.username, transactions)
            
            progress.close()
            
            if success:
                # Statement month is automatically calculated by _normalize_statement_months in add_transactions
                # Show user the calculated month number
                if transactions:
                    # Get the statement_month from the first transaction (all in upload should have same month)
                    calculated_month = transactions[0].statement_month if transactions[0].statement_month else "Unknown"
                    self.notify.emit(f"Uploaded {len(transactions)} transactions. Assigned to {calculated_month}.", "success")
                # Update current user object
                self.current_user.transactions.extend(transactions)
                
                # Repopulate month filter with new transactions
                if hasattr(self, 'month_filter'):
                    self._populate_month_filter()
                
                # Update dashboard stats
                self.update_dashboard_stats()
                
                # Emit signal to notify other components
                self.transactions_updated.emit()
                
                # Update recent activity
                self.update_recent_activity(f"Processed {len(transactions)} transactions from {Path(file_path).name}")
                
                # Show success message
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Successfully processed {len(transactions)} transactions!\n\n"
                    f"Categories found: {len(set(t.category for t in transactions))}\n"
                    f"Total amount: ${sum(abs(t.amount) for t in transactions):.2f}"
                )
                self.notify.emit(f"Processed {len(transactions)} transactions.", "success")
            else:
                QMessageBox.critical(self, "Error", f"Failed to save transactions: {message}")
                self.notify.emit(f"Failed to save transactions: {message}", "error")
                
        except Exception as e:
            if 'progress' in locals():
                progress.close()
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to process bank statement:\n{str(e)}\n\n"
                f"Please ensure the CSV file is in the correct format."
            )
            self.notify.emit("Error while processing bank statement", "error")
    
    def update_recent_activity(self, activity_text):
        """Update the recent activity section"""
        current_time = "Just now"  # In real implementation, use actual timestamp
        self.recent_transactions_label.setText(f"""
        <h4 style="color: #27ae60;">Recent Activity</h4>
        <p style="color: #2c3e50;"><strong>{current_time}:</strong> {activity_text}</p>
        <p style="color: #6c757d; font-size: 12px;">Upload more statements to see detailed transaction history</p>
        """)
    
    def switch_to_page(self, page_name):
        """Switch to different page"""
        if page_name == "dashboard":
            # Dashboard is already shown, do nothing
            return
        else:
            QMessageBox.information(
                self,
                "Navigation",
                f"Switching to {page_name} page.\n\nThis feature will be implemented in future sprints."
            )
    
    def set_current_user(self, user):
        """Update the current user and refresh the welcome message"""
        self.current_user = user
        # Refresh the welcome message
        if hasattr(self, 'welcome_label'):
            name = (getattr(user, 'first_name', '') or '').strip()
            if not name:
                name = (getattr(user, 'username', '') or '').strip()
            if name:
                welcome_text = f"Welcome, {name}!"
            else:
                welcome_text = "Welcome!"
            self.welcome_label.setText(welcome_text)
        
        # Populate month filter with user's transactions
        if hasattr(self, 'month_filter'):
            self._populate_month_filter()
        
        # Update dashboard stats
        self.update_dashboard_stats()
        self.update_streak_badge()
    
    def _populate_month_filter(self):
        """Populate month filter dropdown with available months"""
        if not self.current_user or not self.current_user.transactions:
            self.month_filter.clear()
            self.month_filter.addItem("All Time")
            return
        
        transactions = self.current_user.transactions
        
        # Get unique months (both by date and statement_month)
        month_options = {"All Time": None}
        
        # Add months by date (YYYY-MM format)
        date_months = set()
        for t in transactions:
            month_key = t.date.strftime("%Y-%m")
            month_name = t.date.strftime("%B %Y")  # e.g., "January 2025"
            date_months.add((month_key, month_name))
        
        # Add statement months if they exist
        statement_months = set()
        for t in transactions:
            if t.statement_month:
                statement_months.add(t.statement_month)
        
        # Sort date months chronologically (most recent first)
        sorted_date_months = sorted(date_months, key=lambda x: x[0], reverse=True)
        
        # Add date-based months
        for month_key, month_name in sorted_date_months:
            month_options[month_name] = ("date", month_key)
        
        # Add statement months (prefixed with "Statement: ")
        for stmt_month in sorted(statement_months, reverse=True):
            display_name = f"Statement: {stmt_month}"
            month_options[display_name] = ("statement", stmt_month)
        
        # Populate dropdown
        self.month_filter.clear()
        self.month_filter.addItem("All Time")
        
        # Add date months first
        for month_key, month_name in sorted_date_months:
            self.month_filter.addItem(month_name)
        
        # Add statement months
        for stmt_month in sorted(statement_months, reverse=True):
            display_name = f"Statement: {stmt_month}"
            self.month_filter.addItem(display_name)
        
        # Store options for filtering
        self._month_filter_options = month_options
    
    def _filter_transactions_by_month(self, transactions):
        """Filter transactions based on selected month"""
        selected = self.month_filter.currentText()
        if selected == "All Time" or not hasattr(self, '_month_filter_options'):
            return transactions
        
        filter_info = self._month_filter_options.get(selected)
        if not filter_info:
            return transactions
        
        filter_type, filter_value = filter_info
        
        if filter_type == "date":
            # Filter by date (YYYY-MM)
            year, month = map(int, filter_value.split("-"))
            return [t for t in transactions if t.date.year == year and t.date.month == month]
        elif filter_type == "statement":
            # Filter by statement_month
            return [t for t in transactions if t.statement_month == filter_value]
        
        return transactions
    
    def _on_month_filter_changed(self, text):
        """Handle month filter change"""
        self.update_dashboard_stats()
    
    def update_dashboard_stats(self):
        """Update dashboard statistics with real transaction data"""
        if not self.current_user or not hasattr(self, 'spending_card'):
            return
        
        all_transactions = self.current_user.transactions
        
        # Filter transactions by selected month
        transactions = self._filter_transactions_by_month(all_transactions) if hasattr(self, 'month_filter') else all_transactions
        
        # Populate month filter if not already done
        if hasattr(self, 'month_filter') and self.month_filter.count() == 0:
            self._populate_month_filter()
        
        # Calculate total spending (negative amounts)
        total_spending = sum(abs(t.amount) for t in transactions if t.amount < 0)
        
        # Calculate total income (positive amounts)
        total_income = sum(t.amount for t in transactions if t.amount > 0)
        
        # Calculate budget remaining (simple calculation)
        budget_remaining = total_income - total_spending
        
        # Get unique categories count
        categories = set(t.category for t in transactions)
        category_count = len(categories)
        
        # Update stat cards - find the value labels in each card
        try:
            # Update spending card
            spending_layout = self.spending_card.layout()
            if spending_layout and spending_layout.count() > 1:
                spending_value_label = spending_layout.itemAt(1).widget()
                if spending_value_label:
                    spending_value_label.setText(f"${total_spending:.2f}")
            
            # Update budget card
            budget_layout = self.budget_card.layout()
            if budget_layout and budget_layout.count() > 1:
                budget_value_label = budget_layout.itemAt(1).widget()
                if budget_value_label:
                    budget_value_label.setText(f"${budget_remaining:.2f}")
            
            # Update transactions card
            transactions_layout = self.transactions_card.layout()
            if transactions_layout and transactions_layout.count() > 1:
                transactions_value_label = transactions_layout.itemAt(1).widget()
                if transactions_value_label:
                    transactions_value_label.setText(str(len(transactions)))
            # Update income card
            income_layout = self.income_card.layout()
            if income_layout and income_layout.count() > 1:
                income_value_label = income_layout.itemAt(1).widget()
                if income_value_label:
                    income_value_label.setText(f"${total_income:.2f}")
            # Update net card
            net_layout = self.net_card.layout()
            if net_layout and net_layout.count() > 1:
                net_value_label = net_layout.itemAt(1).widget()
                if net_value_label:
                    net_value_label.setText(f"${budget_remaining:.2f}")
            
            # Update categories card
            if hasattr(self, 'categories_card'):
                categories_layout = self.categories_card.layout()
                if categories_layout and categories_layout.count() > 1:
                    categories_value_label = categories_layout.itemAt(1).widget()
                    if categories_value_label:
                        categories_value_label.setText(str(category_count))
        except Exception as e:
            print(f"Error updating dashboard stats: {e}")
        
        # Update recent activity if there are transactions
        if transactions:
            recent_txns = sorted(transactions, key=lambda t: t.date, reverse=True)[:5]
            activity_html = "<h4 style='color: #27ae60;'>Recent Transactions</h4>"
            for txn in recent_txns:
                amount_color = "#e74c3c" if txn.amount < 0 else "#27ae60"
                amount_sign = "-" if txn.amount < 0 else "+"
                activity_html += f"""
                <p style='color: #2c3e50; margin: 5px 0;'>
                    <strong>{txn.date.strftime('%m/%d')}:</strong> {txn.description[:30]}...
                    <span style='color: {amount_color}; font-weight: bold;'>
                        {amount_sign}${abs(txn.amount):.2f}
                    </span>
                    <span style='color: #7f8c8d; font-size: 11px;'> ({txn.category})</span>
                </p>
                """
            activity_html += "<p style='color: #6c757d; font-size: 12px;'>Upload more statements to see complete history</p>"
            self.recent_transactions_label.setText(activity_html)
        else:
            self.recent_transactions_label.setText("""
            <h4 style="color: #6c757d;">No recent transactions</h4>
            <p style="color: #6c757d;">Upload your first bank statement to start tracking your spending!</p>
            <p style="color: #6c757d; font-size: 12px;">Supported formats: CSV</p>
            """)

        # Budget alerts
        try:
            from datetime import datetime as _dt
            if getattr(self.current_user, 'monthly_spending_limit', None):
                # compute current month spending
                now = _dt.now()
                month_spend = sum(
                    abs(t.amount) for t in transactions
                    if (t.amount < 0 and t.date.year == now.year and t.date.month == now.month)
                )
                limit = float(self.current_user.monthly_spending_limit)
                if limit > 0:
                    ratio = (float(month_spend) / limit) * 100.0
                    if ratio >= 100:
                        self.notify.emit("You have reached your monthly spending limit.", "warning")
                    elif ratio >= 75:
                        self.notify.emit(f"You have used {ratio:.0f}% of your monthly spending limit.", "info")

            # Upcoming subscriptions (Luke fields)
            upcoming = 0
            try:
                now = _dt.now()
                for t in transactions:
                    nd = getattr(t, 'next_due_date', None)
                    is_sub = getattr(t, 'is_subscription', False)
                    if is_sub and nd and (0 <= (nd - now).days <= 14):
                        upcoming += 1
            except Exception:
                pass
            if upcoming > 0:
                self.notify.emit(f"{upcoming} subscription payment(s) due soon.", "warning")
        except Exception:
            pass

    def update_streak_badge(self):
        try:
            if not self.current_user or not self.user_manager:
                return
            streak = self.user_manager.recompute_goal_streak(self.current_user.username)
            if streak and streak > 0:
                self.streak_label.setText(f"🔥 Goal streak: {streak} month(s) in a row")
            else:
                self.streak_label.setText("")
        except Exception:
            self.streak_label.setText("")
