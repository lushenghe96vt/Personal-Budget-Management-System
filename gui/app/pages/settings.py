from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QDialog, QTextEdit, QToolButton, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from gui.widgets.components import SectionCard
from gui.app.style import Styles


class BudgetSettingsPage(QWidget):
    """Page to manage spending/savings goals and per-category limits."""

    go_back_to_dashboard = pyqtSignal()
    saved = pyqtSignal()

    def __init__(self, user, user_manager):
        super().__init__()
        self.user = user
        self.user_manager = user_manager
        self._build_ui()
        self._load_from_user()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header with back button and title - use common PageHeader
        from gui.widgets.components import PageHeader
        page_header = PageHeader("Budget Settings", show_back=True)
        page_header.back_clicked.connect(self.go_back_to_dashboard.emit)
        layout.addWidget(page_header)

        # Content layout (two columns - left smaller, right larger)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Overall Monthly Goals (left side - smaller, top-aligned)
        overall_section = SectionCard("Overall Monthly Goals")
        overall_section.setStyleSheet(Styles.GROUPBOX)
        # Ensure content is top-aligned (not vertically centered)
        overall_section.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        form = QFormLayout()
        form.setSpacing(16)
        form.setContentsMargins(0, 0, 0, 0)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)  # Left-align labels
        
        self.spending_limit_input = QLineEdit()
        self.spending_limit_input.setPlaceholderText("e.g., 1500.00")
        self.spending_limit_input.setStyleSheet(Styles.SEARCH_INPUT)
        self.savings_goal_input = QLineEdit()
        self.savings_goal_input.setPlaceholderText("e.g., 500.00")
        self.savings_goal_input.setStyleSheet(Styles.SEARCH_INPUT)
        
        form.addRow("Monthly Spending Limit ($)", self.spending_limit_input)
        form.addRow("Monthly Savings Goal ($)", self.savings_goal_input)
        
        overall_section.content_layout.addLayout(form)
        # Add stretch at bottom to push content to top
        overall_section.content_layout.addStretch()
        # Set smaller stretch factor (1) vs right side (2) = 33% vs 67% split
        content_layout.addWidget(overall_section, 1)  # Smaller width

        # Per-Category Limits (right side - larger)
        per_cat_section = SectionCard("Per-Category Limits")
        per_cat_section.setStyleSheet(Styles.GROUPBOX)
        
        per_cat_layout = QVBoxLayout()
        per_cat_layout.setSpacing(12)
        
        self.per_cat_table = QTableWidget(0, 2)
        self.per_cat_table.setHorizontalHeaderLabels(["Category", "Limit ($)"])
        header = self.per_cat_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.per_cat_table.setStyleSheet(Styles.TABLE)
        per_cat_layout.addWidget(self.per_cat_table)

        row_btns = QHBoxLayout()
        row_btns.setSpacing(8)
        add_row = QPushButton("Add Row")
        add_row.setStyleSheet(Styles.BUTTON_SECONDARY)
        remove_row = QPushButton("Remove Selected")
        remove_row.setStyleSheet(Styles.BUTTON_SECONDARY)
        add_row.clicked.connect(self._add_row)
        remove_row.clicked.connect(self._remove_selected_row)
        row_btns.addWidget(add_row)
        row_btns.addWidget(remove_row)
        row_btns.addStretch()
        per_cat_layout.addLayout(row_btns)
        
        per_cat_section.content_layout.addLayout(per_cat_layout)
        content_layout.addWidget(per_cat_section, 2)  # Larger width (2x stretch)

        layout.addLayout(content_layout)

        # Actions
        actions = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet(Styles.BUTTON_SUCCESS)
        support_btn = QPushButton("Contact Support")
        support_btn.setStyleSheet(Styles.BUTTON_SECONDARY)
        save_btn.clicked.connect(self._save)
        support_btn.clicked.connect(self._open_support_dialog)
        actions.addWidget(save_btn)
        actions.addWidget(support_btn)
        actions.addStretch()
        layout.addLayout(actions)

    def _load_from_user(self):
        if self.user is None:
            return
        self.spending_limit_input.setText("" if self.user.monthly_spending_limit is None else f"{self.user.monthly_spending_limit:.2f}")
        self.savings_goal_input.setText("" if self.user.monthly_savings_goal is None else f"{self.user.monthly_savings_goal:.2f}")

        # load per-category
        limits = self.user.per_category_limits or {}
        self.per_cat_table.setRowCount(0)
        for category, limit in limits.items():
            self._add_row(category, f"{float(limit):.2f}")

    def _add_row(self, category: str = "", limit: str = ""):
        r = self.per_cat_table.rowCount()
        self.per_cat_table.insertRow(r)
        self.per_cat_table.setItem(r, 0, QTableWidgetItem(category))
        self.per_cat_table.setItem(r, 1, QTableWidgetItem(limit))

    def _remove_selected_row(self):
        rows = sorted({i.row() for i in self.per_cat_table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.per_cat_table.removeRow(r)

    def _save(self):
        if self.user is None:
            return
        # parse numbers safely
        def _to_float(txt: str):
            t = (txt or "").strip()
            if not t:
                return None
            try:
                return float(t)
            except ValueError:
                return None

        spending_limit = _to_float(self.spending_limit_input.text())
        savings_goal = _to_float(self.savings_goal_input.text())

        # per-category
        per_cat: dict[str, float] = {}
        for r in range(self.per_cat_table.rowCount()):
            cat_item = self.per_cat_table.item(r, 0)
            lim_item = self.per_cat_table.item(r, 1)
            cat = (cat_item.text() if cat_item else "").strip()
            lim = _to_float(lim_item.text() if lim_item else "")
            if cat and lim is not None:
                per_cat[cat] = lim

        # update user
        self.user.monthly_spending_limit = spending_limit
        self.user.monthly_savings_goal = savings_goal
        self.user.per_category_limits = per_cat

        # Directly persist without revalidating immutable fields
        self.user_manager._users[self.user.username] = self.user
        self.user_manager._save_users()
        QMessageBox.information(self, "Saved", "Budget settings saved successfully.")
        self.saved.emit()

    def _open_support_dialog(self):
        dlg = SupportEmailDialog(self)
        dlg.exec()


class SupportEmailDialog(QDialog):
    """Simple dialog for sending support emails using Jason's supportMail."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Contact Support")
        # Removed fixed width for responsiveness

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Your Email"))
        self.email_input = QLineEdit()
        layout.addWidget(self.email_input)

        layout.addWidget(QLabel("Message"))
        self.msg_input = QTextEdit()
        self.msg_input.setPlaceholderText("Describe your issue or suggestion...")
        layout.addWidget(self.msg_input)

        btns = QHBoxLayout()
        send_btn = QPushButton("Send")
        cancel_btn = QPushButton("Cancel")
        send_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 8px 14px; border: none; border-radius: 6px; font-weight: 600;")
        cancel_btn.setStyleSheet("background-color: #95a5a6; color: white; padding: 8px 14px; border: none; border-radius: 6px; font-weight: 600;")
        send_btn.clicked.connect(self._send)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(send_btn)
        btns.addWidget(cancel_btn)
        btns.addStretch()
        layout.addLayout(btns)

        self.setLayout(layout)

    def _send(self):
        email = (self.email_input.text() or "").strip()
        msg = (self.msg_input.toPlainText() or "").strip()
        if not email or not msg:
            QMessageBox.warning(self, "Missing Info", "Please provide your email and a message.")
            return
        try:
            from core.supportMail import send_sup_msg
            send_sup_msg(email, msg)
            QMessageBox.information(self, "Sent", "Your message has been sent to the developers.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Failed", f"Unable to send email: {e}")


