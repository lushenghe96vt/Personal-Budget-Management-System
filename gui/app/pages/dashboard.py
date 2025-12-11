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
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, 
    QMenu, QMenuBar, QFileDialog, QMessageBox, QFrame, QProgressDialog,
    QScrollArea, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QAction, QPixmap, QIcon
from pathlib import Path
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.categorize_edit import dicts_to_transactions, auto_categorize, CategoryRules
from core.fileUpload import upload_statement
from core.analytics import (
    calculate_total_spending, calculate_total_income, calculate_net_balance,
    get_top_spending_categories, get_period_summary, check_spending_limit
)
from core.models import Transaction
from ..models.user import User
from ..style import Styles
from gui.widgets.components import PageHeader, SectionCard, StyledButton
from gui.widgets.metric_card import MetricCard


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
        self._alert_state = {"monthly": False, "weekly": False}
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dashboard UI - Real dashboard with KPIs, quick actions, and insights"""
        # Create scroll area for the entire dashboard
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Create main widget for scroll area
        main_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(24)
        layout.setContentsMargins(24, 24, 24, 24)

        # Streak badge (shown if > 0)
        self.streak_label = QLabel("")
        self.streak_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.streak_label.setStyleSheet(Styles.LABEL_SECONDARY)
        layout.addWidget(self.streak_label)

        # Overview heading for metrics grid
        overview_heading = QLabel("Account Overview")
        overview_heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overview_heading.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 20px;
                font-weight: 600;
            }
        """)
        layout.addWidget(overview_heading)

        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(16)
        metrics_grid.setContentsMargins(0, 0, 0, 0)
        for i in range(3):
            metrics_grid.setColumnStretch(i, 1)
        
        # Metric cards (9 total, arranged 3x3)
        self.spending_card = MetricCard("Total Spending", "$0.00", "danger")
        self.income_card = MetricCard("Total Income", "$0.00", "success")
        self.net_card = MetricCard("Net Balance", "$0.00", "info")
        self.transactions_card = MetricCard("Transactions", "0", "info")
        self.categories_card = MetricCard("Active Categories", "0", "neutral")
        self.top_category_card = MetricCard("Top Spending Category", "No data", "info", small_font=True)
        self.budget_status_card = MetricCard("Budget Status", "No limit set", "neutral", small_font=True)
        self.goal_streak_card = MetricCard("Savings Streak", "No data", "neutral", small_font=True)
        self.weekly_progress_card = MetricCard("Weekly Spending", "No data", "neutral", small_font=True)

        metrics_grid.addWidget(self.spending_card, 0, 0)
        metrics_grid.addWidget(self.income_card, 0, 1)
        metrics_grid.addWidget(self.net_card, 0, 2)

        metrics_grid.addWidget(self.transactions_card, 1, 0)
        metrics_grid.addWidget(self.categories_card, 1, 1)
        metrics_grid.addWidget(self.top_category_card, 1, 2)

        metrics_grid.addWidget(self.budget_status_card, 2, 0)
        metrics_grid.addWidget(self.goal_streak_card, 2, 1)
        metrics_grid.addWidget(self.weekly_progress_card, 2, 2)

        layout.addLayout(metrics_grid)
        
        # Quick Actions section - white card matching metric cards with margins
        actions_widget = QWidget()
        actions_widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 1px solid #e6e8eb;
                border-radius: 12px;
            }
        """)
        actions_container = QVBoxLayout(actions_widget)
        actions_container.setContentsMargins(20, 20, 20, 20)
        actions_container.setSpacing(16)
        
        # Title - clean style without border
        actions_title = QLabel("Quick Actions")
        actions_title.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 14px;
                font-weight: bold;
                padding: 0px;
                border: none;
                background: transparent;
            }
        """)
        actions_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        actions_container.addWidget(actions_title)
        
        # Buttons layout with improved styling
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)
        actions_layout.setContentsMargins(0, 4, 0, 0)  # Small top margin for better spacing
        
        upload_button = StyledButton("Upload Bank Statement", StyledButton.PRIMARY)
        upload_button.setMinimumHeight(42)
        upload_button.setStyleSheet("""
            QPushButton {
                background-color: #2f6fed;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #245add;
            }
            QPushButton:pressed {
                background-color: #1e4fc7;
            }
        """)
        upload_button.clicked.connect(self.upload_bank_statement)
        actions_layout.addWidget(upload_button)
        
        view_transactions_btn = StyledButton("View All Transactions", StyledButton.SECONDARY)
        view_transactions_btn.setMinimumHeight(42)
        view_transactions_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f3f8;
                color: #2c3e50;
                border: 1px solid #e6e8eb;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e6eaf1;
                border-color: #d0d7e0;
            }
            QPushButton:pressed {
                background-color: #dce2eb;
            }
        """)
        view_transactions_btn.clicked.connect(self.show_transactions.emit)
        actions_layout.addWidget(view_transactions_btn)
        
        view_analysis_btn = StyledButton("View Analysis", StyledButton.SECONDARY)
        view_analysis_btn.setMinimumHeight(42)
        view_analysis_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f3f8;
                color: #2c3e50;
                border: 1px solid #e6e8eb;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e6eaf1;
                border-color: #d0d7e0;
            }
            QPushButton:pressed {
                background-color: #dce2eb;
            }
        """)
        view_analysis_btn.clicked.connect(self.show_spending_analysis.emit)
        actions_layout.addWidget(view_analysis_btn)
        
        export_btn = StyledButton("Export Dashboard", StyledButton.NEUTRAL)
        export_btn.setMinimumHeight(42)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #7f8c8d;
                border: 1px solid #e6e8eb;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f5f7fb;
                border-color: #d0d7e0;
                color: #2c3e50;
            }
            QPushButton:pressed {
                background-color: #ecf0f3;
            }
        """)
        from core.exportWin import save_window_dialog
        export_btn.clicked.connect(lambda: save_window_dialog(self))
        actions_layout.addWidget(export_btn)
        
        actions_layout.addStretch()
        actions_container.addLayout(actions_layout)
        
        # Add widget with spacing to match metric cards (they're in rows with spacing)
        # The main layout already has 24px margins, so this will align with metric cards
        layout.addWidget(actions_widget)
        
        # Recent Transactions section - white card matching metric cards
        recent_widget = QWidget()
        recent_widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 1px solid #e6e8eb;
                border-radius: 12px;
            }
        """)
        recent_container = QVBoxLayout(recent_widget)
        recent_container.setContentsMargins(20, 20, 20, 20)
        recent_container.setSpacing(16)
        
        # Title - clean style without border
        recent_title = QLabel("Recent Transactions")
        recent_title.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 14px;
                font-weight: bold;
                padding: 0px;
                border: none;
                background: transparent;
            }
        """)
        recent_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        recent_container.addWidget(recent_title)
        
        # Content with better styling
        self.recent_transactions_label = QLabel("No recent transactions")
        self.recent_transactions_label.setWordWrap(True)
        self.recent_transactions_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 13px;
                padding: 8px 0px;
                border: none;
                background: transparent;
                line-height: 1.5;
            }
        """)
        recent_container.addWidget(self.recent_transactions_label)
        
        # View all button with better styling
        view_all_button = StyledButton("View All Transactions", StyledButton.TEXT)
        view_all_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #2f6fed;
                border: none;
                padding: 8px 12px;
                text-align: center;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                color: #245add;
                background-color: #f0f7ff;
                border-radius: 6px;
            }
            QPushButton:pressed {
                background-color: #e6f2ff;
            }
        """)
        view_all_button.clicked.connect(self.show_transactions.emit)
        recent_container.addWidget(view_all_button)

        layout.addWidget(recent_widget)

        layout.addStretch()
        main_widget.setLayout(layout)

        # Set the scroll area's widget
        scroll_area.setWidget(main_widget)

        # Set the scroll area as the main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
        
        # Update stats with current user data
        self.update_dashboard_stats()
    
    # Removed create_stat_card - now using MetricCard component
    
    def create_navigation_menu(self, parent_layout):
        """Create navigation menu bar"""
        nav_layout = QHBoxLayout()

        # Menu button (hamburger style)
        menu_button = QPushButton("☰ Menu")
        menu_button.setStyleSheet(Styles.BUTTON_SECONDARY)

        # Create menu
        menu = QMenu(self)
        menu.setStyleSheet(Styles.MENU)

        # Add menu actions
        dashboard_action = QAction("Dashboard", self)
        dashboard_action.triggered.connect(lambda: self.switch_to_page("dashboard"))
        menu.addAction(dashboard_action)

        transactions_action = QAction("Transactions", self)
        transactions_action.triggered.connect(self.show_transactions.emit)
        menu.addAction(transactions_action)

        budget_action = QAction("Budget", self)
        budget_action.triggered.connect(self.show_budget_settings.emit)
        menu.addAction(budget_action)

        analysis_action = QAction("Analysis", self)
        analysis_action.triggered.connect(self.show_spending_analysis.emit)
        menu.addAction(analysis_action)

        menu.addSeparator()

        settings_action = QAction("Settings", self)
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

            # Processing file: {file_path}
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
            # CSV processing completed. Found {len(rows) if rows else 0} rows

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
                
                # Reload user from manager to get updated transactions (don't extend manually - already added by add_transactions)
                self.current_user = self.user_manager.get_user(self.current_user.username)
                
                # Dashboard stats will be updated automatically
                
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
        """Update the current user (welcome message is now in sidebar)"""
        self.current_user = user
        self._alert_state = {
            "monthly_threshold": False,
            "monthly_limit": False,
            "weekly_threshold": False,
            "weekly_limit": False,
        }
        
        # Update dashboard stats
        self.update_dashboard_stats()
        self.update_streak_badge()
    
    
    def update_dashboard_stats(self):
        """Update dashboard statistics with real transaction data using analytics"""
        if not self.current_user or not hasattr(self, 'spending_card'):
            return

        try:
            all_transactions = self.current_user.transactions or []
            
            # Use all transactions (no filtering on dashboard)
            transactions = all_transactions
            
            # Use analytics functions for calculations
            total_spending = calculate_total_spending(transactions)
            total_income = calculate_total_income(transactions)
            net_balance = calculate_net_balance(transactions)
            
            # Get unique categories count
            categories = set(t.category for t in transactions if t.category)
            category_count = len(categories)

            # Update MetricCard components using their set_value method
            self.spending_card.set_value(f"${float(total_spending):.2f}")
            self.income_card.set_value(f"${float(total_income):.2f}")
            self.net_card.set_value(f"${float(net_balance):.2f}")
            self.transactions_card.set_value(str(len(transactions)))
            self.categories_card.set_value(str(category_count))

            streak_count = getattr(self.current_user, "goal_streak_count", 0)
            self._update_streak_card(streak_count)
            self._update_weekly_card(transactions)
            
            # Update top spending category insight - using MetricCard
            if transactions:
                top_categories = get_top_spending_categories(transactions, limit=1)
                if top_categories:
                    category, amount = top_categories[0]
                    self.top_category_card.set_value(f"{category}: ${float(amount):.2f}")
                    self.top_category_card.set_variant("info")
                else:
                    self.top_category_card.set_value("No spending data")
                    self.top_category_card.set_variant("neutral")
            else:
                self.top_category_card.set_value("No data")
                self.top_category_card.set_variant("neutral")
            
            # Update budget status - using MetricCard and proper analytics function
            # Budget status shows ALL TIME spending vs adjusted limit (monthly limit × number of months)
            try:
                from decimal import Decimal
                from core.analytics.months import group_transactions_by_month
                spending_limit = getattr(self.current_user, 'monthly_spending_limit', None)
                
                if spending_limit is None or spending_limit == 0:
                    self.budget_status_card.set_value("No limit set")
                    self.budget_status_card.set_variant("neutral")
                else:
                    # Calculate number of months in all transactions
                    monthly_groups = group_transactions_by_month(transactions)
                    num_months = len(monthly_groups) if monthly_groups else 1
                    
                    # Adjust limit for all time: monthly limit × number of months
                    if not isinstance(spending_limit, Decimal):
                        spending_limit = Decimal(str(spending_limit))
                    adjusted_limit = spending_limit * Decimal(str(num_months))
                    
                    # Use check_spending_limit with all transactions and adjusted limit
                    spending_status = check_spending_limit(
                        transactions, 
                        adjusted_limit
                    )
                    
                    if spending_status['limit'] is not None and spending_status['limit'] > 0:
                        used_percent = spending_status['used_percent']
                        remaining = float(spending_status['remaining'])
                        spent = float(spending_status['spent'])
                        
                        # Show percentage with month count
                        if spent == 0:
                            # No spending yet
                            self.budget_status_card.set_value(f"0% used ({num_months} months)")
                            self.budget_status_card.set_variant("success")
                        elif spending_status['over_limit']:
                            # Show over limit message with percentage and month count
                            self.budget_status_card.set_value(f"{used_percent}% ({num_months} months, Over by ${abs(remaining):.2f})")
                            self.budget_status_card.set_variant("danger")
                        elif used_percent >= 75:
                            self.budget_status_card.set_value(f"{used_percent}% used ({num_months} months)")
                            self.budget_status_card.set_variant("warning")
                        else:
                            self.budget_status_card.set_value(f"{used_percent}% used ({num_months} months)")
                            self.budget_status_card.set_variant("success")
                    else:
                        self.budget_status_card.set_value("No limit set")
                        self.budget_status_card.set_variant("neutral")
            except Exception as e:
                # Silently handle errors to prevent crashes
                self.budget_status_card.set_value("No limit set")
                self.budget_status_card.set_variant("neutral")
            # Update recent transactions with error handling
            if transactions:
                try:
                    recent_txns = sorted(
                        [t for t in transactions if hasattr(t, 'date') and t.date],
                        key=lambda t: t.date, reverse=True
                    )[:5]
                    if recent_txns:
                        activity_text = ""
                        for txn in recent_txns:
                            try:
                                amount = getattr(txn, 'amount', 0) or 0
                                amount_color = "#e74c3c" if amount < 0 else "#27ae60"
                                amount_sign = "-" if amount < 0 else "+"
                                date_str = txn.date.strftime('%m/%d') if hasattr(txn, 'date') and txn.date else "N/A"
                                desc = getattr(txn, 'description', '') or 'N/A'
                                desc_short = desc[:40] + ('...' if len(desc) > 40 else '')
                                category = getattr(txn, 'category', '') or 'Uncategorized'
                                activity_text += f"{date_str}: {desc_short} - {amount_sign}${abs(amount):.2f} ({category})\n"
                            except Exception:
                                continue
                        self.recent_transactions_label.setText(activity_text.strip() if activity_text.strip() else "No recent transactions")
                    else:
                        self.recent_transactions_label.setText("No recent transactions")
                except Exception:
                    self.recent_transactions_label.setText("No recent transactions")
            else:
                self.recent_transactions_label.setText("No recent transactions. Upload your first bank statement to start tracking!")
        except Exception as e:
            # Silently handle errors to prevent crashes
            pass
        
        self._emit_budget_alerts(transactions)

    def update_streak_badge(self):
        try:
            if not self.current_user or not self.user_manager:
                return
            streak = self.user_manager.recompute_goal_streak(self.current_user.username)
            if streak and streak > 0:
                self.streak_label.setText(f"Goal streak: {streak} month(s) in a row")
            else:
                self.streak_label.setText("")
            self._update_streak_card(streak)
        except Exception:
            self.streak_label.setText("")

    def _update_streak_card(self, streak: int):
        if not hasattr(self, "goal_streak_card"):
            return
        if streak and streak > 0:
            self.goal_streak_card.set_value(f"{streak} month(s)")
            self.goal_streak_card.set_variant("success")
        else:
            self.goal_streak_card.set_value("No active streak")
            self.goal_streak_card.set_variant("neutral")

    def _update_weekly_card(self, transactions: list[Transaction]):
        if not hasattr(self, "weekly_progress_card"):
            return
        weekly_limit = getattr(self.current_user, "weekly_spending_limit", None)
        if not weekly_limit or weekly_limit <= 0:
            self.weekly_progress_card.set_value("No weekly limit")
            self.weekly_progress_card.set_variant("neutral")
            return

        now = datetime.now()
        week_start = datetime(now.year, now.month, now.day) - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=7)

        spent = 0.0
        for txn in transactions:
            if getattr(txn, "amount", 0) < 0 and getattr(txn, "date", None) and week_start <= txn.date < week_end:
                spent += float(abs(txn.amount))

        ratio = (spent / weekly_limit) * 100 if weekly_limit else 0
        self.weekly_progress_card.set_value(f"${spent:.2f} of ${weekly_limit:.2f}")
        if ratio >= 100:
            self.weekly_progress_card.set_variant("danger")
        elif ratio >= 75:
            self.weekly_progress_card.set_variant("warning")
        else:
            self.weekly_progress_card.set_variant("info")

    def _emit_budget_alerts(self, transactions: list[Transaction]):
        if not self.current_user:
            return
        try:
            now = datetime.now()

            def within_current_month(txn: Transaction) -> bool:
                return (
                    hasattr(txn, "date")
                    and txn.date
                    and txn.date.year == now.year
                    and txn.date.month == now.month
                )

            def spending_sum(predicate):
                total = 0.0
                for txn in transactions:
                    if getattr(txn, "amount", 0) < 0 and predicate(txn):
                        total += float(abs(txn.amount))
                return total

            monthly_limit = getattr(self.current_user, "monthly_spending_limit", None)
            monthly_threshold = getattr(self.current_user, "monthly_alert_threshold_pct", None) or 75
            if monthly_limit and monthly_limit > 0:
                month_spend = spending_sum(within_current_month)
                ratio = (month_spend / float(monthly_limit)) * 100.0 if monthly_limit else 0
                if ratio >= 100 and not self._alert_state.get("monthly_limit", False):
                    self.notify.emit("You have reached your monthly spending limit.", "warning")
                    self._alert_state["monthly_limit"] = True
                elif ratio >= monthly_threshold and not self._alert_state.get("monthly_threshold", False):
                    self.notify.emit(f"You have used {ratio:.0f}% of your monthly spending limit.", "info")
                    self._alert_state["monthly_threshold"] = True
                elif ratio < monthly_threshold:
                    self._alert_state["monthly_threshold"] = False
                    self._alert_state["monthly_limit"] = False

            weekly_limit = getattr(self.current_user, "weekly_spending_limit", None)
            weekly_threshold = getattr(self.current_user, "weekly_alert_threshold_pct", None) or 75
            if weekly_limit and weekly_limit > 0:
                week_start = datetime(now.year, now.month, now.day) - timedelta(days=now.weekday())
                week_end = week_start + timedelta(days=7)

                def within_week(txn: Transaction) -> bool:
                    return hasattr(txn, "date") and txn.date and week_start <= txn.date < week_end

                week_spend = spending_sum(within_week)
                week_ratio = (week_spend / float(weekly_limit)) * 100.0 if weekly_limit else 0
                if week_ratio >= 100 and not self._alert_state.get("weekly_limit", False):
                    self.notify.emit("You have reached your weekly spending limit.", "warning")
                    self._alert_state["weekly_limit"] = True
                elif week_ratio >= weekly_threshold and not self._alert_state.get("weekly_threshold", False):
                    self.notify.emit(f"You have used {week_ratio:.0f}% of your weekly spending limit.", "info")
                    self._alert_state["weekly_threshold"] = True
                elif week_ratio < weekly_threshold:
                    self._alert_state["weekly_threshold"] = False
                    self._alert_state["weekly_limit"] = False

            upcoming = 0
            try:
                for txn in transactions:
                    if not hasattr(txn, "next_due_date") or not getattr(txn, "is_subscription", False):
                        continue
                    nd = getattr(txn, "next_due_date", None)
                    if nd and (0 <= (nd - now).days <= 14):
                        upcoming += 1
            except Exception:
                pass
            if upcoming > 0:
                self.notify.emit(f"{upcoming} subscription payment(s) due soon.", "warning")
        except Exception:
            pass
