"""
Styled Table Component
Personal Budget Management System – Standardized Table Widget
"""

from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from gui.app.style import Styles


class StyledTable(QTableWidget):
    """Standardized table with consistent styling and behavior."""
    
    def __init__(self, columns: list[str], parent=None):
        super().__init__(parent)
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        self._apply_styling()
        self._configure_behavior()
    
    def _apply_styling(self):
        """Apply standard table styling."""
        self.setStyleSheet(Styles.TABLE)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    
    def _configure_behavior(self):
        """Configure table behavior."""
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setDefaultSectionSize(100)
        
        # Set minimum row height
        self.verticalHeader().setMinimumSectionSize(40)
        self.verticalHeader().setDefaultSectionSize(40)
    
    def add_row(self, items: list, editable: bool = False):
        """Add a row with items."""
        row = self.rowCount()
        self.insertRow(row)
        
        for col, item_text in enumerate(items):
            item = QTableWidgetItem(str(item_text))
            if not editable:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(row, col, item)
    
    def set_column_resize_mode(self, column: int, mode: QHeaderView.ResizeMode):
        """Set resize mode for a specific column."""
        self.horizontalHeader().setSectionResizeMode(column, mode)

