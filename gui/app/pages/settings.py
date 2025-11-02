from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QTextEdit, QToolButton, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


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
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header row with back icon and title
        header = QHBoxLayout()
        back_btn_top = QToolButton()
        back_btn_top.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack))
        back_btn_top.setAutoRaise(True)
        back_btn_top.setStyleSheet("QToolButton { padding-right: 8px; }")
        back_btn_top.clicked.connect(self.go_back_to_dashboard.emit)
        header.addWidget(back_btn_top)
        title = QLabel("Budget Settings")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        f = QFont()
        f.setPointSize(26)
        f.setBold(True)
        title.setFont(f)
        title.setStyleSheet("color: #2c3e50;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Overall goals
        overall_group = QGroupBox("Overall Monthly Goals")
        form = QFormLayout()
        self.spending_limit_input = QLineEdit()
        self.spending_limit_input.setPlaceholderText("e.g., 1500.00")
        self.savings_goal_input = QLineEdit()
        self.savings_goal_input.setPlaceholderText("e.g., 500.00")
        form.addRow("Monthly Spending Limit ($)", self.spending_limit_input)
        form.addRow("Monthly Savings Goal ($)", self.savings_goal_input)
        overall_group.setLayout(form)
        layout.addWidget(overall_group)

        # Per-category limits table
        per_cat_group = QGroupBox("Per-Category Limits (optional)")
        self.per_cat_table = QTableWidget(0, 2)
        self.per_cat_table.setHorizontalHeaderLabels(["Category", "Limit ($)"])
        header = self.per_cat_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        per_cat_layout = QVBoxLayout()
        per_cat_layout.addWidget(self.per_cat_table)

        row_btns = QHBoxLayout()
        add_row = QPushButton("Add Row")
        remove_row = QPushButton("Remove Selected")
        add_row.clicked.connect(self._add_row)
        remove_row.clicked.connect(self._remove_selected_row)
        row_btns.addWidget(add_row)
        row_btns.addWidget(remove_row)
        row_btns.addStretch()
        per_cat_layout.addLayout(row_btns)
        per_cat_group.setLayout(per_cat_layout)
        layout.addWidget(per_cat_group)

        # Actions
        actions = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 10px 16px; border: none; border-radius: 6px; font-weight: 600;")
        support_btn = QPushButton("📧 Contact Support")
        support_btn.setStyleSheet("background-color: #3498db; color: white; padding: 10px 16px; border: none; border-radius: 6px; font-weight: 600;")
        save_btn.clicked.connect(self._save)
        support_btn.clicked.connect(self._open_support_dialog)
        actions.addWidget(save_btn)
        actions.addWidget(support_btn)
        actions.addStretch()
        layout.addLayout(actions)

        self.setLayout(layout)

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
        self.setMinimumWidth(420)

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


