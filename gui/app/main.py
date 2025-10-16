"""
main.py
Personal Budget Management System - Main Application Entry Point
Author: Ankush
Date: 10/11/25

Description:
  Main application window that manages authentication, navigation, and page switching.
  Orchestrates the entire GUI application and integrates all backend components.

Implements:
  - User authentication and session management
  - Page navigation and menu system
  - Integration with backend components (Jason's CSV parsing, Luke's categorization)
  - Real-time data synchronization across pages
"""

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMenuBar, QStatusBar, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import UserManager, User
from pages.auth import AuthWidget
from pages.profile import ProfilePage
from pages.dashboard import DashboardPage
from pages.transactions import TransactionsPage
from pages.budgets import BudgetAnalysisPage


class MainWindow(QMainWindow):
    """Main application window with authentication and main app functionality"""
    
    def __init__(self):
        super().__init__()
        self.user_manager = UserManager()
        self.current_user = None
        self.setup_ui()
        self.show_auth()
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("Personal Budget Management System")
        self.resize(1000, 700)
        self.setMinimumSize(800, 600)
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
        """)
        
        # Create stacked widget for different views
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create authentication widget
        self.auth_widget = AuthWidget(self.user_manager)
        self.auth_widget.auth_successful.connect(self.handle_login_success)
        self.stacked_widget.addWidget(self.auth_widget)
        
        # Create main application widget
        self.main_app_widget = QMainWindow()
        self.main_app_widget.setWindowTitle("Personal Budget Management System - Dashboard")
        self.stacked_widget.addWidget(self.main_app_widget)
        
        # Setup main app UI (will be populated after login)
        self.setup_main_app_ui()
        
        # Initialize page references
        self.transactions_page = None
        self.budget_analysis_page = None
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def setup_main_app_ui(self):
        """Setup the main application UI (called after login)"""
        # Create menu bar on the main window
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        logout_action = QAction('Logout', self)
        logout_action.triggered.connect(self.handle_logout)
        file_menu.addAction(logout_action)
        
        # User menu
        user_menu = menubar.addMenu('Account')
        
        profile_action = QAction('My Profile', self)
        profile_action.triggered.connect(self.show_profile)
        user_menu.addAction(profile_action)
        
        # Navigation menu
        nav_menu = menubar.addMenu('Navigation')
        
        dashboard_action = QAction('Dashboard', self)
        dashboard_action.triggered.connect(self.show_dashboard)
        nav_menu.addAction(dashboard_action)
        
        transactions_action = QAction('Transactions', self)
        transactions_action.triggered.connect(self.handle_show_transactions)
        nav_menu.addAction(transactions_action)
        
        analysis_action = QAction('Budget Analysis', self)
        analysis_action.triggered.connect(self.handle_show_spending_analysis)
        nav_menu.addAction(analysis_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Create pages for the main app
        self.create_main_app_pages()
    
    def create_main_app_pages(self):
        """Create the main application pages"""
        # Create a stacked widget for main app pages
        self.main_pages = QStackedWidget()
        self.main_app_widget.setCentralWidget(self.main_pages)
        
        # Dashboard page
        self.dashboard_page = DashboardPage()
        self.dashboard_page.show_spending_analysis.connect(self.handle_show_spending_analysis)
        self.dashboard_page.show_transactions.connect(self.handle_show_transactions)
        self.dashboard_page.show_budget_settings.connect(self.handle_show_budget_settings)
        self.dashboard_page.show_profile.connect(self.show_profile)
        self.dashboard_page.transactions_updated.connect(self.handle_transactions_updated)
        self.main_pages.addWidget(self.dashboard_page)
        
        # Profile page
        self.profile_page = None  # Will be created when needed
    
    def show_auth(self):
        """Show authentication screen"""
        self.stacked_widget.setCurrentWidget(self.auth_widget)
        self.setWindowTitle("Personal Budget Management System - Login")
        self.status_bar.showMessage("Please login to continue")
    
    def show_main_app(self):
        """Show main application"""
        self.stacked_widget.setCurrentWidget(self.main_app_widget)
        self.setWindowTitle(f"Personal Budget Management System - Welcome, {self.current_user.first_name}")
        self.status_bar.showMessage(f"Logged in as {self.current_user.username}")
    
    def handle_login_success(self, user: User):
        """Handle successful login"""
        self.current_user = user
        self.show_main_app()
        
        # Update dashboard with current user and user manager
        self.dashboard_page.current_user = user
        self.dashboard_page.user_manager = self.user_manager
        self.dashboard_page.set_current_user(user)
        
        # Show welcome message
        QMessageBox.information(
            self, 
            "Welcome!", 
            f"Welcome back, {user.first_name}!\n\nYou are now logged into your Personal Budget Management account."
        )
    
    def handle_logout(self):
        """Handle user logout"""
        reply = QMessageBox.question(
            self, 
            'Logout', 
            'Are you sure you want to logout?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.current_user = None
            self.show_auth()
    
    def show_profile(self):
        """Show user profile page"""
        if self.current_user is None:
            return
        
        # Create profile page if it doesn't exist or user changed
        if self.profile_page is None:
            self.profile_page = ProfilePage(self.user_manager, self.current_user)
            self.profile_page.profile_updated.connect(self.handle_profile_updated)
            self.profile_page.go_back_to_dashboard.connect(self.show_dashboard)
            self.main_pages.addWidget(self.profile_page)
        
        # Update profile page with current user data
        self.profile_page.current_user = self.current_user
        self.profile_page.load_user_data()
        
        # Switch to profile page
        self.main_pages.setCurrentWidget(self.profile_page)
    
    def handle_profile_updated(self, updated_user: User):
        """Handle profile update"""
        self.current_user = updated_user
        self.setWindowTitle(f"Personal Budget Management System - Welcome, {self.current_user.first_name}")
        self.status_bar.showMessage(f"Profile updated for {self.current_user.username}")
    
    def handle_show_spending_analysis(self):
        """Handle request to show spending analysis"""
        if self.current_user is None:
            return
        
        # Create budget analysis page if it doesn't exist
        if self.budget_analysis_page is None:
            self.budget_analysis_page = BudgetAnalysisPage(self.current_user, self.user_manager)
            self.budget_analysis_page.go_back_to_dashboard.connect(self.show_dashboard)
            self.main_pages.addWidget(self.budget_analysis_page)
        
        # Update with current user data
        self.budget_analysis_page.user = self.current_user
        self.budget_analysis_page.update_analysis()
        
        # Switch to budget analysis page
        self.main_pages.setCurrentWidget(self.budget_analysis_page)
    
    def handle_show_transactions(self):
        """Handle request to show transactions"""
        if self.current_user is None:
            return
        
        # Create transactions page if it doesn't exist
        if self.transactions_page is None:
            self.transactions_page = TransactionsPage(self.current_user, self.user_manager)
            self.transactions_page.transaction_updated.connect(self.handle_transactions_updated)
            self.transactions_page.go_back_to_dashboard.connect(self.show_dashboard)
            self.main_pages.addWidget(self.transactions_page)
        
        # Update with current user data
        self.transactions_page.user = self.current_user
        self.transactions_page.refresh_table()
        
        # Switch to transactions page
        self.main_pages.setCurrentWidget(self.transactions_page)
    
    def handle_show_budget_settings(self):
        """Handle request to show budget settings"""
        QMessageBox.information(
            self,
            "Budget Settings",
            "Budget settings feature will be implemented in future sprints.\n\nThis will include:\n- Set monthly budget limits\n- Create spending categories\n- Set budget goals\n- Configure notifications"
        )
    
    def handle_transactions_updated(self):
        """Handle when transactions are updated"""
        # Refresh dashboard stats
        if self.dashboard_page:
            self.dashboard_page.update_dashboard_stats()
        
        # Refresh budget analysis if it's currently shown
        if self.budget_analysis_page and self.main_pages.currentWidget() == self.budget_analysis_page:
            self.budget_analysis_page.update_analysis()
    
    def show_dashboard(self):
        """Show the dashboard page"""
        self.main_pages.setCurrentWidget(self.dashboard_page)
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Personal Budget Management System",
            """
            <h3>Personal Budget Management System</h3>
            <p><b>Team 8 Project</b></p>
            <p><b>Team Members:</b></p>
            <ul>
                <li>Jason Huang (Scrum Master)</li>
                <li>Sheng Lu</li>
                <li>Ankush Chaudhary</li>
                <li>Luke Graham</li>
            </ul>
            <p><b>Description:</b></p>
            <p>A comprehensive tool for personal finance management that makes budgeting less overwhelming and more approachable. Upload bank statements, track spending, set goals, and visualize your financial data.</p>
            <p><b>Features:</b></p>
            <ul>
                <li>Bank statement upload and auto-categorization</li>
                <li>Interactive budget visualization</li>
                <li>Spending trends and forecasting</li>
                <li>Goal tracking and notifications</li>
                <li>Export reports and tax preparation</li>
            </ul>
            """
        )



def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Personal Budget Management System")
    app.setApplicationVersion("1.0")
    
    # Set application style
    app.setStyleSheet("""
        QApplication {
            font-family: 'Segoe UI', Arial, sans-serif;
        }
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
