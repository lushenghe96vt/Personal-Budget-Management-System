# Personal Budget Management System - GUI

## Overview
This is the PyQt6 GUI application for Team 8's Personal Budget Management System. The application provides user authentication, account management, and a foundation for budget tracking features.

## Features Implemented (Sprint 1)

### ✅ User Authentication
- **Account Creation**: Users can create new accounts with username, email, password, and personal information
- **Login System**: Secure login with password hashing using SHA-256
- **Form Validation**: Comprehensive validation for all input fields
- **Error Handling**: User-friendly error messages and validation feedback

### ✅ Account Management
- **Profile Modification**: Users can update their personal information (name, email, phone)
- **Password Changes**: Secure password update functionality
- **Account Statistics**: View account creation date, last login, and user information

### ✅ User Interface
- **Modern Design**: Clean, professional PyQt6 interface with custom styling
- **Responsive Layout**: Adaptive UI that works on different screen sizes
- **Navigation**: Menu bar with File, Account, and Help menus
- **Dashboard**: Welcome page with placeholder for future budget features

## Project Structure

```
gui/
├── app/
│   ├── models/           # Data models and user management
│   │   ├── __init__.py
│   │   └── user.py       # User model and UserManager class
│   ├── pages/            # Application pages
│   │   ├── auth.py       # Login and signup pages
│   │   ├── profile.py    # User profile management
│   │   └── dashboard.py  # Main dashboard (placeholder)
│   ├── main.py           # Main application entry point
│   └── __main__.py       # Application runner
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Installation and Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python -m app
   ```
   or
   ```bash
   python app/main.py
   ```

## Usage

### First Time Setup
1. Launch the application
2. Click "Sign Up" on the login screen
3. Fill in your information:
   - Username (3-20 characters, letters/numbers/underscores only)
   - Email address
   - First and last name
   - Phone number (optional)
   - Password (minimum 6 characters)
   - Confirm password

### Daily Usage
1. Launch the application
2. Enter your username and password
3. Access your dashboard and profile features
4. Use the menu bar to navigate between features

### Profile Management
- Access your profile via **Account → My Profile**
- Update personal information in the "Personal Information" tab
- Change your password in the "Account Settings" tab
- View account statistics in the "Account Statistics" tab

## Data Storage

- User data is stored locally in JSON format in the `data/` directory
- Passwords are securely hashed using SHA-256
- No sensitive data is stored in plain text

## Team Information

**Team 8: Personal Budget Management System**
- **Jason Huang** (Scrum Master)
- **Sheng Lu**
- **Ankush Chaudhary**
- **Luke Graham**

## Future Features (Coming in Next Sprints)

- Bank statement upload and processing
- Automatic transaction categorization
- Interactive budget visualizations (pie charts, line graphs)
- Spending trends and forecasting
- Budget goals and tracking
- Transaction management with notes and category editing
- Export functionality for reports and tax preparation
- Notification system for budget alerts
- Subscription tracking

## Technical Details

- **Framework**: PyQt6
- **Language**: Python 3.x
- **Data Storage**: JSON files (local storage)
- **Security**: SHA-256 password hashing
- **Architecture**: MVC pattern with separate models, views, and controllers

## Sprint 1 Backlog Completion

| Task ID | Description | Status |
|---------|-------------|---------|
| 3 | Be able to create an account / Login in an account | ✅ Complete |
| 9 | Modify personal information - Make my account information accurate | ✅ Complete |
| 28 | Use PyQt for visually appealing GUI | ✅ Complete |

## Development Notes

- The application uses a stacked widget architecture for smooth transitions between login and main app
- All user input is validated on both client and server side
- The UI is designed to be responsive and user-friendly
- Code follows Python best practices with proper error handling and documentation
