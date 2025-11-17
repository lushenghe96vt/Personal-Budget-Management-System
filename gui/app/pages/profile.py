"""
profile.py
Personal Budget Management System - User Profile Module
Author: Ankush
Date: 10/11/25

Description:
  User profile management interface for editing personal information and account settings.
  Provides secure password change functionality and account statistics.

Implements:
  - Personal information editing (name, email, phone)
  - Password change with current password verification
  - Account statistics display
  - Profile data persistence
  - Tabbed interface for organized settings
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFormLayout, QGroupBox,
    QTabWidget, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from ..models.user import UserManager, User
from ..style import Styles
from gui.widgets.components import PageHeader, SectionCard, StyledButton


class ProfilePage(QWidget):
    """User profile modification page"""
    profile_updated = pyqtSignal(User)
    go_back_to_dashboard = pyqtSignal()  # Signal to go back to dashboard
    
    def __init__(self, user_manager: UserManager, current_user: User):
        super().__init__()
        self.user_manager = user_manager
        self.current_user = current_user
        self.setup_ui()
        self.load_user_data()
    
    def setup_ui(self):
        """Setup the profile UI with unified styling"""
        layout = QVBoxLayout()
        layout.setSpacing(24)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Header with back button and title
        page_header = PageHeader("My Profile", show_back=True)
        page_header.back_clicked.connect(self.go_back_to_dashboard.emit)
        layout.addWidget(page_header)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(Styles.TAB_WIDGET)
        
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
        layout.addStretch()
        
        self.setLayout(layout)
    
    def create_personal_info_tab(self):
        """Create personal information tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Personal Information Group
        personal_group = QGroupBox("Personal Information")
        personal_group.setStyleSheet(Styles.GROUPBOX)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # First Name
        self.first_name_input = QLineEdit()
        self.first_name_input.setStyleSheet(Styles.LINE_EDIT)
        form_layout.addRow("First Name:", self.first_name_input)
        
        # Last Name
        self.last_name_input = QLineEdit()
        self.last_name_input.setStyleSheet(Styles.LINE_EDIT)
        form_layout.addRow("Last Name:", self.last_name_input)
        
        # Username (read-only)
        self.username_input = QLineEdit()
        self.username_input.setReadOnly(True)
        self.username_input.setStyleSheet(Styles.LINE_EDIT_READONLY)
        form_layout.addRow("Username:", self.username_input)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setStyleSheet(Styles.LINE_EDIT)
        form_layout.addRow("Email:", self.email_input)
        
        # Phone
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Optional")
        self.phone_input.setStyleSheet(Styles.LINE_EDIT)
        form_layout.addRow("Phone:", self.phone_input)
        
        personal_group.setLayout(form_layout)
        layout.addWidget(personal_group)
        
        # Update button
        self.update_personal_button = StyledButton("Update Personal Information", StyledButton.PRIMARY)
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
        password_group.setStyleSheet(Styles.GROUPBOX)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Current Password
        self.current_password_input = QLineEdit()
        self.current_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_password_input.setPlaceholderText("Enter current password")
        self.current_password_input.setStyleSheet(Styles.LINE_EDIT)
        form_layout.addRow("Current Password:", self.current_password_input)
        
        # New Password
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setPlaceholderText("Enter new password")
        self.new_password_input.setStyleSheet(Styles.LINE_EDIT)
        form_layout.addRow("New Password:", self.new_password_input)
        
        # Confirm New Password
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Confirm new password")
        self.confirm_password_input.setStyleSheet(Styles.LINE_EDIT)
        form_layout.addRow("Confirm Password:", self.confirm_password_input)
        
        password_group.setLayout(form_layout)
        layout.addWidget(password_group)
        
        # Change password button
        self.change_password_button = StyledButton("Change Password", StyledButton.DANGER)
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
        stats_group.setStyleSheet(Styles.GROUPBOX)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Username (read-only)
        self.username_display = QLineEdit()
        self.username_display.setReadOnly(True)
        self.username_display.setStyleSheet(Styles.LINE_EDIT_READONLY)
        form_layout.addRow("Username:", self.username_display)
        
        # Account Created (read-only)
        self.created_display = QLineEdit()
        self.created_display.setReadOnly(True)
        self.created_display.setStyleSheet(Styles.LINE_EDIT_READONLY)
        form_layout.addRow("Account Created:", self.created_display)
        
        # Last Login (read-only)
        self.last_login_display = QLineEdit()
        self.last_login_display.setReadOnly(True)
        self.last_login_display.setStyleSheet(Styles.LINE_EDIT_READONLY)
        form_layout.addRow("Last Login:", self.last_login_display)
        
        stats_group.setLayout(form_layout)
        layout.addWidget(stats_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def load_user_data(self):
        """Load current user data into the form"""
        self.first_name_input.setText(self.current_user.first_name)
        self.last_name_input.setText(self.current_user.last_name)
        self.email_input.setText(self.current_user.email)
        self.phone_input.setText(self.current_user.phone or "")
        self.username_input.setText(self.current_user.username)
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
