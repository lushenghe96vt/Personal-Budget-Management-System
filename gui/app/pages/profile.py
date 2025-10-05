"""
User profile page for Personal Budget Management System
Allows users to modify their personal information
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFormLayout, QGroupBox,
    QTabWidget, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from ..models import UserManager, User


class ProfilePage(QWidget):
    """User profile modification page"""
    profile_updated = pyqtSignal(User)
    
    def __init__(self, user_manager: UserManager, current_user: User):
        super().__init__()
        self.user_manager = user_manager
        self.current_user = current_user
        self.setup_ui()
        self.load_user_data()
    
    def setup_ui(self):
        """Setup the profile UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("My Profile")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                background-color: #f8f9fa;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #d5dbdb;
            }
        """)
        
        # Personal Information Tab
        self.personal_info_tab = self.create_personal_info_tab()
        self.tab_widget.addTab(self.personal_info_tab, "Personal Information")
        
        # Account Settings Tab
        self.account_settings_tab = self.create_account_settings_tab()
        self.tab_widget.addTab(self.account_settings_tab, "Account Settings")
        
        # Statistics Tab
        self.stats_tab = self.create_stats_tab()
        self.tab_widget.addTab(self.stats_tab, "Account Statistics")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def create_personal_info_tab(self):
        """Create personal information tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Personal Information Group
        personal_group = QGroupBox("Personal Information")
        personal_group.setStyleSheet("""
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
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # First Name
        self.first_name_input = QLineEdit()
        self.first_name_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        form_layout.addRow("First Name:", self.first_name_input)
        
        # Last Name
        self.last_name_input = QLineEdit()
        self.last_name_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        form_layout.addRow("Last Name:", self.last_name_input)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        form_layout.addRow("Email:", self.email_input)
        
        # Phone
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Optional")
        self.phone_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        form_layout.addRow("Phone:", self.phone_input)
        
        personal_group.setLayout(form_layout)
        layout.addWidget(personal_group)
        
        # Update button
        self.update_personal_button = QPushButton("Update Personal Information")
        self.update_personal_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.update_personal_button.clicked.connect(self.update_personal_info)
        layout.addWidget(self.update_personal_button)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_account_settings_tab(self):
        """Create account settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Change Password Group
        password_group = QGroupBox("Change Password")
        password_group.setStyleSheet("""
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
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Current Password
        self.current_password_input = QLineEdit()
        self.current_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_password_input.setPlaceholderText("Enter current password")
        self.current_password_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        form_layout.addRow("Current Password:", self.current_password_input)
        
        # New Password
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setPlaceholderText("Enter new password")
        self.new_password_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        form_layout.addRow("New Password:", self.new_password_input)
        
        # Confirm New Password
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Confirm new password")
        self.confirm_password_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        form_layout.addRow("Confirm Password:", self.confirm_password_input)
        
        password_group.setLayout(form_layout)
        layout.addWidget(password_group)
        
        # Change password button
        self.change_password_button = QPushButton("Change Password")
        self.change_password_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        self.change_password_button.clicked.connect(self.change_password)
        layout.addWidget(self.change_password_button)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_stats_tab(self):
        """Create account statistics tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Account Statistics Group
        stats_group = QGroupBox("Account Statistics")
        stats_group.setStyleSheet("""
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
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Username (read-only)
        self.username_display = QLineEdit()
        self.username_display.setReadOnly(True)
        self.username_display.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
                background-color: #ecf0f1;
            }
        """)
        form_layout.addRow("Username:", self.username_display)
        
        # Account Created (read-only)
        self.created_display = QLineEdit()
        self.created_display.setReadOnly(True)
        self.created_display.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
                background-color: #ecf0f1;
            }
        """)
        form_layout.addRow("Account Created:", self.created_display)
        
        # Last Login (read-only)
        self.last_login_display = QLineEdit()
        self.last_login_display.setReadOnly(True)
        self.last_login_display.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
                background-color: #ecf0f1;
            }
        """)
        form_layout.addRow("Last Login:", self.last_login_display)
        
        stats_group.setLayout(form_layout)
        layout.addWidget(stats_group)
        
        # Additional Info
        info_label = QLabel("""
        <h3>Account Information</h3>
        <p>Your account is part of Team 8's Personal Budget Management System.</p>
        <p>As a registered user, you have access to:</p>
        <ul>
            <li>Personalized budget tracking</li>
            <li>Data persistence across sessions</li>
            <li>Advanced notification settings</li>
            <li>Historical data access</li>
            <li>Custom spending categories</li>
        </ul>
        """)
        info_label.setStyleSheet("""
            QLabel {
                background-color: #e8f4f8;
                border: 1px solid #bee5eb;
                border-radius: 5px;
                padding: 15px;
                color: #0c5460;
            }
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def load_user_data(self):
        """Load current user data into the form"""
        self.first_name_input.setText(self.current_user.first_name)
        self.last_name_input.setText(self.current_user.last_name)
        self.email_input.setText(self.current_user.email)
        self.phone_input.setText(self.current_user.phone or "")
        self.username_display.setText(self.current_user.username)
        
        if self.current_user.created_at:
            self.created_display.setText(self.current_user.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        
        if self.current_user.last_login:
            self.last_login_display.setText(self.current_user.last_login.strftime("%Y-%m-%d %H:%M:%S"))
    
    def update_personal_info(self):
        """Update personal information"""
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        
        if not all([first_name, last_name, email]):
            QMessageBox.warning(self, "Update Error", "Please fill in all required fields.")
            return
        
        # Update user information
        success, message = self.user_manager.update_user(
            self.current_user.username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone if phone else None
        )
        
        if success:
            # Update current user object
            self.current_user.first_name = first_name
            self.current_user.last_name = last_name
            self.current_user.email = email
            self.current_user.phone = phone if phone else None
            
            QMessageBox.information(self, "Success", message)
            self.profile_updated.emit(self.current_user)
        else:
            QMessageBox.warning(self, "Update Failed", message)
    
    def change_password(self):
        """Change user password"""
        current_password = self.current_password_input.text().strip()
        new_password = self.new_password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()
        
        if not all([current_password, new_password, confirm_password]):
            QMessageBox.warning(self, "Password Change Error", "Please fill in all password fields.")
            return
        
        if new_password != confirm_password:
            QMessageBox.warning(self, "Password Change Error", "New passwords do not match.")
            return
        
        # Verify current password
        success, _, _ = self.user_manager.authenticate_user(self.current_user.username, current_password)
        if not success:
            QMessageBox.warning(self, "Password Change Error", "Current password is incorrect.")
            return
        
        # Update password
        success, message = self.user_manager.update_user(
            self.current_user.username,
            password=new_password
        )
        
        if success:
            QMessageBox.information(self, "Success", message)
            # Clear password fields
            self.current_password_input.clear()
            self.new_password_input.clear()
            self.confirm_password_input.clear()
        else:
            QMessageBox.warning(self, "Password Change Failed", message)
