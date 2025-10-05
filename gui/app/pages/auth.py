"""
Authentication pages for Personal Budget Management System
Includes login and signup functionality
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFormLayout, QGroupBox,
    QStackedWidget, QCheckBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPalette
from ..models import UserManager, User


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
        title_label = QLabel("Welcome Back!")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Sign in to your Personal Budget Management account")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #7f8c8d; margin-bottom: 30px;")
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
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Username field
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        form_layout.addRow("Username:", self.username_input)
        
        # Password field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        form_layout.addRow("Password:", self.password_input)
        
        # Remember me checkbox
        self.remember_checkbox = QCheckBox("Remember me")
        self.remember_checkbox.setStyleSheet("color: #2c3e50;")
        form_layout.addRow("", self.remember_checkbox)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Login button
        self.login_button = QPushButton("Sign In")
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 15px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)
        
        # Sign up link
        signup_layout = QHBoxLayout()
        signup_label = QLabel("Don't have an account?")
        signup_label.setStyleSheet("color: #7f8c8d;")
        signup_button = QPushButton("Sign Up")
        signup_button.setStyleSheet("""
            QPushButton {
                color: #3498db;
                border: none;
                background: transparent;
                text-decoration: underline;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #2980b9;
            }
        """)
        signup_button.clicked.connect(self.switch_to_signup.emit)
        
        signup_layout.addWidget(signup_label)
        signup_layout.addWidget(signup_button)
        signup_layout.addStretch()
        layout.addLayout(signup_layout)
        
        # Set layout
        layout.addStretch()
        self.setLayout(layout)
        
        # Connect Enter key to login
        self.password_input.returnPressed.connect(self.handle_login)
    
    def handle_login(self):
        """Handle login attempt"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Login Error", "Please enter both username and password.")
            return
        
        success, message, user = self.user_manager.authenticate_user(username, password)
        
        if success:
            QMessageBox.information(self, "Success", message)
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
        title_label = QLabel("Create Account")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Join Team 8's Personal Budget Management System")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #7f8c8d; margin-bottom: 30px;")
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
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Username field
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Choose a username (3-20 characters)")
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        form_layout.addRow("Username:", self.username_input)
        
        # Email field
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email address")
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
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
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Last name")
        self.last_name_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        name_layout.addWidget(self.first_name_input)
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
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        form_layout.addRow("Phone:", self.phone_input)
        
        # Password fields
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Create a password (min 6 characters)")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
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
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        form_layout.addRow("Confirm Password:", self.confirm_password_input)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Signup button
        self.signup_button = QPushButton("Create Account")
        self.signup_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 15px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        self.signup_button.clicked.connect(self.handle_signup)
        layout.addWidget(self.signup_button)
        
        # Login link
        login_layout = QHBoxLayout()
        login_label = QLabel("Already have an account?")
        login_label.setStyleSheet("color: #7f8c8d;")
        login_button = QPushButton("Sign In")
        login_button.setStyleSheet("""
            QPushButton {
                color: #3498db;
                border: none;
                background: transparent;
                text-decoration: underline;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #2980b9;
            }
        """)
        login_button.clicked.connect(self.switch_to_login.emit)
        
        login_layout.addWidget(login_label)
        login_layout.addWidget(login_button)
        login_layout.addStretch()
        layout.addLayout(login_layout)
        
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
