"""
Month Filter Widget
Personal Budget Management System – Reusable Month Filter Component

A reusable month filter dropdown that works with the analytics.months module.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import pyqtSignal
from typing import List, Dict, Tuple, Optional
from core.models import Transaction
from core.analytics.months import get_available_months
from gui.app.style import Styles


class MonthFilter(QWidget):
    """Reusable month filter widget."""
    
    filter_changed = pyqtSignal(str)  # Emits the selected filter text
    
    def __init__(self, label: str = "Filter by Period:", parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        filter_label = QLabel(label)
        layout.addWidget(filter_label)
        
        # ComboBox
        self.combo = QComboBox()
        self.combo.setStyleSheet(Styles.COMBOBOX)
        self.combo.currentTextChanged.connect(self.filter_changed.emit)
        layout.addWidget(self.combo)
        
        layout.addStretch()
        
        self._month_options: Dict[str, Tuple[Optional[str], Optional[str]]] = {}
    
    def populate_from_transactions(self, transactions: List[Transaction]):
        """Populate filter options from transactions."""
        self._month_options = get_available_months(transactions)
        self.combo.clear()
        self.combo.addItem("All Time")
        
        # Add date-based months
        date_months = [(k, v) for k, v in self._month_options.items() 
                      if v[0] == "date"]
        date_months.sort(key=lambda x: x[1][1] if x[1][1] else "", reverse=True)
        for month_name, _ in date_months:
            self.combo.addItem(month_name)
        
        # Add statement-based months
        stmt_months = [(k, v) for k, v in self._month_options.items() 
                      if v[0] == "statement"]
        stmt_months.sort(key=lambda x: x[1][1] if x[1][1] else "", reverse=True)
        for stmt_name, _ in stmt_months:
            self.combo.addItem(stmt_name)
    
    def get_filter_info(self) -> Optional[Tuple[str, str]]:
        """Get filter type and value for current selection."""
        selected = self.combo.currentText()
        if selected == "All Time":
            return None
        return self._month_options.get(selected)
    
    def set_current_filter(self, filter_text: str):
        """Set the current filter selection."""
        index = self.combo.findText(filter_text)
        if index >= 0:
            self.combo.setCurrentIndex(index)

