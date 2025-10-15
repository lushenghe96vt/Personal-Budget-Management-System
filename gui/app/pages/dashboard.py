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
    QScrollArea
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
from fileUpload.fileUpload import upload_statement
from models import User


class DashboardPage(QWidget):
    """Main dashboard page widget"""
    
    # Signals for communication with main window
    show_spending_analysis = pyqtSignal()
    show_transactions = pyqtSignal()
    show_budget_settings = pyqtSignal()
    show_profile = pyqtSignal()  # Signal to show profile page
    transactions_updated = pyqtSignal()  # Signal when transactions are updated
    
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
        
        # Welcome section with user name
        welcome_text = "Welcome to your Personal Budget Dashboard!"
        if self.current_user:
            welcome_text = f"Welcome back, {self.current_user.first_name}!"
        
        welcome_label = QLabel(welcome_text)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_font = QFont()
        welcome_font.setPointSize(24)
        welcome_font.setBold(True)
        welcome_label.setFont(welcome_font)
        welcome_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(welcome_label)
        
        # Navigation menu bar
        self.create_navigation_menu(layout)
        
        # Quick stats section
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
        
        # Update stats with current user data
        self.update_dashboard_stats()
        
        # Quick actions section
        actions_label = QLabel("Quick Actions")
        actions_font = QFont()
        actions_font.setPointSize(18)
        actions_font.setBold(True)
        actions_label.setFont(actions_font)
        actions_label.setStyleSheet("color: #2c3e50; margin-top: 30px;")
        layout.addWidget(actions_label)
        
        actions_layout = QHBoxLayout()
        
        # Upload Statement Button
        upload_button = QPushButton("📄 Upload Bank Statement")
        upload_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 15px 25px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        upload_button.clicked.connect(self.upload_bank_statement)
        actions_layout.addWidget(upload_button)
        
        # View Transactions Button
        transactions_button = QPushButton("💳 View Transactions")
        transactions_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 15px 25px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        transactions_button.clicked.connect(self.show_transactions.emit)
        actions_layout.addWidget(transactions_button)
        
        # Set Budget Button
        budget_button = QPushButton("💰 Set Budget")
        budget_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 15px 25px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        budget_button.clicked.connect(self.show_budget_settings.emit)
        actions_layout.addWidget(budget_button)
        
        # Spending Analysis Button
        analysis_button = QPushButton("📊 Spending Analysis")
        analysis_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 15px 25px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        analysis_button.clicked.connect(self.show_spending_analysis.emit)
        actions_layout.addWidget(analysis_button)
        
        # Add second row for more buttons
        actions_layout2 = QHBoxLayout()
        
        # My Profile Button
        profile_button = QPushButton("👤 My Profile")
        profile_button.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                padding: 15px 25px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        profile_button.clicked.connect(self.show_profile)
        actions_layout2.addWidget(profile_button)
        
        actions_layout2.addStretch()
        
        layout.addLayout(actions_layout)
        layout.addLayout(actions_layout2)
        
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
        
        # Coming soon features
        features_label = QLabel("Coming Soon Features")
        features_font = QFont()
        features_font.setPointSize(18)
        features_font.setBold(True)
        features_label.setFont(features_font)
        features_label.setStyleSheet("color: #2c3e50; margin-top: 30px;")
        layout.addWidget(features_label)
        
        features_info = QLabel("""
        <div style="background-color: #e8f4f8; border: 1px solid #bee5eb; border-radius: 8px; padding: 20px; color: #0c5460;">
            <h4>Dashboard Features Coming Soon:</h4>
            <ul>
                <li><strong>Spending Categories:</strong> Visualize your expenses with interactive pie charts</li>
                <li><strong>Monthly Trends:</strong> Track your spending patterns over time</li>
                <li><strong>Budget Goals:</strong> Set and monitor your monthly spending limits</li>
                <li><strong>Transaction Management:</strong> Add notes and modify categories</li>
                <li><strong>Reports:</strong> Export your data for tax preparation</li>
                <li><strong>Notifications:</strong> Get alerts for budget limits and subscriptions</li>
            </ul>
        </div>
        """)
        features_info.setWordWrap(True)
        layout.addWidget(features_info)
        
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
            rows = upload_statement(file_path)
            
            if not rows:
                progress.close()
                QMessageBox.warning(self, "Error", "Failed to read CSV file or file is empty")
                return
            
            # Step 2: Convert to Transaction objects using Luke's dicts_to_transactions
            progress.setLabelText("Converting to transactions...")
            transactions = dicts_to_transactions(
                rows,
                source_name="user-upload",
                source_upload_id=f"upload-{datetime.now().isoformat(timespec='seconds')}"
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
                # Update current user object
                self.current_user.transactions.extend(transactions)
                
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
            else:
                QMessageBox.critical(self, "Error", f"Failed to save transactions: {message}")
                
        except Exception as e:
            if 'progress' in locals():
                progress.close()
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to process bank statement:\n{str(e)}\n\n"
                f"Please ensure the CSV file is in the correct format."
            )
    
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
        if hasattr(self, 'layout') and self.layout().count() > 0:
            welcome_widget = self.layout().itemAt(0).widget()
            if isinstance(welcome_widget, QLabel):
                welcome_text = f"Welcome back, {user.first_name}!"
                welcome_widget.setText(welcome_text)
        
        # Update dashboard stats
        self.update_dashboard_stats()
    
    def update_dashboard_stats(self):
        """Update dashboard statistics with real transaction data"""
        if not self.current_user or not hasattr(self, 'spending_card'):
            return
        
        transactions = self.current_user.transactions
        
        # Calculate total spending (negative amounts)
        total_spending = sum(abs(t.amount) for t in transactions if t.amount < 0)
        
        # Calculate total income (positive amounts)
        total_income = sum(t.amount for t in transactions if t.amount > 0)
        
        # Calculate budget remaining (simple calculation)
        budget_remaining = total_income - total_spending
        
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
