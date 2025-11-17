"""
Pie Chart Widget
Personal Budget Management System – Simple Pie Chart Component

A lightweight pie chart widget that maintains perfect circular aspect ratio.
"""

from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QPainter, QColor
from typing import Dict
from decimal import Decimal


class SimplePieChart(QWidget):
    """Simple pie chart widget for category breakdown with perfect circular rendering."""
    
    # Color palette for pie chart segments
    COLORS = [
        QColor("#e74c3c"), QColor("#3498db"), QColor("#2ecc71"), QColor("#f39c12"),
        QColor("#9b59b6"), QColor("#1abc9c"), QColor("#e67e22"), QColor("#34495e"),
        QColor("#f1c40f"), QColor("#e91e63"), QColor("#00bcd4"), QColor("#4caf50")
    ]
    
    def __init__(self, data: Dict[str, Decimal] = None, parent=None):
        super().__init__(parent)
        self.data = data or {}
        self.setMinimumSize(300, 300)
        self.setMaximumSize(500, 500)
        
        # Set size policy to maintain aspect ratio
        size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        size_policy.setHeightForWidth(True)
        self.setSizePolicy(size_policy)
    
    def sizeHint(self) -> QSize:
        """Return preferred size (square)."""
        return QSize(400, 400)
    
    def heightForWidth(self, width: int) -> int:
        """Maintain square aspect ratio."""
        return width
    
    def set_data(self, data: Dict[str, Decimal]):
        """Update the chart data and trigger repaint."""
        self.data = data
        self.update()
    
    def paintEvent(self, event):
        """Draw the pie chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
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
                color = self.COLORS[i % len(self.COLORS)]
                
                painter.setBrush(color)
                painter.setPen(QColor("#2c3e50"))
                painter.drawPie(rect, start_angle, angle)
                
                start_angle += angle
