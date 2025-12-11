from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QLineEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt

from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal

from core.models import Transaction
from gui.app.style import Styles
from core.analytics.loan import calculate_loan

class LoanTab(QWidget):
    """Loan accessibility calculator tab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.user = None
        self.transactions: List[Transaction] = []
        self._build_ui()

    def set_user(self, user):
        self.user = user

    def _build_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none;")
        outer_layout.addWidget(self.scroll)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(24, 24, 24, 24)
        container_layout.setSpacing(24)

        title = QLabel("Loan Eligibility & Payment Calculator")
        title.setStyleSheet(Styles.LABEL_SECTION)
        container_layout.addWidget(title)

        columns = QGridLayout()
        columns.setHorizontalSpacing(24)
        columns.setVerticalSpacing(24)
        columns.setColumnStretch(0, 1)
        columns.setColumnStretch(1, 1)
        container_layout.addLayout(columns)

        # ---------------------------
        # INPUT FORM
        # ---------------------------
        form_group = QGroupBox("Loan Application")
        form_group.setStyleSheet(Styles.GROUPBOX)
        form_layout = QVBoxLayout()

        # Income
        self.income_input = QLineEdit()
        self.income_input.setPlaceholderText("Monthly Income ($)")
        self.income_input.setStyleSheet(Styles.LINE_EDIT)

        # Credit Score
        self.credit_input = QLineEdit()
        self.credit_input.setPlaceholderText("Credit Score (300–850)")
        self.credit_input.setStyleSheet(Styles.LINE_EDIT)

        # Duration
        self.duration_input = QLineEdit()
        self.duration_input.setPlaceholderText("Loan Duration (Months)")
        self.duration_input.setStyleSheet(Styles.LINE_EDIT)

        # Amount
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Amount Requested ($)")
        self.amount_input.setStyleSheet(Styles.LINE_EDIT)

        # Purpose
        self.purpose_dropdown = QComboBox()
        self.purpose_dropdown.addItems([
            "Auto", "Home", "Education", "Medical",
            "Business", "Debt Consolidation", "Personal"
        ])
        self.purpose_dropdown.setStyleSheet(Styles.COMBOBOX)

        # Submit button
        submit_btn = QPushButton("Calculate Loan")
        submit_btn.setStyleSheet(Styles.BUTTON_PRIMARY)
        submit_btn.clicked.connect(self._on_calculate)

        # Add inputs to layout
        for label, widget in [
            ("Monthly Income ($):", self.income_input),
            ("Credit Score:", self.credit_input),
            ("Loan Duration (Months):", self.duration_input),
            ("Amount Requested ($):", self.amount_input),
            ("Loan Purpose:", self.purpose_dropdown),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label)
            row.addWidget(lbl)
            row.addWidget(widget)
            form_layout.addLayout(row)

        form_layout.addWidget(submit_btn)
        form_group.setLayout(form_layout)
        columns.addWidget(form_group, 0, 0)

        # ---------------------------
        # OUTPUT SECTION (clean card)
        # ---------------------------
        self.result_group = QGroupBox("Loan Results")
        self.result_group.setStyleSheet(Styles.GROUPBOX)
        self.result_group.setMinimumHeight(150)

        self.result_layout = QVBoxLayout()
        self.result_layout.setContentsMargins(24, 24, 24, 24)
        self.result_layout.setSpacing(18)
        self.result_group.setLayout(self.result_layout)

        columns.addWidget(self.result_group, 0, 1)

        container_layout.addStretch()
        self.scroll.setWidget(container)

    # -----------------------------------------
    # LOGIC → Run loan calculation
    # -----------------------------------------
    def _on_calculate(self):

        if self.user is None:
            try:
                from gui.app.main import AppWindow
                self.user = AppWindow.instance.user
            except Exception:
                pass

        if self.user is None:
            QMessageBox.warning(self, "Error", "User data is not available.")
            return

        try:
            income = float(self.income_input.text())
            credit = int(self.credit_input.text())
            duration = int(self.duration_input.text())
            amount = float(self.amount_input.text())
            purpose = self.purpose_dropdown.currentText()

            # Internal behavioral data from user dashboard
            avg_balance = self.user.average_balance_last_3_months()
            monthly_goal_tracker = self.user.monthly_goal_tracker()

            result = calculate_loan(
                income=income,
                credit_score=credit,
                duration_months=duration,
                amount_requested=amount,
                loan_purpose=purpose,
                avg_balance=avg_balance,
                monthly_goal_tracker=monthly_goal_tracker
            )

            self._populate_results(result)

        except Exception as e:
            QMessageBox.critical(self, "Calculation Error", str(e))

    def _populate_results(self, result: dict):
        """Display loan results in a clean card format."""

        # remove old widgets
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)

            if item.widget():
                item.widget().deleteLater()

            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                    elif child.layout():
                        self._delete_layout(child.layout())
                item.layout().deleteLater()

        # Status banner
        approved = result.get("approved", False)
        status_color = "#27ae60" if approved else "#e74c3c"
        status_text = "APPROVED" if approved else "DENIED"

        status_label = QLabel(f"<h2 style='color:{status_color};'>{status_text}</h2>")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_layout.addWidget(status_label)

        # Reason
        reason = result.get("reason", "")
        reason_label = QLabel(f"<i>{reason}</i>")
        reason_label.setWordWrap(True)
        reason_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_layout.addWidget(reason_label)

        # Divider
        divider = QLabel("<hr>")
        self.result_layout.addWidget(divider)

        # Two-column compact results
        grid = QGridLayout()
        row = 0

        for key, value in result.items():
            if key in ("approved", "reason"):
                continue

            label = QLabel(f"<b>{key.replace('_', ' ').title()}</b>")
            label.setStyleSheet("font-size: 13px; margin-bottom: 4px;")

            value_label = QLabel(str(value))
            value_label.setStyleSheet("font-size: 13px; margin-bottom: 4px;")

            grid.addWidget(label, row, 0)
            grid.addWidget(value_label, row, 1)

            row += 1

        self.result_layout.addLayout(grid)
        self.result_layout.addStretch()