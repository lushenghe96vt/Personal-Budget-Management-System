"""
budgets.py
Personal Budget Management System - Budget Analysis Module
Author: Ankush
Date: 10/11/25

Description:
  Advanced budget analysis and spending insights with visual charts and statistics.
  Provides comprehensive financial analysis across multiple time periods.

Implements:
  - Category breakdown with pie charts
  - Spending by category analysis
  - Monthly trends visualization
  - Budget goals tracking
  - Spending insights and recommendations
  - Custom pie chart widget with perfect circular rendering
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QGroupBox, QTabWidget, QScrollArea, QGridLayout, QSizePolicy,
    QToolButton, QStyle, QProgressBar, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QSize
from PyQt6.QtGui import QFont, QColor, QPixmap, QPainter
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QScatterSeries, QCategoryAxis, QValueAxis
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
from core.view_spending import spending_summary, income_summary, forecast_spending
from core.exportWin import save_window_dialog


class SimplePieChart(QWidget):
    """Simple pie chart widget for category breakdown"""
    
    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.setMinimumSize(300, 300)
        self.setMaximumSize(500, 500)
        
        # Set size policy to maintain aspect ratio
        size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        size_policy.setHeightForWidth(True)
        self.setSizePolicy(size_policy)
    
    def sizeHint(self):
        """Return preferred size (square)"""
        return QSize(400, 400)
    
    def heightForWidth(self, width):
        """Maintain square aspect ratio"""
        return width
    
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
        
        # Get widget dimensions
        widget_rect = self.rect()
        widget_width = widget_rect.width()
        widget_height = widget_rect.height()
        
        # Calculate the largest square that fits in the widget
        size = min(widget_width, widget_height)
        margin = 20
        
        # Center the square
        x_offset = (widget_width - size) // 2
        y_offset = (widget_height - size) // 2
        
        # Create a perfect square for the pie chart
        pie_size = size - (margin * 2)
        rect = QRect(x_offset + margin, y_offset + margin, pie_size, pie_size)
        
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
        self._month_filter_options = {}  # Initialize filter options
        self.setup_ui()
        # Populate filters first, then update analysis
        if self.user and self.user.transactions:
            self._populate_month_filters()
        self.update_analysis()
    
    def setup_ui(self):
        """Setup the budget analysis page UI"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header row with back icon and title
        header = QHBoxLayout()
        self.back_button_top = QToolButton()
        self.back_button_top.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack))
        self.back_button_top.setAutoRaise(True)
        self.back_button_top.setStyleSheet("QToolButton { padding-right: 8px; }")
        self.back_button_top.clicked.connect(self.go_back_to_dashboard.emit)
        header.addWidget(self.back_button_top)
        title_label = QLabel("Budget Analysis & Insights")
        tf = QFont(); tf.setPointSize(26); tf.setBold(True)
        title_label.setFont(tf)
        title_label.setStyleSheet("color: #2c3e50;")
        export_btn = QPushButton("Export Page (PNG/PDF)")
        export_btn.setStyleSheet("background-color: #34495e; color: white; padding: 8px 14px; border: none; border-radius: 6px; font-weight: 600;")
        export_btn.clicked.connect(lambda: save_window_dialog(self))
        header.addWidget(title_label)
        header.addStretch()
        header.addWidget(export_btn)
        layout.addLayout(header)
        
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

        # Income vs Spending tab (Sheng)
        self.income_vs_spending_tab = self.create_income_vs_spending_tab()
        self.tab_widget.addTab(self.income_vs_spending_tab, "Income vs Spending")

        # Forecast tab (Sheng)
        self.forecast_tab = self.create_forecast_tab()
        self.tab_widget.addTab(self.forecast_tab, "Forecast")

        # Subscriptions tab
        self.subscriptions_tab = self.create_subscriptions_tab()
        self.tab_widget.addTab(self.subscriptions_tab, "Subscriptions")
        
        layout.addWidget(self.tab_widget)
        
        # (Removed bottom back button; now in topbar)
        
        self.setLayout(layout)
    
    def create_overview_tab(self):
        """Create the overview tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Month filter dropdown for overview
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Period:"))
        self.overview_month_filter = QComboBox()
        self.overview_month_filter.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                min-width: 200px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #ddd;
                border-radius: 6px;
                selection-background-color: #3498db;
                selection-color: white;
            }
        """)
        self.overview_month_filter.currentTextChanged.connect(self._on_overview_month_filter_changed)
        filter_layout.addWidget(self.overview_month_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
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

    def create_subscriptions_tab(self):
        """List recurring subscription transactions and next due dates if available."""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)

        title = QLabel("Subscriptions")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Month filter dropdown for subscriptions
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Period:"))
        self.subscriptions_month_filter = QComboBox()
        self.subscriptions_month_filter.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                min-width: 200px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #ddd;
                border-radius: 6px;
                selection-background-color: #3498db;
                selection-color: white;
            }
        """)
        self.subscriptions_month_filter.currentTextChanged.connect(self._on_subscriptions_month_filter_changed)
        filter_layout.addWidget(self.subscriptions_month_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self.subs_table = QTableWidget(0, 5)
        self.subs_table.setHorizontalHeaderLabels(["Date", "Description", "Amount", "Next Due", "Notes"])
        header = self.subs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.subs_table)

        tab.setLayout(layout)
        return tab

    def create_income_vs_spending_tab(self):
        """Tab showing aggregated income vs spending using Sheng's summaries."""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)

        title = QLabel("Income vs Spending")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # Month filter dropdown for income vs spending
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Period:"))
        self.income_vs_spending_month_filter = QComboBox()
        self.income_vs_spending_month_filter.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                min-width: 200px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #ddd;
                border-radius: 6px;
                selection-background-color: #3498db;
                selection-color: white;
            }
        """)
        self.income_vs_spending_month_filter.currentTextChanged.connect(self._on_income_vs_spending_month_filter_changed)
        filter_layout.addWidget(self.income_vs_spending_month_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self.ivs_table = QTableWidget(0, 3)
        self.ivs_table.setHorizontalHeaderLabels(["Category", "Amount", "Percent"])
        header = self.ivs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.ivs_table)

        # Launch Sheng's visualizations
        btns = QHBoxLayout()
        open_pie = QPushButton("Open Income vs Spending Pie Chart")
        open_pie.clicked.connect(self._open_income_vs_spending_chart)
        btns.addWidget(open_pie)
        btns.addStretch()
        layout.addLayout(btns)

        tab.setLayout(layout)
        return tab

    def create_forecast_tab(self):
        """Tab showing forecast chart and table using Sheng's forecast_spending."""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)

        title = QLabel("Monthly Spend Forecast")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        # Embedded forecast chart
        self.forecast_chart_view = QChartView()
        self.forecast_chart_view.setMinimumHeight(400)
        self.forecast_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Initialize with empty chart
        empty_chart = QChart()
        empty_chart.setTitle("Monthly Spending Forecast\n(Upload transactions to see forecast)")
        self.forecast_chart_view.setChart(empty_chart)
        layout.addWidget(self.forecast_chart_view)

        # Forecast data table
        table_label = QLabel("Forecast Data")
        table_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #2c3e50; margin-top: 10px;")
        layout.addWidget(table_label)

        self.forecast_table = QTableWidget(0, 2)
        self.forecast_table.setHorizontalHeaderLabels(["Month", "Spending / Forecast ($)"])
        header = self.forecast_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.forecast_table)
        
        tab.setLayout(layout)
        return tab
    
    def create_categories_tab(self):
        """Create the categories breakdown tab"""
        tab = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        
        # Month filter dropdown for categories
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Period:"))
        self.categories_month_filter = QComboBox()
        self.categories_month_filter.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                min-width: 200px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #ddd;
                border-radius: 6px;
                selection-background-color: #3498db;
                selection-color: white;
            }
        """)
        self.categories_month_filter.currentTextChanged.connect(self._on_categories_month_filter_changed)
        filter_layout.addWidget(self.categories_month_filter)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)
        
        # Content layout (pie chart and table)
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
        
        main_layout.addLayout(layout)
        tab.setLayout(main_layout)
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
        
        # Month filter dropdown for budget goals
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Period:"))
        self.goals_month_filter = QComboBox()
        self.goals_month_filter.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                min-width: 200px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #ddd;
                border-radius: 6px;
                selection-background-color: #3498db;
                selection-color: white;
            }
        """)
        self.goals_month_filter.currentTextChanged.connect(self._on_goals_month_filter_changed)
        filter_layout.addWidget(self.goals_month_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Overall goals group
        overall_group = QGroupBox("Overall Goals")
        overall_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold; font-size: 16px; color: #2c3e50;
                border: 2px solid #bdc3c7; border-radius: 8px; padding: 15px; margin-top: 10px;
            }
        """)
        ovl = QVBoxLayout()
        ovl.setSpacing(12)
        
        # Spending limit section
        spending_box = QVBoxLayout()
        spending_label = QLabel("Monthly Spending Limit")
        spending_label.setStyleSheet("font-weight: 600; font-size: 14px; color: #2c3e50;")
        spending_box.addWidget(spending_label)
        
        self.period_label = QLabel("")
        self.period_label.setStyleSheet("font-size: 12px; color: #7f8c8d; font-style: italic;")
        spending_box.addWidget(self.period_label)
        
        row_spend = QHBoxLayout()
        self.spend_current_label = QLabel("Spent: $0.00")
        self.spend_limit_label = QLabel("Limit: —")
        self.spend_remaining_label = QLabel("Remaining: —")
        row_spend.addWidget(self.spend_current_label)
        row_spend.addStretch()
        row_spend.addWidget(self.spend_limit_label)
        row_spend.addStretch()
        row_spend.addWidget(self.spend_remaining_label)
        spending_box.addLayout(row_spend)
        
        self.spending_progress = QProgressBar()
        self.spending_progress.setMinimum(0)
        self.spending_progress.setMaximum(100)
        self.spending_progress.setFormat("%p%")
        spending_box.addWidget(self.spending_progress)
        ovl.addLayout(spending_box)
        
        # Savings goal section
        savings_box = QVBoxLayout()
        savings_label = QLabel("Monthly Savings Goal")
        savings_label.setStyleSheet("font-weight: 600; font-size: 14px; color: #2c3e50;")
        savings_box.addWidget(savings_label)
        
        row_save = QHBoxLayout()
        self.save_current_label = QLabel("Saved: $0.00")
        self.save_goal_label = QLabel("Goal: —")
        self.save_progress_label = QLabel("Progress: —")
        row_save.addWidget(self.save_current_label)
        row_save.addStretch()
        row_save.addWidget(self.save_goal_label)
        row_save.addStretch()
        row_save.addWidget(self.save_progress_label)
        savings_box.addLayout(row_save)
        
        self.savings_progress = QProgressBar()
        self.savings_progress.setMinimum(0)
        self.savings_progress.setMaximum(100)
        self.savings_progress.setFormat("%p%")
        savings_box.addWidget(self.savings_progress)
        ovl.addLayout(savings_box)
        
        overall_group.setLayout(ovl)
        layout.addWidget(overall_group)

        # Per-category group
        percat_group = QGroupBox("Per-Category Limits")
        percat_group.setStyleSheet("""
            QGroupBox { font-weight: bold; font-size: 16px; color: #2c3e50; border: 2px solid #bdc3c7; border-radius: 8px; padding: 15px; }
        """)
        self.percat_table = QTableWidget(0, 5)
        self.percat_table.setHorizontalHeaderLabels(["Category", "Limit ($)", "Spent ($)", "Remaining ($)", "Progress"])
        ph = self.percat_table.horizontalHeader()
        ph.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        ph.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        ph.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        ph.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        ph.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        pc_layout = QVBoxLayout()
        pc_layout.addWidget(self.percat_table)
        percat_group.setLayout(pc_layout)
        layout.addWidget(percat_group)
        
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
    
    def _populate_month_filters(self):
        """Populate all month filter dropdowns with available months"""
        if not self.user or not self.user.transactions:
            return
        
        transactions = self.user.transactions
        
        # Get unique months (both by date and statement_month)
        date_months = set()
        for t in transactions:
            month_key = t.date.strftime("%Y-%m")
            month_name = t.date.strftime("%B %Y")  # e.g., "January 2025"
            date_months.add((month_key, month_name))
        
        # Add statement months if they exist
        statement_months = set()
        for t in transactions:
            if t.statement_month:
                statement_months.add(t.statement_month)
        
        # Sort date months chronologically (most recent first)
        sorted_date_months = sorted(date_months, key=lambda x: x[0], reverse=True)
        
        # Month options dictionary
        month_options = {"All Time": None}
        
        # Add date-based months
        for month_key, month_name in sorted_date_months:
            month_options[month_name] = ("date", month_key)
        
        # Add statement months (prefixed with "Statement: ")
        for stmt_month in sorted(statement_months, reverse=True):
            display_name = f"Statement: {stmt_month}"
            month_options[display_name] = ("statement", stmt_month)
        
        # Store options for filtering
        self._month_filter_options = month_options
        
        # Populate all month filters
        filters = []
        if hasattr(self, 'overview_month_filter'):
            filters.append(self.overview_month_filter)
        if hasattr(self, 'categories_month_filter'):
            filters.append(self.categories_month_filter)
        if hasattr(self, 'goals_month_filter'):
            filters.append(self.goals_month_filter)
        if hasattr(self, 'income_vs_spending_month_filter'):
            filters.append(self.income_vs_spending_month_filter)
        if hasattr(self, 'subscriptions_month_filter'):
            filters.append(self.subscriptions_month_filter)
        
        for month_filter in filters:
            month_filter.clear()
            month_filter.addItem("All Time")
            # Add date months first
            for month_key, month_name in sorted_date_months:
                month_filter.addItem(month_name)
            # Add statement months
            for stmt_month in sorted(statement_months, reverse=True):
                display_name = f"Statement: {stmt_month}"
                month_filter.addItem(display_name)
    
    def _filter_transactions_by_month(self, transactions, filter_widget):
        """Filter transactions based on selected month in the given filter widget"""
        if not hasattr(self, '_month_filter_options') or not filter_widget:
            return transactions
        
        selected = filter_widget.currentText()
        if selected == "All Time":
            return transactions
        
        filter_info = self._month_filter_options.get(selected)
        if not filter_info:
            return transactions
        
        filter_type, filter_value = filter_info
        
        if filter_type == "date":
            # Filter by date (YYYY-MM)
            year, month = map(int, filter_value.split("-"))
            return [t for t in transactions if t.date.year == year and t.date.month == month]
        elif filter_type == "statement":
            # Filter by statement_month
            return [t for t in transactions if t.statement_month == filter_value]
        
        return transactions
    
    def _on_overview_month_filter_changed(self, text):
        """Handle overview month filter change"""
        self.update_analysis()
    
    def _on_categories_month_filter_changed(self, text):
        """Handle categories month filter change"""
        if not self.user or not self.user.transactions:
            return
        transactions = self.user.transactions
        filtered = self._filter_transactions_by_month(transactions, self.categories_month_filter)
        self.update_category_breakdown(filtered)
    
    def _on_goals_month_filter_changed(self, text):
        """Handle budget goals month filter change"""
        if not self.user or not self.user.transactions:
            return
        transactions = self.user.transactions
        filtered = self._filter_transactions_by_month(transactions, self.goals_month_filter)
        self.update_goals_view(filtered)
    
    def _on_income_vs_spending_month_filter_changed(self, text):
        """Handle income vs spending month filter change"""
        if not self.user or not self.user.transactions:
            return
        transactions = self.user.transactions
        filtered = self._filter_transactions_by_month(transactions, self.income_vs_spending_month_filter)
        self.update_income_vs_spending(filtered)
    
    def _on_subscriptions_month_filter_changed(self, text):
        """Handle subscriptions month filter change"""
        if not self.user or not self.user.transactions:
            return
        transactions = self.user.transactions
        filtered = self._filter_transactions_by_month(transactions, self.subscriptions_month_filter)
        self.update_subscriptions(filtered)
    
    def update_analysis(self):
        """Update all analysis data"""
        if not self.user or not self.user.transactions:
            return
        
        # Populate month filters if not already done
        if hasattr(self, 'overview_month_filter') and self.overview_month_filter.count() == 0:
            self._populate_month_filters()
        
        all_transactions = self.user.transactions
        
        # Filter transactions by selected month for overview
        transactions = self._filter_transactions_by_month(all_transactions, 
                                                          getattr(self, 'overview_month_filter', None))
        
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
        
        # Update monthly trends (uses all transactions to show trends across months)
        self.update_monthly_trends(self.user.transactions)

        # Update income vs spending (Sheng) - filtered by month
        if hasattr(self, 'income_vs_spending_month_filter'):
            income_vs_spend_filtered = self._filter_transactions_by_month(self.user.transactions, 
                                                                          self.income_vs_spending_month_filter)
            # Sync filter with overview if needed
            if self.income_vs_spending_month_filter.currentText() == "All Time":
                overview_selected = getattr(self.overview_month_filter, 'currentText', lambda: "All Time")() if hasattr(self, 'overview_month_filter') else "All Time"
                if overview_selected != "All Time":
                    self.income_vs_spending_month_filter.setCurrentText(overview_selected)
                    income_vs_spend_filtered = self._filter_transactions_by_month(self.user.transactions,
                                                                                  self.income_vs_spending_month_filter)
            self.update_income_vs_spending(income_vs_spend_filtered)
        else:
            self.update_income_vs_spending(transactions)

        # Update forecast (Sheng) - uses all transactions for forecasting
        self.update_forecast(self.user.transactions)

        # Update subscriptions view - filtered by month
        if hasattr(self, 'subscriptions_month_filter'):
            subs_filtered = self._filter_transactions_by_month(self.user.transactions,
                                                                self.subscriptions_month_filter)
            # Sync filter with overview if needed
            if self.subscriptions_month_filter.currentText() == "All Time":
                overview_selected = getattr(self.overview_month_filter, 'currentText', lambda: "All Time")() if hasattr(self, 'overview_month_filter') else "All Time"
                if overview_selected != "All Time":
                    self.subscriptions_month_filter.setCurrentText(overview_selected)
                    subs_filtered = self._filter_transactions_by_month(self.user.transactions,
                                                                        self.subscriptions_month_filter)
            self.update_subscriptions(subs_filtered)
        else:
            self.update_subscriptions(transactions)

        # Update goals/limits view - filtered by month (for monthly budgets, use all-time for cumulative)
        if hasattr(self, 'goals_month_filter'):
            goals_filtered = self._filter_transactions_by_month(self.user.transactions,
                                                                 self.goals_month_filter)
            # Sync filter with overview if needed
            if self.goals_month_filter.currentText() == "All Time":
                overview_selected = getattr(self.overview_month_filter, 'currentText', lambda: "All Time")() if hasattr(self, 'overview_month_filter') else "All Time"
                if overview_selected != "All Time":
                    self.goals_month_filter.setCurrentText(overview_selected)
                    goals_filtered = self._filter_transactions_by_month(self.user.transactions,
                                                                        self.goals_month_filter)
            # For goals view, if "All Time" selected, use all transactions for cumulative savings
            # Otherwise, use filtered transactions for monthly view
            if self.goals_month_filter.currentText() == "All Time":
                self.update_goals_view(self.user.transactions)
            else:
                self.update_goals_view(goals_filtered)
        else:
            # Default: use all transactions for cumulative calculation
            self.update_goals_view(self.user.transactions)
        
        # Update category breakdown with filtered transactions
        # Categories will update separately if user changes its filter, otherwise sync with overview
        if hasattr(self, 'categories_month_filter'):
            # Sync categories filter with overview filter if not changed by user
            overview_text = getattr(self, 'overview_month_filter', None)
            if overview_text:
                overview_selected = overview_text.currentText()
                # Set categories filter to match overview filter
                if self.categories_month_filter.currentText() != overview_selected:
                    self.categories_month_filter.setCurrentText(overview_selected)
                # Update with filtered transactions
                filtered = self._filter_transactions_by_month(self.user.transactions, 
                                                              self.categories_month_filter)
                self.update_category_breakdown(filtered)
        else:
            # Fallback if categories filter doesn't exist yet
            self.update_category_breakdown(transactions)
        
    def update_goals_view(self, transactions: list):
        from datetime import datetime as _dt
        from collections import defaultdict
        now = _dt.now()
        
        # Determine period text based on filter selection or transactions
        # Initialize target_year and target_month to None
        target_year = None
        target_month = None
        
        if hasattr(self, 'goals_month_filter') and self.goals_month_filter.currentText():
            filter_text = self.goals_month_filter.currentText()
            if filter_text == "All Time":
                period_text = "Showing data for: All Time (Cumulative)"
                # For "All Time", use most recent transaction date
                if transactions:
                    most_recent_date = max(t.date for t in transactions)
                    target_year = most_recent_date.year
                    target_month = most_recent_date.month
            else:
                period_text = f"Showing data for: {filter_text}"
                # Extract year and month from filter
                if hasattr(self, '_month_filter_options') and filter_text in self._month_filter_options:
                    filter_info = self._month_filter_options[filter_text]
                    if filter_info:
                        filter_type, filter_value = filter_info
                        if filter_type == "date":
                            # Filter value is "YYYY-MM"
                            target_year, target_month = map(int, filter_value.split("-"))
                        elif filter_type == "statement":
                            # For statement-based filters, find the date from transactions
                            if transactions:
                                statement_transactions = [t for t in transactions if t.statement_month == filter_value]
                                if statement_transactions:
                                    most_recent_date = max(t.date for t in statement_transactions)
                                    target_year = most_recent_date.year
                                    target_month = most_recent_date.month
        else:
            # Fallback: Find the most recent statement_month or date
            latest_statement_month = None
            if transactions:
                # Group transactions by statement_month
                statement_groups = defaultdict(list)
                for t in transactions:
                    stmt_month = t.statement_month or "Uncategorized"
                    statement_groups[stmt_month].append(t.date)
                
                if statement_groups:
                    # Find the statement_month with the most recent date
                    latest_date = None
                    for stmt_month, dates in statement_groups.items():
                        if dates:
                            max_date = max(dates)
                            if latest_date is None or max_date > latest_date:
                                latest_date = max_date
                                latest_statement_month = stmt_month
                    
                    if latest_statement_month:
                        # Get dates for this statement
                        latest_dates = statement_groups[latest_statement_month]
                        most_recent_date = max(latest_dates)
                        target_year = most_recent_date.year
                        target_month = most_recent_date.month
                        month_names = ["January", "February", "March", "April", "May", "June",
                                      "July", "August", "September", "October", "November", "December"]
                        period_text = f"Showing data for: {latest_statement_month} ({month_names[target_month - 1]} {target_year})"
                    else:
                        # Fallback to latest date if no statement_month
                        most_recent_date = max(t.date for t in transactions)
                        target_year = most_recent_date.year
                        target_month = most_recent_date.month
                        month_names = ["January", "February", "March", "April", "May", "June",
                                      "July", "August", "September", "October", "November", "December"]
                        period_text = f"Showing data for: {month_names[target_month - 1]} {target_year}"
                else:
                    most_recent_date = max(t.date for t in transactions)
                    target_year = most_recent_date.year
                    target_month = most_recent_date.month
                    month_names = ["January", "February", "March", "April", "May", "June",
                                  "July", "August", "September", "October", "November", "December"]
                    period_text = f"Showing data for: {month_names[target_month - 1]} {target_year}"
            else:
                period_text = "No transactions found"
        
        # Update period label
        if hasattr(self, 'period_label'):
            self.period_label.setText(period_text)
        
        # Calculate income and spending from the transactions passed
        # If "All Time" is selected, transactions will be all transactions (cumulative)
        # Otherwise, transactions will be filtered to the selected period (monthly view)
        month_spend = sum(float(abs(t.amount)) for t in transactions if t.amount < 0)
        month_income = sum(float(t.amount) for t in transactions if t.amount > 0)
        
        month_saved = month_income - month_spend
        
        # Spending limit section
        limit = getattr(self.user, 'monthly_spending_limit', None)
        if limit and limit > 0:
            limit_float = float(limit)
            self.spend_current_label.setText(f"Spent: ${month_spend:.2f}")
            self.spend_limit_label.setText(f"Limit: ${limit_float:.2f}")
            remaining = max(0, limit_float - month_spend)
            self.spend_remaining_label.setText(f"Remaining: ${remaining:.2f}")
            used_pct = int(min(100, (month_spend / limit_float * 100)))
            self.spending_progress.setValue(used_pct)
            # Color progress bar based on usage
            if used_pct >= 100:
                self.spending_progress.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")
            elif used_pct >= 75:
                self.spending_progress.setStyleSheet("QProgressBar::chunk { background-color: #f39c12; }")
            else:
                self.spending_progress.setStyleSheet("QProgressBar::chunk { background-color: #27ae60; }")
        else:
            self.spend_current_label.setText(f"Spent: ${month_spend:.2f}")
            self.spend_limit_label.setText("Limit: Not set")
            self.spend_remaining_label.setText("Remaining: —")
            self.spending_progress.setValue(0)
        
        # Savings goal section
        goal = getattr(self.user, 'monthly_savings_goal', None)
        if goal and goal > 0:
            goal_float = float(goal)
            self.save_current_label.setText(f"Saved: ${month_saved:.2f}")
            self.save_goal_label.setText(f"Goal: ${goal_float:.2f}")
            goal_pct = int(min(100, max(0, (month_saved / goal_float * 100))))
            self.save_progress_label.setText(f"Progress: {goal_pct}%")
            self.savings_progress.setValue(goal_pct)
            # Color progress bar based on achievement
            if goal_pct >= 100:
                self.savings_progress.setStyleSheet("QProgressBar::chunk { background-color: #27ae60; }")
            elif goal_pct >= 50:
                self.savings_progress.setStyleSheet("QProgressBar::chunk { background-color: #3498db; }")
            else:
                self.savings_progress.setStyleSheet("QProgressBar::chunk { background-color: #e67e22; }")
        else:
            self.save_current_label.setText(f"Saved: ${month_saved:.2f}")
            self.save_goal_label.setText("Goal: Not set")
            self.save_progress_label.setText("Progress: —")
            self.savings_progress.setValue(0)

        # Per-category table: compare limits to month spend
        per_limits = getattr(self.user, 'per_category_limits', {}) or {}
        # compute spend per category for target month (case-insensitive matching)
        cat_spend = defaultdict(float)
        cat_spend_lower = {}  # map lowercase category -> original category
        
        # Only process if target_year and target_month are set
        if target_year is not None and target_month is not None:
            for t in transactions:
                if t.amount < 0 and t.date.year == target_year and t.date.month == target_month:
                    cat_lower = t.category.lower()
                    cat_spend[cat_lower] += float(abs(t.amount))
                    if cat_lower not in cat_spend_lower:
                        cat_spend_lower[cat_lower] = t.category
        
        self.percat_table.setRowCount(len(per_limits))
        for r, (cat, lim) in enumerate(per_limits.items()):
            # Try exact match first, then case-insensitive match
            spent = cat_spend.get(cat, 0.0)
            if spent == 0.0:
                spent = cat_spend.get(cat.lower(), 0.0)
            lim_float = float(lim)
            remaining = max(0, lim_float - spent)
            used_pct = int(min(100, (spent / lim_float * 100) if lim_float > 0 else 0))
            
            self.percat_table.setItem(r, 0, QTableWidgetItem(cat))
            self.percat_table.setItem(r, 1, QTableWidgetItem(f"${lim_float:.2f}"))
            self.percat_table.setItem(r, 2, QTableWidgetItem(f"${spent:.2f}"))
            self.percat_table.setItem(r, 3, QTableWidgetItem(f"${remaining:.2f}"))
            
            # Progress bar widget
            progress_bar = QProgressBar()
            progress_bar.setMinimum(0)
            progress_bar.setMaximum(100)
            progress_bar.setValue(used_pct)
            progress_bar.setFormat(f"{used_pct}%")
            progress_bar.setTextVisible(True)
            # Color based on usage
            if used_pct >= 100:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")
            elif used_pct >= 75:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #f39c12; }")
            else:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #27ae60; }")
            self.percat_table.setCellWidget(r, 4, progress_bar)

    def _open_income_vs_spending_chart(self):
        try:
            from core.view_spending import show_pie, income_summary
            data = income_summary(self.user.transactions)
            show_pie(data)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Chart Error", f"Failed to open chart: {e}")

    def _build_forecast_chart(self, forecast_data: list[dict]):
        """Build and display forecast chart widget"""
        if not hasattr(self, 'forecast_chart_view'):
            return
        try:
            from decimal import Decimal
            
            months = []
            values = []
            forecast_value = Decimal("0.00")

            for row in forecast_data:
                if "forecast_next_month" in row:
                    forecast_value = row["forecast_next_month"]
                elif "month" in row and "spending" in row:
                    months.append(row["month"])
                    values.append(float(row["spending"]))

            if len(months) == 0:
                # Show empty chart message
                chart = QChart()
                chart.setTitle("Monthly Spending Forecast\n(No historical data available)")
                self.forecast_chart_view.setChart(chart)
                return

            # Create line series for past data
            line_series = QLineSeries()
            for i, val in enumerate(values):
                line_series.append(i, val)
            line_series.append(len(values), float(forecast_value))

            # Create scatter series for actual spending (blue points)
            scatter_actual = QScatterSeries()
            scatter_actual.setName("Previous Spending")
            scatter_actual.setMarkerShape(QScatterSeries.MarkerShape.MarkerShapeCircle)
            scatter_actual.setColor(QColor("blue"))
            scatter_actual.setBorderColor(QColor("blue"))
            scatter_actual.setMarkerSize(10)
            for i, val in enumerate(values):
                scatter_actual.append(i, val)

            # Create scatter series for forecast (yellow point)
            scatter_forecast = QScatterSeries()
            scatter_forecast.setName("Forecast For Next Month")
            scatter_forecast.setMarkerShape(QScatterSeries.MarkerShape.MarkerShapeCircle)
            scatter_forecast.setColor(QColor("yellow"))
            scatter_forecast.setBorderColor(QColor("orange"))
            scatter_forecast.setMarkerSize(12)
            scatter_forecast.append(len(values), float(forecast_value))

            # Create chart
            chart = QChart()
            chart.addSeries(line_series)
            if chart.legend().markers(line_series):
                chart.legend().markers(line_series)[0].setVisible(False)
            chart.addSeries(scatter_actual)
            chart.addSeries(scatter_forecast)
            chart.setTitle("Monthly Spending Forecast")

            # X axis (category axis with month labels)
            axis_x = QCategoryAxis()
            axis_x.setTitleText("Month")
            for i, month in enumerate(months):
                axis_x.append(month, i)
            axis_x.append("Forecast", len(values))
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)

            # Y axis (value axis for spending)
            axis_y = QValueAxis()
            axis_y.setTitleText("Spending ($)")
            y_min = min(values + [float(forecast_value)]) * 0.9
            y_max = max(values + [float(forecast_value)]) * 1.1
            if y_min < 0:
                y_min = 0
            axis_y.setRange(y_min, y_max)
            chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)

            # Attach series to axes
            line_series.attachAxis(axis_x)
            line_series.attachAxis(axis_y)
            scatter_actual.attachAxis(axis_x)
            scatter_actual.attachAxis(axis_y)
            scatter_forecast.attachAxis(axis_x)
            scatter_forecast.attachAxis(axis_y)

            # Set chart to view
            self.forecast_chart_view.setChart(chart)
            
        except Exception as e:
            # Show error message in chart
            chart = QChart()
            chart.setTitle(f"Error loading forecast chart: {str(e)}")
            self.forecast_chart_view.setChart(chart)
    
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
            insights.append(f"Top expense category: <b>{top_category[0]}</b> — ${top_category[1]:.2f}")
        
        # Recent spending trend
        recent_transactions = [t for t in transactions if t.date >= datetime.now() - timedelta(days=30)]
        if recent_transactions:
            recent_spending = sum(abs(t.amount) for t in recent_transactions if t.amount < 0)
            insights.append(f"Last 30 days spending: ${recent_spending:.2f}")
        
        # Income vs spending
        total_spending = sum(abs(t.amount) for t in transactions if t.amount < 0)
        total_income = sum(t.amount for t in transactions if t.amount > 0)
        if total_income > 0:
            spending_ratio = (total_spending / total_income) * 100
            insights.append(f"Spending {spending_ratio:.1f}% of income")
        
        # Transaction frequency
        if len(transactions) > 0:
            avg_per_day = len(transactions) / max(1, (datetime.now() - min(t.date for t in transactions)).days)
            insights.append(f"Average {avg_per_day:.1f} transactions per day")
        
        return "<br>".join(insights) if insights else "Upload more transactions to see detailed insights!"
    
    def update_category_breakdown(self, transactions: list = None):
        """Update category breakdown chart and table"""
        if transactions is None:
            if not self.user or not self.user.transactions:
                return
            # Get filtered transactions for categories
            all_transactions = self.user.transactions
            transactions = self._filter_transactions_by_month(all_transactions,
                                                              getattr(self, 'categories_month_filter', None))
            # Populate filter if needed
            if hasattr(self, 'categories_month_filter') and self.categories_month_filter.count() == 0:
                self._populate_month_filters()
        
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

    def update_income_vs_spending(self, transactions: list):
        rows = income_summary(transactions)
        self.ivs_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.ivs_table.setItem(r, 0, QTableWidgetItem(str(row.get("category", ""))))
            self.ivs_table.setItem(r, 1, QTableWidgetItem(f"${float(row.get('amount', 0)):.2f}"))
            self.ivs_table.setItem(r, 2, QTableWidgetItem(f"{float(row.get('percent', 0)):.2f}%"))

    def update_forecast(self, transactions: list):
        rows = forecast_spending(transactions)
        
        # Update embedded chart
        self._build_forecast_chart(rows)
        
        # Update forecast table
        # count months + 1 for forecast row
        self.forecast_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            if "month" in row:
                self.forecast_table.setItem(r, 0, QTableWidgetItem(row["month"]))
                self.forecast_table.setItem(r, 1, QTableWidgetItem(f"${float(row['spending']):.2f}"))
            else:
                self.forecast_table.setItem(r, 0, QTableWidgetItem("Forecast (Next Month)"))
                self.forecast_table.setItem(r, 1, QTableWidgetItem(f"${float(row['forecast_next_month']):.2f}"))

    def update_subscriptions(self, transactions: list):
        subs = []
        for t in transactions:
            is_sub = getattr(t, 'is_subscription', False) or t.category.lower() == 'subscriptions'
            if is_sub:
                subs.append(t)

        self.subs_table.setRowCount(len(subs))
        for r, t in enumerate(sorted(subs, key=lambda x: x.date, reverse=True)):
            self.subs_table.setItem(r, 0, QTableWidgetItem(t.date.strftime('%Y-%m-%d')))
            self.subs_table.setItem(r, 1, QTableWidgetItem(t.description))
            self.subs_table.setItem(r, 2, QTableWidgetItem(f"-${abs(t.amount):.2f}"))
            nd = getattr(t, 'next_due_date', None)
            self.subs_table.setItem(r, 3, QTableWidgetItem(nd.strftime('%Y-%m-%d') if nd else "-"))
            self.subs_table.setItem(r, 4, QTableWidgetItem(t.notes or ""))
