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

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QStatusBar, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QFont
import sys
import os
import argparse

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
from .models.user import UserManager, User
from .pages.auth import AuthWidget
from .pages.profile import ProfilePage
from .pages.dashboard import DashboardPage
from .pages.transactions import TransactionsPage
from .budgets import BudgetAnalysisPage
from .pages.settings import BudgetSettingsPage
from .widgets import NotificationBanner


class MainWindow(QMainWindow):
    """Main application window with authentication and main app functionality"""
    
    def __init__(self, dev_mode: bool = False):
        super().__init__()
        # Ensure we read/write users from gui/data/users.json
        data_dir = str(Path(__file__).resolve().parent.parent / "data")
        self.user_manager = UserManager(data_dir=data_dir)
        self.current_user = None
        self.dev_mode = dev_mode
        self.setup_ui()
        
        if dev_mode:
            # Auto-login with test user in dev mode
            self._auto_login_dev()
        else:
            self.show_auth()
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("Personal Budget Management System")
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
        self.budget_settings_page = None
        self.profile_page = None
        
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
        # Create a central container with a notification banner on top and pages below
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setSpacing(8)

        self.banner = NotificationBanner()
        container_layout.addWidget(self.banner)

        # Header
        header = self._build_header()
        container_layout.addWidget(header)

        # Body: sidebar + pages
        body = QWidget()
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(12)

        self.sidebar = self._build_sidebar()
        body_layout.addWidget(self.sidebar)

        # Main pages stack
        self.main_pages = QStackedWidget()
        body_layout.addWidget(self.main_pages, 1)
        body.setLayout(body_layout)
        container_layout.addWidget(body, 1)

        # Footer
        footer = self._build_footer()
        container_layout.addWidget(footer)

        container.setLayout(container_layout)
        self.main_app_widget.setCentralWidget(container)
        
        # Dashboard page
        self.dashboard_page = DashboardPage()
        self.dashboard_page.show_spending_analysis.connect(self.handle_show_spending_analysis)
        self.dashboard_page.show_transactions.connect(self.handle_show_transactions)
        self.dashboard_page.show_budget_settings.connect(self.handle_show_budget_settings)
        self.dashboard_page.show_profile.connect(self.show_profile)
        self.dashboard_page.transactions_updated.connect(self.handle_transactions_updated)
        self.dashboard_page.notify.connect(self._notify)
        self.main_pages.addWidget(self.dashboard_page)
        
        # Profile page
        self.profile_page = None  # Will be created when needed
    
    def _auto_login_dev(self):
        """Auto-login with test user in development mode"""
        test_username = "dev"
        test_password = "dev123"
        
        # Check if test user exists, create if not
        if not self.user_manager.user_exists(test_username):
            success, message = self.user_manager.create_user(
                username=test_username,
                email="dev@example.com",
                password=test_password,
                first_name="Dev",
                last_name="User"
            )
            if not success:
                print(f"Warning: Could not create dev user: {message}")
                self.show_auth()
                return
        
        # Authenticate and login
        success, message, user = self.user_manager.authenticate_user(test_username, test_password)
        if success and user:
            self.handle_login_success(user)
            self.status_bar.showMessage("DEV MODE: Auto-logged in as 'dev'")
        else:
            print(f"Warning: Could not auto-login: {message}")
            self.show_auth()
    
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
        # Reload user from manager to ensure fresh data
        self.current_user = self.user_manager.get_user(user.username)
        if not self.current_user:
            self.current_user = user
        
        self.show_main_app()
        
        # Clear and recreate pages to ensure fresh data for new user
        # This prevents showing old user's data
        if hasattr(self, 'dashboard_page') and self.dashboard_page:
            self.dashboard_page.current_user = None
        if hasattr(self, 'transactions_page') and self.transactions_page:
            self.transactions_page.user = None
        if hasattr(self, 'budget_analysis_page') and self.budget_analysis_page:
            self.budget_analysis_page.user = None
        if hasattr(self, 'budget_settings_page') and self.budget_settings_page:
            self.budget_settings_page.user = None
        if hasattr(self, 'profile_page') and self.profile_page:
            self.profile_page.current_user = None
        
        # Update dashboard with current user and user manager
        self.dashboard_page.current_user = self.current_user
        self.dashboard_page.user_manager = self.user_manager
        self.dashboard_page.set_current_user(self.current_user)
        
        # Update sidebar welcome message
        self._update_sidebar_welcome(self.current_user)
        
        # Show welcome notification
        self._notify("Welcome back, {}!".format(self.current_user.first_name), level="success")
    
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
            # Clear all page references to prevent showing old user data
            if hasattr(self, 'dashboard_page') and self.dashboard_page:
                self.dashboard_page.current_user = None
            if hasattr(self, 'transactions_page') and self.transactions_page:
                self.transactions_page.user = None
            if hasattr(self, 'budget_analysis_page') and self.budget_analysis_page:
                self.budget_analysis_page.user = None
            if hasattr(self, 'budget_settings_page') and self.budget_settings_page:
                self.budget_settings_page.user = None
            if hasattr(self, 'profile_page') and self.profile_page:
                self.profile_page.current_user = None
            
            # Clear current user
            self.current_user = None
            
            # Reset window title
            self.setWindowTitle("Personal Budget Management System")
            self.status_bar.showMessage("Logged out")
            
            # Show auth screen
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
        """Handle profile update - refresh all pages"""
        # Reload user data to ensure latest profile data
        self.current_user = self.user_manager.get_user(updated_user.username)
        self.setWindowTitle(f"Personal Budget Management System - Welcome, {self.current_user.first_name}")
        self.status_bar.showMessage(f"Profile updated for {self.current_user.username}")
        
        # Update sidebar welcome message
        self._update_sidebar_welcome(self.current_user)
        
        # Refresh dashboard
        if self.dashboard_page:
            self.dashboard_page.current_user = self.current_user
            self.dashboard_page.update_dashboard_stats()
    
    def handle_show_spending_analysis(self):
        """Handle request to show spending analysis"""
        if self.current_user is None:
            return
        
        # Reload user data to ensure latest transactions
        self.current_user = self.user_manager.get_user(self.current_user.username)
        
        # Create budget analysis page if it doesn't exist
        if self.budget_analysis_page is None:
            self.budget_analysis_page = BudgetAnalysisPage(self.current_user, self.user_manager)
            self.budget_analysis_page.go_back_to_dashboard.connect(self.show_dashboard)
            self.main_pages.addWidget(self.budget_analysis_page)
        
        # Update with current user data
        self.budget_analysis_page.user = self.current_user
        # Repopulate month filters with updated transactions
        if hasattr(self.budget_analysis_page, '_populate_month_filters'):
            self.budget_analysis_page._populate_month_filters()
        self.budget_analysis_page.update_analysis()
        
        # Switch to budget analysis page
        self.main_pages.setCurrentWidget(self.budget_analysis_page)
    
    def handle_show_transactions(self):
        """Handle request to show transactions"""
        if self.current_user is None:
            return
        
        try:
            # Reload user data to ensure latest transactions
            self.current_user = self.user_manager.get_user(self.current_user.username)
            
            # Create transactions page if it doesn't exist
            if self.transactions_page is None:
                self.transactions_page = TransactionsPage(self.current_user, self.user_manager)
                self.transactions_page.transaction_updated.connect(self.handle_transactions_updated)
                self.transactions_page.go_back_to_dashboard.connect(self.show_dashboard)
                self.main_pages.addWidget(self.transactions_page)
            else:
                # Check if user changed (compare usernames to avoid object comparison issues)
                old_username = getattr(self.transactions_page.user, 'username', None) if self.transactions_page.user else None
                new_username = getattr(self.current_user, 'username', None) if self.current_user else None
                
                if old_username != new_username:
                    # User changed - recreate page
                    self.main_pages.removeWidget(self.transactions_page)
                    self.transactions_page.deleteLater()
                    self.transactions_page = None
                    
                    self.transactions_page = TransactionsPage(self.current_user, self.user_manager)
                    self.transactions_page.transaction_updated.connect(self.handle_transactions_updated)
                    self.transactions_page.go_back_to_dashboard.connect(self.show_dashboard)
                    self.main_pages.addWidget(self.transactions_page)
                else:
                    # Same user - just update and refresh
                    self.transactions_page.user = self.current_user
                    if hasattr(self.transactions_page, 'refresh_table'):
                        self.transactions_page.refresh_table()
            
            # Switch to transactions page
            self.main_pages.setCurrentWidget(self.transactions_page)
            
            # Ensure the page is visible
            self.transactions_page.show()
            self.transactions_page.setVisible(True)
            
        except Exception as e:
            import traceback
            print(f"Error showing transactions page: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to load transactions page: {str(e)}")
    
    def handle_show_budget_settings(self):
        """Handle request to show budget settings"""
        if self.current_user is None:
            return
        
        # Reload user data to ensure latest settings
        self.current_user = self.user_manager.get_user(self.current_user.username)
        
        # Create page if missing
        if not hasattr(self, 'budget_settings_page') or self.budget_settings_page is None:
            self.budget_settings_page = BudgetSettingsPage(self.current_user, self.user_manager)
            self.budget_settings_page.go_back_to_dashboard.connect(self.show_dashboard)
            self.budget_settings_page.saved.connect(self.handle_budget_settings_saved)
            self.main_pages.addWidget(self.budget_settings_page)
        # keep user reference fresh
        self.budget_settings_page.user = self.current_user
        self.main_pages.setCurrentWidget(self.budget_settings_page)
    
    def handle_budget_settings_saved(self):
        """Handle budget settings saved - refresh all pages"""
        # Reload user data
        self.current_user = self.user_manager.get_user(self.current_user.username)
        
        # Refresh dashboard
        if self.dashboard_page:
            self.dashboard_page.current_user = self.current_user
            self.dashboard_page.update_dashboard_stats()
        
        # Refresh budget analysis if it exists
        if self.budget_analysis_page:
            self.budget_analysis_page.user = self.current_user
            self.budget_analysis_page.update_analysis()
        
        # Refresh transactions page if it exists
        if self.transactions_page:
            self.transactions_page.user = self.current_user
            self.transactions_page.refresh_table()
        
        self._notify("Budget settings saved.", level="success")
    
    def handle_transactions_updated(self):
        """Handle when transactions are updated - refresh all pages"""
        # Reload user data to ensure latest transactions
        if self.current_user:
            self.current_user = self.user_manager.get_user(self.current_user.username)
        
        # Refresh dashboard stats
        if self.dashboard_page:
            self.dashboard_page.current_user = self.current_user
            # Repopulate month filter if it exists
            if hasattr(self.dashboard_page, 'month_filter'):
                self.dashboard_page._populate_month_filter()
            self.dashboard_page.update_dashboard_stats()
        
        # Refresh budget analysis if it exists
        if self.budget_analysis_page:
            self.budget_analysis_page.user = self.current_user
            # Repopulate month filters with updated transactions
            if hasattr(self.budget_analysis_page, '_populate_month_filters'):
                self.budget_analysis_page._populate_month_filters()
            self.budget_analysis_page.update_analysis()
        
        # Refresh transactions page if it exists
        if self.transactions_page:
            self.transactions_page.user = self.current_user
            self.transactions_page.refresh_table()

    def show_dashboard(self):
        """Show the dashboard page"""
        # Reload user data to ensure latest data
        if self.current_user:
            self.current_user = self.user_manager.get_user(self.current_user.username)
            self.dashboard_page.current_user = self.current_user
            # Repopulate month filter if it exists
            if hasattr(self.dashboard_page, 'month_filter'):
                self.dashboard_page._populate_month_filter()
            self.dashboard_page.update_dashboard_stats()
        self.main_pages.setCurrentWidget(self.dashboard_page)

    def _notify(self, text: str, level: str = "info"):
        if hasattr(self, 'banner') and self.banner is not None:
            self.banner.show_message(text, level=level)

    def _build_header(self) -> QWidget:
        from gui.widgets.components import MainHeader
        
        bar = QWidget()
        bar.setObjectName("HeaderBar")
        layout = QHBoxLayout()
        # Increased margins: left, top, right, bottom - more space on left and right
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(8)

        # Use common MainHeader component
        main_header = MainHeader()
        layout.addWidget(main_header)
        layout.addStretch()

        profile_btn = QPushButton("My Profile")
        profile_btn.clicked.connect(self.show_profile)
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.handle_logout)
        for b in (profile_btn, logout_btn):
            b.setObjectName("HeaderBtn")
        layout.addWidget(profile_btn)
        layout.addWidget(logout_btn)

        bar.setLayout(layout)
        # Remove any height constraints and allow header to size naturally
        bar.setStyleSheet("""
            #HeaderBar { 
                background: #ffffff; 
                border: 1px solid #e6e8eb; 
                border-radius: 8px;
            }
        """)
        return bar

    def _build_sidebar(self) -> QWidget:
        side = QWidget()
        side.setObjectName("Sidebar")
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Welcome message at the top
        self.sidebar_welcome_label = QLabel("Welcome!")
        self.sidebar_welcome_label.setObjectName("SidebarWelcome")
        welcome_font = QFont()
        welcome_font.setPointSize(18)
        welcome_font.setBold(True)
        self.sidebar_welcome_label.setFont(welcome_font)
        self.sidebar_welcome_label.setStyleSheet("""
            QLabel#SidebarWelcome {
                color: #2c3e50;
                padding: 8px 0px;
                margin-bottom: 4px;
            }
        """)
        layout.addWidget(self.sidebar_welcome_label)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("""
            QFrame {
                color: #e6e8eb;
                background-color: #e6e8eb;
                max-height: 1px;
                margin: 8px 0px;
            }
        """)
        layout.addWidget(separator)

        def nav_btn(text, handler):
            btn = QPushButton(text)
            btn.setObjectName("NavBtn")
            btn.setCheckable(False)
            btn.clicked.connect(handler)
            return btn

        layout.addWidget(nav_btn("Dashboard", self.show_dashboard))
        layout.addWidget(nav_btn("Transactions", self.handle_show_transactions))
        layout.addWidget(nav_btn("Analysis", self.handle_show_spending_analysis))
        layout.addWidget(nav_btn("Budget Settings", self.handle_show_budget_settings))
        layout.addStretch()

        side.setLayout(layout)
        side.setStyleSheet("#Sidebar { background: #ffffff; border: 1px solid #e6e8eb; border-radius: 8px; min-width: 220px; }")
        return side

    def _update_sidebar_welcome(self, user: User):
        """Update the sidebar welcome message with user's name"""
        if hasattr(self, 'sidebar_welcome_label') and self.sidebar_welcome_label:
            name = (getattr(user, 'first_name', '') or '').strip()
            if not name:
                name = (getattr(user, 'username', '') or '').strip()
            if name:
                self.sidebar_welcome_label.setText(f"Welcome, {name}!")
            else:
                self.sidebar_welcome_label.setText("Welcome!")

    def _build_footer(self) -> QWidget:
        foot = QWidget()
        foot.setObjectName("Footer")
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)
        label = QLabel("© Team 8 — Personal Budget Management")
        label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(label)
        layout.addStretch()
        foot.setLayout(layout)
        foot.setStyleSheet("#Footer { background: #ffffff; border: 1px solid #e6e8eb; border-radius: 8px; }")
        return foot
    
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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Personal Budget Management System')
    parser.add_argument('--dev', '--dev-mode', action='store_true', 
                       help='Enable development mode (auto-login, bypasses authentication)')
    args = parser.parse_args()
    
    # Check for environment variable as alternative
    dev_mode = args.dev or os.getenv('DEV_MODE', '').lower() in ('1', 'true', 'yes')
    
    app = QApplication(sys.argv)
    app.setApplicationName("Personal Budget Management System")
    app.setApplicationVersion("1.0")
    
    # Set application style
    app.setStyleSheet("""
        QApplication { font-family: 'Inter', 'Segoe UI', Arial, sans-serif; }
        QWidget { font-size: 13px; }
        QLabel#MainHeaderTitle { font-size: 32px !important; font-weight: bold !important; color: #2c3e50; }
        QPushButton { padding: 9px 14px; border-radius: 8px; background: #2f6fed; color: #ffffff; border: none; }
        QPushButton:hover { background: #245add; }
        QPushButton#HeaderBtn { background: #f0f3f8; color: #2c3e50; }
        QPushButton#HeaderBtn:hover { background: #e6eaf1; }
        QPushButton#NavBtn { text-align: left; background: transparent; color: #2c3e50; padding: 10px 12px; }
        QPushButton#NavBtn:hover { background: #f5f7fb; }
        QTableWidget { selection-background-color: #e6efff; }
        QHeaderView::section { background: #f5f7fb; color: #2c3e50; border: none; padding: 10px; font-weight: 600; }
        QScrollArea { background: transparent; }
    """)

    window = MainWindow(dev_mode=dev_mode)
    window.show()
    
    # Run the application
    exit_code = app.exec()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
