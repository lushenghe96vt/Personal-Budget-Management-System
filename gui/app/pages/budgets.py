"""
Budget analysis and management page for Personal Budget Management System
Provides spending analysis, category breakdowns, and budget insights
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QGroupBox, QTabWidget, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPixmap, QPainter
from pathlib import Path
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.models import Transaction
from models import User


class SimplePieChart(QWidget):
    """Simple pie chart widget for category breakdown"""
    
    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.setMinimumSize(300, 300)
    
    def paintEvent(self, event):
        """Draw the pie chart"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Colors for different categories
        colors = [
            QColor("#e74c3c"), QColor("#3498db"), QColor("#2ecc71"), QColor("#f39c12"),
            QColor("#9b59b6"), QColor("#1abc9c"), QColor("#e67e22"), QColor("#34495e"),
            QColor("#f1c40f"), QColor("#e91e63"), QColor("#00bcd4"), QColor("#4caf50")
        ]
        
        # Calculate total
        total = sum(self.data.values())
        if total == 0:
            return
        
        # Draw pie chart
        rect = self.rect().adjusted(20, 20, -20, -20)
        start_angle = 0
        
        for i, (category, value) in enumerate(self.data.items()):
            if value > 0:
                angle = int((value / total) * 360 * 16)  # Qt uses 1/16th degree units
                color = colors[i % len(colors)]
                
                painter.setBrush(color)
                painter.setPen(QColor("#2c3e50"))
                painter.drawPie(rect, start_angle, angle)
                
                start_angle += angle


