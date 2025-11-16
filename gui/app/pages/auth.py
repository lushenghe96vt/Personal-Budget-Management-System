"""
auth.py
Personal Budget Management System - Authentication Module
Author: Ankush
Date: 10/11/25

Description:
  Handles user authentication including login and signup functionality.
  Provides secure user registration and login with password hashing.

Implements:
  - User login with username/password authentication
  - New user registration with validation
  - Password hashing using SHA-256
  - Session management and user state
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFormLayout, QGroupBox,
    QStackedWidget, QCheckBox, QFrame, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPalette
from models import UserManager, User


class LoginPage(QWidget):
    """Login page widget"""
    login_successful = pyqtSignal(User)
    switch_to_signup = pyqtSignal()
    
    def __init__(self, user_manager: UserManager):
        super().__init__()
        self.user_manager = user_manager
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the login UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # Title
        title_label = QLabel("Personal Budget Management")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(26)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 4px;")
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Sign In")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(26)
        subtitle_font.setBold(True)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #7f8c8d; margin-bottom: 24px;")
        layout.addWidget(subtitle_label)
        
        # Login form
        form_group = QGroupBox()
        form_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                padding: 20px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        form_group.setMinimumWidth(560)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignHCenter)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        
        # Username field
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QLineEdit::placeholder { color: #8a96a3; }
        """)
        self.username_input.setMinimumWidth(420)
        self.username_input.setMinimumHeight(44)
        form_layout.addRow("Username:", self.username_input)
        
        # Password field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QLineEdit::placeholder { color: #8a96a3; }
        """)
        self.password_input.setMinimumWidth(420)
        self.password_input.setMinimumHeight(44)
        form_layout.addRow("Password:", self.password_input)
        
        # Remember me checkbox
        self.remember_checkbox = QCheckBox("Remember me")
        self.remember_checkbox.setStyleSheet("color: #2c3e50;")
        form_layout.addRow("", self.remember_checkbox)
        
        # Assemble form group with fields, primary action and secondary links inside the box
        group_vbox = QVBoxLayout()
        group_vbox.setSpacing(14)
        group_vbox.addLayout(form_layout)

        self.login_button = QPushButton("Sign In")
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #2f6fed;
                color: white;
                border: none;
                padding: 15px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #245add; }
            QPushButton:pressed { background-color: #1e49bd; }
        """)
        self.login_button.clicked.connect(self.handle_login)
        group_vbox.addWidget(self.login_button)

        links_row = QHBoxLayout()
        forgot_btn = QPushButton("Forgot Password?")
        forgot_btn.setStyleSheet("""
            QPushButton { color: #2f6fed; background: transparent; border: none; font-weight: 600; }
            QPushButton:hover { text-decoration: underline; }
        """)
        forgot_btn.clicked.connect(self.open_reset_password_dialog)
        links_row.addWidget(forgot_btn)
        links_row.addStretch()
        signup_btn = QPushButton("Create an account")
        signup_btn.setStyleSheet("""
            QPushButton { color: #2f6fed; background: transparent; border: none; font-weight: 600; }
            QPushButton:hover { text-decoration: underline; }
        """)
        signup_btn.clicked.connect(self.switch_to_signup.emit)
        links_row.addWidget(signup_btn)
        group_vbox.addLayout(links_row)

        form_group.setLayout(group_vbox)
        layout.addWidget(form_group, 0, Qt.AlignmentFlag.AlignHCenter)

        # (Forgot password moved into links row above)
        
        # Set layout
        layout.addStretch()
        self.setLayout(layout)
        
        # Connect Enter key to login
        self.password_input.returnPressed.connect(self.handle_login)

    def open_reset_password_dialog(self):
        """Open a simple reset password dialog without external auth."""
        dlg = ResetPasswordDialog(self.user_manager, self)
        dlg.exec()
    
    def handle_login(self):
        """Handle login attempt"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Login Error", "Please enter both username and password.")
            return
        
        success, message, user = self.user_manager.authenticate_user(username, password)
        
        if success:
            self.login_successful.emit(user)
            self.clear_form()
        else:
            QMessageBox.warning(self, "Login Failed", message)
    
    def clear_form(self):
        """Clear the login form"""
        self.username_input.clear()
        self.password_input.clear()
        self.remember_checkbox.setChecked(False)


class SignupPage(QWidget):
    """Signup page widget"""
    signup_successful = pyqtSignal(User)
    switch_to_login = pyqtSignal()
    
    def __init__(self, user_manager: UserManager):
        super().__init__()
        self.user_manager = user_manager
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the signup UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # Title
        title_label = QLabel("Personal Budget Management")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(26)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 4px;")
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Create Account")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(26)
        subtitle_font.setBold(True)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #7f8c8d; margin-bottom: 24px;")
        layout.addWidget(subtitle_label)
        
        # Signup form
        form_group = QGroupBox()
        form_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                padding: 20px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        form_group.setMinimumWidth(600)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignHCenter)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        
        # Username field
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username (3-20 characters)")
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QLineEdit::placeholder { color: #8a96a3; }
        """)
        self.username_input.setMinimumWidth(420)
        self.username_input.setMinimumHeight(44)
        form_layout.addRow("Username:", self.username_input)
        
        # Email field
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email address")
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QLineEdit::placeholder { color: #8a96a3; }
        """)
        self.email_input.setMinimumWidth(420)
        self.email_input.setMinimumHeight(44)
        form_layout.addRow("Email:", self.email_input)
        
        # Name fields
        name_layout = QHBoxLayout()
        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("First name")
        self.first_name_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QLineEdit::placeholder { color: #8a96a3; }
        """)
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Last name")
        self.last_name_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QLineEdit::placeholder { color: #8a96a3; }
        """)
        self.first_name_input.setMinimumHeight(44)
        name_layout.addWidget(self.first_name_input)
        self.last_name_input.setMinimumHeight(44)
        name_layout.addWidget(self.last_name_input)
        form_layout.addRow("Name:", name_layout)
        
        # Phone field (optional)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone number (optional)")
        self.phone_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QLineEdit::placeholder { color: #8a96a3; }
        """)
        self.phone_input.setMinimumWidth(420)
        self.phone_input.setMinimumHeight(44)
        form_layout.addRow("Phone:", self.phone_input)
        
        # Password fields
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password (min 6 characters)")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QLineEdit::placeholder { color: #8a96a3; }
        """)
        self.password_input.setMinimumWidth(420)
        self.password_input.setMinimumHeight(44)
        form_layout.addRow("Password:", self.password_input)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm your password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
            QLineEdit::placeholder { color: #8a96a3; }
        """)
        self.confirm_password_input.setMinimumWidth(420)
        self.confirm_password_input.setMinimumHeight(44)
        form_layout.addRow("Confirm Password:", self.confirm_password_input)
        
        # Assemble signup group with fields, primary action and secondary link inside the box
        group_vbox = QVBoxLayout()
        group_vbox.setSpacing(14)
        group_vbox.addLayout(form_layout)

        self.signup_button = QPushButton("Create Account")
        self.signup_button.setStyleSheet("""
            QPushButton {
                background-color: #2f6fed;
                color: white;
                border: none;
                padding: 15px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #245add; }
            QPushButton:pressed { background-color: #1e49bd; }
        """)
        self.signup_button.clicked.connect(self.handle_signup)
        group_vbox.addWidget(self.signup_button)

        # Secondary link: already have an account (Sign In)
        link_row = QHBoxLayout()
        signin_btn = QPushButton("Already have an account? Sign In")
        signin_btn.setStyleSheet("""
            QPushButton { color: #2f6fed; background: transparent; border: none; font-weight: 600; }
            QPushButton:hover { text-decoration: underline; }
        """)
        signin_btn.clicked.connect(self.switch_to_login.emit)
        link_row.addWidget(signin_btn)
        link_row.addStretch()
        group_vbox.addLayout(link_row)

        form_group.setLayout(group_vbox)
        layout.addWidget(form_group, 0, Qt.AlignmentFlag.AlignHCenter)
        
        # (Removed duplicate bottom login link; link lives inside form box)
        
        # Set layout
        layout.addStretch()
        self.setLayout(layout)
        
        # Connect Enter key to signup
        self.confirm_password_input.returnPressed.connect(self.handle_signup)
    
    def handle_signup(self):
        """Handle signup attempt"""
        # Get form data
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        phone = self.phone_input.text().strip()
        password = self.password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()
        
        # Validation
        if not all([username, email, first_name, last_name, password, confirm_password]):
            QMessageBox.warning(self, "Signup Error", "Please fill in all required fields.")
            return
        
        if password != confirm_password:
            QMessageBox.warning(self, "Signup Error", "Passwords do not match.")
            return
        
        # Create account
        success, message = self.user_manager.create_user(
            username, email, password, first_name, last_name, phone
        )
        
        if success:
            QMessageBox.information(self, "Success", message)
            # Get the created user and emit signal
            user = self.user_manager.get_user(username)
            self.signup_successful.emit(user)
            self.clear_form()
        else:
            QMessageBox.warning(self, "Signup Failed", message)
    
    def clear_form(self):
        """Clear the signup form"""
        self.username_input.clear()
        self.email_input.clear()
        self.first_name_input.clear()
        self.last_name_input.clear()
        self.phone_input.clear()
        self.password_input.clear()
        self.confirm_password_input.clear()


