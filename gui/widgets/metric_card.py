"""
Metric Card Widget
Personal Budget Management System – Reusable Metric Display Card

A reusable card component for displaying metrics with title and value.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from gui.app.style import Styles


class MetricCard(QWidget):
    """Reusable metric card widget with title and value."""
    
    def __init__(self, title: str, value: str = "", variant: str = "info", parent=None, small_font: bool = False):
        super().__init__(parent)
        self.small_font = small_font
        # Enhanced card styling - bigger white card
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 1px solid #e6e8eb;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title label - same size for all cards
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(Styles.METRIC_TITLE)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Value label
        self.value_label = QLabel(value)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_variant(variant)
        layout.addWidget(self.value_label)
    
    def set_variant(self, variant: str):
        """Set the color variant for the value label."""
        # Map variant to color
        color_map = {
            "danger": "#e74c3c",
            "success": "#27ae60",
            "info": "#3498db",
            "warning": "#f39c12",
            "neutral": "#7f8c8d",
        }
        color = color_map.get(variant, "#2c3e50")
        # Use smaller font if specified
        font_size = "20px" if self.small_font else "28px"
        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: {font_size};
                font-weight: bold;
            }}
        """)
    
    def set_value(self, value: str):
        """Update the value displayed."""
        self.value_label.setText(value)

