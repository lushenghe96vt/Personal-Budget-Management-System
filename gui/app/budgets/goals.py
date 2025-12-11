"""
Goals Tab Component
Personal Budget Management System – Budget Goals Tracking

Provides the goals tab for tracking spending limits and savings goals.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QScrollArea
)
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from core.models import Transaction
from core.analytics.goals import (
    check_spending_limit, check_savings_goal,
    get_per_category_limits_status
)
from core.analytics.months import filter_transactions_by_month
from gui.widgets.month_filter import MonthFilter
from gui.widgets.components import SectionCard
from gui.widgets.metric_card import MetricCard
from gui.app.style import Styles


class GoalsTab(QWidget):
    """Goals tab for tracking budget goals and limits."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.transactions: List[Transaction] = []
        self.user = None
        self._build_ui()
    
    def _build_ui(self):
        outer_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(24)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Month filter
        self.month_filter = MonthFilter()
        self.month_filter.filter_changed.connect(self._on_filter_changed)
        layout.addWidget(self.month_filter)
        
        # Period indicator
        self.period_label = QLabel("")
        self.period_label.setStyleSheet(Styles.LABEL_INFO)
        layout.addWidget(self.period_label)
        
        # Content layout (overall goals left, table right)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Overall Goals Section (left side)
        overall_section = SectionCard("Overall Budget Goals")
        overall_section.setStyleSheet(Styles.GROUPBOX)
        
        self.streak_card = MetricCard("Savings Goal Streak", "No data", "neutral", small_font=True)
        overall_section.content_layout.addWidget(self.streak_card)

        self.weekly_card = MetricCard("Weekly Spending", "$0.00", "neutral", small_font=True)
        overall_section.content_layout.addWidget(self.weekly_card)

        # Spending Limit Card
        spending_card = SectionCard("Monthly Spending Limit")
        spending_card.setStyleSheet(Styles.GROUPBOX)
        
        self.spend_metric_card = MetricCard("Spent", "$0.00", "danger")
        # Ensure metric card can display full amounts
        self.spend_metric_card.setMinimumWidth(200)
        spending_card.content_layout.addWidget(self.spend_metric_card)
        
        spending_details = QHBoxLayout()
        self.spend_limit_label = QLabel("Limit: Not set")
        self.spend_limit_label.setStyleSheet(Styles.LABEL_BODY)
        self.spend_remaining_label = QLabel("Remaining: —")
        self.spend_remaining_label.setStyleSheet(Styles.LABEL_BODY)
        spending_details.addWidget(self.spend_limit_label)
        spending_details.addStretch()
        spending_details.addWidget(self.spend_remaining_label)
        spending_card.content_layout.addLayout(spending_details)
        
        self.spending_progress = QProgressBar()
        self.spending_progress.setMinimum(0)
        self.spending_progress.setMaximum(100)
        self.spending_progress.setFormat("%p%")
        self.spending_progress.setMinimumHeight(24)
        self.spending_progress.setMaximumHeight(24)
        # Set initial style
        self.spending_progress.setStyleSheet(Styles.PROGRESS_BAR)
        spending_card.content_layout.addWidget(self.spending_progress)
        
        # Savings Goal Card
        savings_card = SectionCard("Monthly Savings Goal")
        savings_card.setStyleSheet(Styles.GROUPBOX)
        
        self.save_metric_card = MetricCard("Saved", "$0.00", "success")
        # Ensure metric card can display full amounts
        self.save_metric_card.setMinimumWidth(200)
        savings_card.content_layout.addWidget(self.save_metric_card)
        
        savings_details = QHBoxLayout()
        self.save_goal_label = QLabel("Goal: Not set")
        self.save_goal_label.setStyleSheet(Styles.LABEL_BODY)
        self.save_progress_label = QLabel("Progress: —")
        self.save_progress_label.setStyleSheet(Styles.LABEL_BODY)
        savings_details.addWidget(self.save_goal_label)
        savings_details.addStretch()
        savings_details.addWidget(self.save_progress_label)
        savings_card.content_layout.addLayout(savings_details)
        
        self.savings_progress = QProgressBar()
        self.savings_progress.setMinimum(0)
        self.savings_progress.setMaximum(100)
        self.savings_progress.setFormat("%p%")
        self.savings_progress.setMinimumHeight(24)
        self.savings_progress.setMaximumHeight(24)
        # Set initial style
        self.savings_progress.setStyleSheet(Styles.PROGRESS_BAR)
        savings_card.content_layout.addWidget(self.savings_progress)
        
        # Add cards to overall section in a column
        goals_column = QVBoxLayout()
        goals_column.setSpacing(16)
        goals_column.addWidget(spending_card)
        goals_column.addWidget(savings_card)
        overall_section.content_layout.addLayout(goals_column)
        
        content_layout.addWidget(overall_section, 1)  # 50% width
        
        # Per-Category Limits Section (right side)
        percat_section = SectionCard("Per-Category Spending Limits")
        percat_section.setStyleSheet(Styles.GROUPBOX)
        
        self.percat_table = QTableWidget(0, 5)
        self.percat_table.setHorizontalHeaderLabels([
            "Category", "Limit ($)", "Spent ($)", "Remaining ($)", "Progress"
        ])
        self.percat_table.setStyleSheet(Styles.TABLE)
        ph = self.percat_table.horizontalHeader()
        ph.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        ph.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        ph.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        ph.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        ph.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        # Set minimum column widths to prevent text cutoff
        self.percat_table.setColumnWidth(1, 100)  # Limit column
        self.percat_table.setColumnWidth(2, 100)  # Spent column
        self.percat_table.setColumnWidth(3, 120)  # Remaining column
        self.percat_table.setColumnWidth(4, 150)  # Progress column
        
        percat_section.add_widget(self.percat_table)
        content_layout.addWidget(percat_section, 1)  # 50% width
        
        layout.addLayout(content_layout)
        layout.addStretch()

        scroll.setWidget(content_widget)
        outer_layout.addWidget(scroll)
    
    def set_user_and_transactions(self, user, transactions: List[Transaction]):
        """Update user and transactions, then refresh display."""
        self.user = user
        self.transactions = transactions
        self.month_filter.populate_from_transactions(transactions)
        self._update_display()
    
    def _on_filter_changed(self, filter_text: str):
        """Handle month filter change."""
        self._update_display()
    
    def _update_display(self):
        """Update goals view based on current filter."""
        # Get filtered transactions
        filter_info = self.month_filter.get_filter_info()
        selected_text = self.month_filter.combo.currentText()
        
        if filter_info is None:
            # "All Time" is selected - use all transactions
            if selected_text == "All Time":
                filtered = self.transactions
                target_year, target_month = None, None
            else:
                # Default to current month if no filter selected (shouldn't happen normally)
                from datetime import datetime
                now = datetime.now()
                filtered = filter_transactions_by_month(self.transactions, year=now.year, month=now.month)
                target_year, target_month = now.year, now.month
        else:
            filter_type, filter_value = filter_info
            if filter_type == "date":
                year, month = map(int, filter_value.split("-"))
                filtered = filter_transactions_by_month(self.transactions, year=year, month=month)
                target_year, target_month = year, month
            elif filter_type == "statement":
                filtered = filter_transactions_by_month(self.transactions, statement_month=filter_value)
                # Find most recent date from filtered transactions
                if filtered:
                    most_recent = max(t.date for t in filtered)
                    target_year, target_month = most_recent.year, most_recent.month
                else:
                    target_year, target_month = None, None
            else:
                # Unknown filter type - use all transactions
                filtered = self.transactions
                target_year, target_month = None, None
        
        # Update period label
        period_text = f"Showing data for: {self.month_filter.combo.currentText()}"
        self.period_label.setText(period_text)
        
        if not self.user:
            return
        
        streak_count = getattr(self.user, "goal_streak_count", 0)
        if streak_count and streak_count > 0:
            self.streak_card.set_value(f"{streak_count} month(s)")
            self.streak_card.set_variant("success")
        else:
            self.streak_card.set_value("No active streak")
            self.streak_card.set_variant("neutral")

        weekly_limit = getattr(self.user, "weekly_spending_limit", None)
        weekly_data = self._calculate_weekly_spending(filtered, target_year, target_month)
        if weekly_limit and weekly_limit > 0:
            weekly_spent = weekly_data["spent"]
            ratio = (weekly_spent / weekly_limit) * 100 if weekly_limit else 0
            self.weekly_card.set_value(f"${weekly_spent:.2f} of ${weekly_limit:.2f}")
            if ratio >= 100:
                self.weekly_card.set_variant("danger")
            elif ratio >= 75:
                self.weekly_card.set_variant("warning")
            else:
                self.weekly_card.set_variant("info")
        else:
            self.weekly_card.set_value("No weekly limit")
            self.weekly_card.set_variant("neutral")
        
        # Calculate number of months for "All Time" view
        num_months = 1  # Default to 1 month for specific month filters
        if selected_text == "All Time" and filtered:
            # Count unique months in filtered transactions
            from core.analytics.months import group_transactions_by_month
            monthly_groups = group_transactions_by_month(filtered)
            num_months = len(monthly_groups) if monthly_groups else 1
        
        # Check spending limit
        spending_limit = getattr(self.user, 'monthly_spending_limit', None)
        # For "All Time", multiply monthly limit by number of months
        if selected_text == "All Time" and spending_limit is not None:
            from decimal import Decimal
            if not isinstance(spending_limit, Decimal):
                spending_limit = Decimal(str(spending_limit))
            spending_limit = spending_limit * Decimal(str(num_months))
        
        # Don't pass year/month since we already filtered the transactions
        spending_status = check_spending_limit(
            filtered, spending_limit
        )
        
        # Update spending limit card
        spent = float(spending_status['spent'])
        self.spend_metric_card.set_value(f"${spent:.2f}")
        if spending_status['limit'] is not None:
            limit = float(spending_status['limit'])
            remaining = float(spending_status['remaining'])
            self.spend_limit_label.setText(f"Limit: ${limit:.2f}")
            self.spend_remaining_label.setText(f"Remaining: ${remaining:.2f}")
            self.spending_progress.setValue(spending_status['used_percent'])
            self.spending_progress.setStyleSheet(
                Styles.PROGRESS_BAR + Styles.get_progress_bar_style(spending_status['used_percent'])
            )
        else:
            self.spend_limit_label.setText("Limit: Not set")
            self.spend_remaining_label.setText("Remaining: —")
            self.spending_progress.setValue(0)
        
        # Check savings goal
        savings_goal = getattr(self.user, 'monthly_savings_goal', None)
        # For "All Time", multiply monthly goal by number of months
        if selected_text == "All Time" and savings_goal is not None:
            from decimal import Decimal
            if not isinstance(savings_goal, Decimal):
                savings_goal = Decimal(str(savings_goal))
            savings_goal = savings_goal * Decimal(str(num_months))
        
        # Don't pass year/month since we already filtered the transactions
        savings_status = check_savings_goal(
            filtered, savings_goal
        )
        
        # Update savings goal card
        saved = float(savings_status['saved'])
        self.save_metric_card.set_value(f"${saved:.2f}")
        if savings_status['goal'] is not None:
            goal = float(savings_status['goal'])
            self.save_goal_label.setText(f"Goal: ${goal:.2f}")
            self.save_progress_label.setText(f"Progress: {savings_status['progress_percent']}%")
            self.savings_progress.setValue(savings_status['progress_percent'])
            self.savings_progress.setStyleSheet(
                Styles.PROGRESS_BAR + Styles.get_savings_progress_style(savings_status['progress_percent'])
            )
        else:
            self.save_goal_label.setText("Goal: Not set")
            self.save_progress_label.setText("Progress: —")
            self.savings_progress.setValue(0)
        
        # Per-category limits
        per_limits = getattr(self.user, 'per_category_limits', {}) or {}
        if per_limits:
            cat_status = get_per_category_limits_status(
                filtered, per_limits, target_year, target_month
            )
            
            self.percat_table.setRowCount(len(cat_status))
            for row, (cat, status) in enumerate(cat_status.items()):
                self.percat_table.setItem(row, 0, QTableWidgetItem(cat))
                self.percat_table.setItem(row, 1, QTableWidgetItem(f"${status['limit']:.2f}"))
                self.percat_table.setItem(row, 2, QTableWidgetItem(f"${status['spent']:.2f}"))
                self.percat_table.setItem(row, 3, QTableWidgetItem(f"${status['remaining']:.2f}"))
                
                pb = QProgressBar()
                pb.setMinimum(0)
                pb.setMaximum(100)
                pb.setValue(status['used_percent'])
                pb.setFormat(f"{status['used_percent']}%")
                pb.setStyleSheet(
                    Styles.PROGRESS_BAR + Styles.get_progress_bar_style(status['used_percent'])
                )
                self.percat_table.setCellWidget(row, 4, pb)
        else:
            self.percat_table.setRowCount(0)

    def _calculate_weekly_spending(self, transactions: List[Transaction], year: Optional[int], month: Optional[int]) -> dict:
        """Calculate current-week spending for a given filtered list."""
        if not transactions:
            return {"spent": 0.0}
        today = datetime.now()
        if year and month:
            today = datetime(year, month, 1)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=7)

        total = 0.0
        for txn in transactions:
            if getattr(txn, "amount", 0) < 0 and getattr(txn, "date", None) and week_start <= txn.date < week_end:
                total += float(abs(txn.amount))
        return {"spent": total}
