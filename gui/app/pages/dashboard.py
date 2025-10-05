"""
Dashboard page for Personal Budget Management System
Main landing page after user login
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class DashboardPage(QWidget):
    """Main dashboard page widget"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dashboard UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Welcome section
        welcome_label = QLabel("Welcome to your Personal Budget Dashboard!")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_font = QFont()
        welcome_font.setPointSize(24)
        welcome_font.setBold(True)
        welcome_label.setFont(welcome_font)
        welcome_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(welcome_label)
        
        # Quick stats section (placeholder)
        stats_layout = QHBoxLayout()
        
        # Total Spending Card
        spending_card = self.create_stat_card("Total Spending This Month", "$0.00", "#e74c3c")
        stats_layout.addWidget(spending_card)
        
        # Budget Remaining Card
        budget_card = self.create_stat_card("Budget Remaining", "$0.00", "#27ae60")
        stats_layout.addWidget(budget_card)
        
        # Transactions Card
        transactions_card = self.create_stat_card("Transactions", "0", "#3498db")
        stats_layout.addWidget(transactions_card)
        
        layout.addLayout(stats_layout)
        
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
        upload_button = QPushButton("Upload Bank Statement")
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
        actions_layout.addWidget(upload_button)
        
        # View Transactions Button
        transactions_button = QPushButton("View Transactions")
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
        actions_layout.addWidget(transactions_button)
        
        # Set Budget Button
        budget_button = QPushButton("Set Budget")
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
        actions_layout.addWidget(budget_button)
        
        layout.addLayout(actions_layout)
        
        # Recent activity section (placeholder)
        activity_label = QLabel("Recent Activity")
        activity_font = QFont()
        activity_font.setPointSize(18)
        activity_font.setBold(True)
        activity_label.setFont(activity_font)
        activity_label.setStyleSheet("color: #2c3e50; margin-top: 30px;")
        layout.addWidget(activity_label)
        
        activity_info = QLabel("""
        <div style="background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; color: #6c757d;">
            <h4>No recent activity</h4>
            <p>Upload your first bank statement to start tracking your spending!</p>
        </div>
        """)
        activity_info.setWordWrap(True)
        layout.addWidget(activity_info)
        
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
        self.setLayout(layout)
    
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