class AuthWidget(QWidget):
    """Main authentication widget that switches between login and signup"""
    auth_successful = pyqtSignal(User)
    
    def __init__(self, user_manager: UserManager):
        super().__init__()
        self.user_manager = user_manager
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the authentication UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget to switch between login and signup
        self.stacked_widget = QStackedWidget()
        
        # Create pages
        self.login_page = LoginPage(self.user_manager)
        self.signup_page = SignupPage(self.user_manager)
        
        # Connect signals
        self.login_page.switch_to_signup.connect(self.show_signup)
        self.signup_page.switch_to_login.connect(self.show_login)
        self.login_page.login_successful.connect(self.auth_successful.emit)
        self.signup_page.signup_successful.connect(self.auth_successful.emit)
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.signup_page)
        
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)
        
        # Set initial page
        self.show_login()
    
    def show_login(self):
        """Show login page"""
        self.stacked_widget.setCurrentWidget(self.login_page)
    
    def show_signup(self):
        """Show signup page"""
        self.stacked_widget.setCurrentWidget(self.signup_page)


class ResetPasswordDialog(QDialog):
    """Simple dialog to reset password by username (no external auth)."""

    def __init__(self, user_manager: UserManager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.setWindowTitle("Reset Password")
        self.setModal(True)
        self.resize(420, 260)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Reset your password")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = QFont()
        f.setPointSize(16)
        f.setBold(True)
        title.setFont(f)
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.new_pw_input = QLineEdit()
        self.new_pw_input.setPlaceholderText("New password (min 6 chars)")
        self.new_pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_pw_input = QLineEdit()
        self.confirm_pw_input.setPlaceholderText("Confirm new password")
        self.confirm_pw_input.setEchoMode(QLineEdit.EchoMode.Password)

        for w in (self.username_input, self.new_pw_input, self.confirm_pw_input):
            w.setStyleSheet("""
                QLineEdit { padding: 10px; border: 2px solid #ddd; border-radius: 6px; }
                QLineEdit:focus { border-color: #3498db; }
            """)
            layout.addWidget(w)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Update Password")
        save_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px 16px; border: none; border-radius: 6px; font-weight: 600;")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #95a5a6; color: white; padding: 10px 16px; border: none; border-radius: 6px; font-weight: 600;")
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        save_btn.clicked.connect(self._handle_save)
        cancel_btn.clicked.connect(self.reject)
        self.setLayout(layout)

    def _handle_save(self):
        username = (self.username_input.text() or "").strip()
        pw = (self.new_pw_input.text() or "").strip()
        confirm = (self.confirm_pw_input.text() or "").strip()

        if not username or not pw or not confirm:
            QMessageBox.warning(self, "Missing Info", "Please fill all fields.")
            return
        if pw != confirm:
            QMessageBox.warning(self, "Mismatch", "Passwords do not match.")
            return
        if not self.user_manager.user_exists(username):
            QMessageBox.warning(self, "User Not Found", "No account with that username.")
            return
        ok, msg = self.user_manager.update_user(username, password=pw)
        if ok:
            QMessageBox.information(self, "Updated", "Password updated successfully.")
            self.accept()
        else:
            QMessageBox.warning(self, "Not Updated", msg or "Unable to update password.")