class BudgetAnalysisPage(QWidget):
    """Budget analysis and spending insights page"""
    
    go_back_to_dashboard = pyqtSignal()  # Signal to go back to dashboard
    
    def __init__(self, user: User, user_manager=None):
        super().__init__()
        self.user = user
        self.user_manager = user_manager
        self.setup_ui()
        self.update_analysis()
    
    def setup_ui(self):
        """Setup the budget analysis page UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Budget Analysis & Insights")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Create tab widget for different analysis views
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
        
        # Overview tab
        self.overview_tab = self.create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "Overview")
        
        # Category breakdown tab
        self.categories_tab = self.create_categories_tab()
        self.tab_widget.addTab(self.categories_tab, "Categories")
        
        # Monthly trends tab
        self.trends_tab = self.create_trends_tab()
        self.tab_widget.addTab(self.trends_tab, "Monthly Trends")
        
        # Budget goals tab
        self.goals_tab = self.create_goals_tab()
        self.tab_widget.addTab(self.goals_tab, "Budget Goals")
        
        layout.addWidget(self.tab_widget)
        
        # Back to Dashboard button
        button_layout = QHBoxLayout()
        self.back_button = QPushButton("🏠 Back to Dashboard")
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.back_button.clicked.connect(self.go_back_to_dashboard.emit)
        button_layout.addWidget(self.back_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_overview_tab(self):
        """Create the overview tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Key metrics
        metrics_layout = QHBoxLayout()
        
        # Total spending
        self.total_spending_label = QLabel("$0.00")
        self.total_spending_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_spending_label.setStyleSheet("""
            QLabel {
                background-color: #e74c3c;
                color: white;
                padding: 20px;
                border-radius: 10px;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        metrics_layout.addWidget(self.create_metric_card("Total Spending", self.total_spending_label))
        
        # Total income
        self.total_income_label = QLabel("$0.00")
        self.total_income_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_income_label.setStyleSheet("""
            QLabel {
                background-color: #27ae60;
                color: white;
                padding: 20px;
                border-radius: 10px;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        metrics_layout.addWidget(self.create_metric_card("Total Income", self.total_income_label))
        
        # Net balance
        self.net_balance_label = QLabel("$0.00")
        self.net_balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.net_balance_label.setStyleSheet("""
            QLabel {
                background-color: #3498db;
                color: white;
                padding: 20px;
                border-radius: 10px;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        metrics_layout.addWidget(self.create_metric_card("Net Balance", self.net_balance_label))
        
        # Transaction count
        self.transaction_count_label = QLabel("0")
        self.transaction_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.transaction_count_label.setStyleSheet("""
            QLabel {
                background-color: #9b59b6;
                color: white;
                padding: 20px;
                border-radius: 10px;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        metrics_layout.addWidget(self.create_metric_card("Transactions", self.transaction_count_label))
        
        layout.addLayout(metrics_layout)
        
        # Recent insights
        insights_group = QGroupBox("Recent Insights")
        insights_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
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
        
        self.insights_label = QLabel("No insights available. Upload transactions to see analysis.")
        self.insights_label.setWordWrap(True)
        self.insights_label.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        
        insights_layout = QVBoxLayout()
        insights_layout.addWidget(self.insights_label)
        insights_group.setLayout(insights_layout)
        layout.addWidget(insights_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_categories_tab(self):
        """Create the categories breakdown tab"""
        tab = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(20)
        
        # Pie chart
        chart_group = QGroupBox("Spending by Category")
        chart_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
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
        
        self.pie_chart = SimplePieChart({})
        chart_layout = QVBoxLayout()
        chart_layout.addWidget(self.pie_chart)
        chart_group.setLayout(chart_layout)
        layout.addWidget(chart_group)
        
        # Category table
        table_group = QGroupBox("Category Details")
        table_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
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
        
        self.category_table = QTableWidget()
        self.category_table.setColumnCount(3)
        self.category_table.setHorizontalHeaderLabels(["Category", "Amount", "Percentage"])
        
        header = self.category_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.category_table.setAlternatingRowColors(True)
        self.category_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
        table_layout = QVBoxLayout()
        table_layout.addWidget(self.category_table)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_trends_tab(self):
        """Create the monthly trends tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Monthly summary table
        trends_group = QGroupBox("Monthly Spending Trends")
        trends_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
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
        
        self.monthly_table = QTableWidget()
        self.monthly_table.setColumnCount(4)
        self.monthly_table.setHorizontalHeaderLabels(["Month", "Income", "Spending", "Net"])
        
        header = self.monthly_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self.monthly_table.setAlternatingRowColors(True)
        self.monthly_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        
        trends_layout = QVBoxLayout()
        trends_layout.addWidget(self.monthly_table)
        trends_group.setLayout(trends_layout)
        layout.addWidget(trends_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_goals_tab(self):
        """Create the budget goals tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Budget goals placeholder
        goals_group = QGroupBox("Budget Goals & Limits")
        goals_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
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
        
        goals_info = QLabel("""
        <div style="background-color: #e8f4f8; border: 1px solid #bee5eb; border-radius: 8px; padding: 20px; color: #0c5460;">
            <h4>Budget Goals Feature Coming Soon!</h4>
            <p>This feature will allow you to:</p>
            <ul>
                <li><strong>Set Monthly Budgets:</strong> Define spending limits for each category</li>
                <li><strong>Track Progress:</strong> Monitor your spending against budget goals</li>
                <li><strong>Get Alerts:</strong> Receive notifications when approaching limits</li>
                <li><strong>Analyze Trends:</strong> See how your spending patterns change over time</li>
                <li><strong>Goal Setting:</strong> Set savings goals and track progress</li>
            </ul>
            <p><em>Upload more transactions to see better insights in the meantime!</em></p>
        </div>
        """)
        goals_info.setWordWrap(True)
        
        goals_layout = QVBoxLayout()
        goals_layout.addWidget(goals_info)
        goals_group.setLayout(goals_layout)
        layout.addWidget(goals_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_metric_card(self, title: str, value_widget: QWidget) -> QWidget:
        """Create a metric card widget"""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 10px;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)
        
        # Value
        layout.addWidget(value_widget)
        
        card.setLayout(layout)
        return card
    
    def update_analysis(self):
        """Update all analysis data"""
        if not self.user or not self.user.transactions:
            return
        
        transactions = self.user.transactions
        
        # Calculate totals
        total_spending = sum(abs(t.amount) for t in transactions if t.amount < 0)
        total_income = sum(t.amount for t in transactions if t.amount > 0)
        net_balance = total_income - total_spending
        transaction_count = len(transactions)
        
        # Update overview metrics
        self.total_spending_label.setText(f"${total_spending:.2f}")
        self.total_income_label.setText(f"${total_income:.2f}")
        self.net_balance_label.setText(f"${net_balance:.2f}")
        self.transaction_count_label.setText(str(transaction_count))
        
        # Update insights
        insights = self.generate_insights(transactions)
        self.insights_label.setText(insights)
        
        # Update category breakdown
        self.update_category_breakdown(transactions)
        
        # Update monthly trends
        self.update_monthly_trends(transactions)
    
    def generate_insights(self, transactions: list) -> str:
        """Generate insights from transaction data"""
        if not transactions:
            return "No insights available. Upload transactions to see analysis."
        
        insights = []
        
        # Most expensive category
        category_totals = defaultdict(Decimal)
        for txn in transactions:
            if txn.amount < 0:  # Only spending
                category_totals[txn.category] += abs(txn.amount)
        
        if category_totals:
            top_category = max(category_totals.items(), key=lambda x: x[1])
            insights.append(f"💸 Your biggest expense category is <b>{top_category[0]}</b> at ${top_category[1]:.2f}")
        
        # Recent spending trend
        recent_transactions = [t for t in transactions if t.date >= datetime.now() - timedelta(days=30)]
        if recent_transactions:
            recent_spending = sum(abs(t.amount) for t in recent_transactions if t.amount < 0)
            insights.append(f"📅 You've spent ${recent_spending:.2f} in the last 30 days")
        
        # Income vs spending
        total_spending = sum(abs(t.amount) for t in transactions if t.amount < 0)
        total_income = sum(t.amount for t in transactions if t.amount > 0)
        if total_income > 0:
            spending_ratio = (total_spending / total_income) * 100
            insights.append(f"💰 You're spending {spending_ratio:.1f}% of your income")
        
        # Transaction frequency
        if len(transactions) > 0:
            avg_per_day = len(transactions) / max(1, (datetime.now() - min(t.date for t in transactions)).days)
            insights.append(f"📊 You average {avg_per_day:.1f} transactions per day")
        
        return "<br>".join(insights) if insights else "Upload more transactions to see detailed insights!"
    
    def update_category_breakdown(self, transactions: list):
        """Update category breakdown chart and table"""
        # Calculate category totals
        category_totals = defaultdict(Decimal)
        for txn in transactions:
            if txn.amount < 0:  # Only spending
                category_totals[txn.category] += abs(txn.amount)
        
        # Update pie chart
        self.pie_chart.data = dict(category_totals)
        self.pie_chart.update()
        
        # Update category table
        total_spending = sum(category_totals.values())
        self.category_table.setRowCount(len(category_totals))
        
        for row, (category, amount) in enumerate(sorted(category_totals.items(), key=lambda x: x[1], reverse=True)):
            # Category
            category_item = QTableWidgetItem(category)
            self.category_table.setItem(row, 0, category_item)
            
            # Amount
            amount_item = QTableWidgetItem(f"${amount:.2f}")
            self.category_table.setItem(row, 1, amount_item)
            
            # Percentage
            percentage = (amount / total_spending * 100) if total_spending > 0 else 0
            percentage_item = QTableWidgetItem(f"{percentage:.1f}%")
            self.category_table.setItem(row, 2, percentage_item)
    
    def update_monthly_trends(self, transactions: list):
        """Update monthly trends table"""
        # Group transactions by month
        monthly_data = defaultdict(lambda: {'income': Decimal('0'), 'spending': Decimal('0')})
        
        for txn in transactions:
            month_key = txn.date.strftime("%Y-%m")
            if txn.amount > 0:
                monthly_data[month_key]['income'] += txn.amount
            else:
                monthly_data[month_key]['spending'] += abs(txn.amount)
        
        # Update table
        self.monthly_table.setRowCount(len(monthly_data))
        
        for row, (month, data) in enumerate(sorted(monthly_data.items(), reverse=True)):
            # Month
            month_item = QTableWidgetItem(month)
            self.monthly_table.setItem(row, 0, month_item)
            
            # Income
            income_item = QTableWidgetItem(f"${data['income']:.2f}")
            income_item.setForeground(QColor("#27ae60"))
            self.monthly_table.setItem(row, 1, income_item)
            
            # Spending
            spending_item = QTableWidgetItem(f"${data['spending']:.2f}")
            spending_item.setForeground(QColor("#e74c3c"))
            self.monthly_table.setItem(row, 2, spending_item)
            
            # Net
            net = data['income'] - data['spending']
            net_item = QTableWidgetItem(f"${net:.2f}")
            net_color = QColor("#27ae60") if net >= 0 else QColor("#e74c3c")
            net_item.setForeground(net_color)
            self.monthly_table.setItem(row, 3, net_item)
