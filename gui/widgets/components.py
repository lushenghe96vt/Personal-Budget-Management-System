"""
Reusable UI Components
Personal Budget Management System – Standardized UI Components

Provides reusable, consistent UI components following the design system.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QToolButton, QSizePolicy, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap
from typing import Optional, Union
from gui.app.style import Styles


class MainHeader(QWidget):
    """Common main header with application title."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
    
    def _build_ui(self):
        layout = QHBoxLayout(self)
        # Margins: left, top, right, bottom - more space on sides
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        title = QLabel("Personal Budget Management")
        # Set object name first for specific targeting
        title.setObjectName("MainHeaderTitle")
        
        # Ensure label can expand vertically and horizontally
        title.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        # Use stylesheet for color and font size (32px)
        title.setStyleSheet("""
            QLabel#MainHeaderTitle {
                color: #2c3e50;
                padding: 0px;
                font-size: 32px;
                font-weight: bold;
            }
        """)
        
        # Set font AFTER stylesheet - this ensures font is applied and not overridden
        title_font = QFont()
        title_font.setPointSize(24)  # 32px ≈ 24pt (1pt ≈ 1.33px)
        title_font.setBold(True)
        title.setFont(title_font)
        
        # Force font update
        title.update()
        layout.addWidget(title)
        layout.addStretch()


class PageHeader(QWidget):
    """Standardized page subheader with title and optional back button."""
    
    back_clicked = pyqtSignal()
    
    def __init__(self, title: str, show_back: bool = False, parent=None):
        super().__init__(parent)
        self._build_ui(title, show_back)
    
    def _build_ui(self, title: str, show_back: bool):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        if show_back:
            # Use ← text instead of icon
            back_btn = QPushButton("←")
            back_btn.setToolTip("Go back")
            back_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    color: #2c3e50;
                    font-size: 24px;
                    font-weight: bold;
                    padding: 4px 8px;
                    min-width: 32px;
                    min-height: 32px;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                    border-radius: 4px;
                }
            """)
            back_btn.clicked.connect(self.back_clicked.emit)
            layout.addWidget(back_btn)
        
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(24)  # Consistent with transactions page
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(Styles.LABEL_TITLE_LARGE)
        layout.addWidget(title_label)
        layout.addStretch()


class MetricCard(QWidget):
    """Standardized metric card for displaying KPIs."""
    
    def __init__(self, label: str, value: str, color: str = "#3498db", parent=None):
        super().__init__(parent)
        self._build_ui(label, value, color)
    
    def _build_ui(self, label: str, value: str, color: str):
        self.setStyleSheet(Styles.METRIC_CARD)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        title_label = QLabel(label)
        title_label.setStyleSheet(Styles.METRIC_TITLE)
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 28px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(value_label)
        layout.addStretch()
    
    def update_value(self, value: str):
        """Update the displayed value."""
        value_label = self.findChild(QLabel)
        if value_label and value_label.text() != self.findChild(QLabel, "title"):
            value_label.setText(value)


class SectionCard(QFrame):
    """Standardized section card for grouping related content."""
    
    def __init__(self, title: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(Styles.GROUPBOX)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet(Styles.LABEL_SECTION)
            layout.addWidget(title_label)
        
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(12)
        layout.addLayout(self.content_layout)
    
    def add_widget(self, widget: QWidget):
        """Add a widget to the section."""
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout: Union[QVBoxLayout, QHBoxLayout]):
        """Add a layout to the section."""
        self.content_layout.addLayout(layout)


class StyledButton(QPushButton):
    """Standardized button with consistent styling."""
    
    PRIMARY = "primary"
    SECONDARY = "secondary"
    DANGER = "danger"
    SUCCESS = "success"
    NEUTRAL = "neutral"
    TEXT = "text"
    
    def __init__(self, text: str, style_type: str = PRIMARY, parent=None):
        super().__init__(text, parent)
        self._apply_style(style_type)
    
    def _apply_style(self, style_type: str):
        style_map = {
            self.PRIMARY: Styles.BUTTON_PRIMARY,
            self.SECONDARY: Styles.BUTTON_SECONDARY,
            self.DANGER: Styles.BUTTON_DANGER,
            self.SUCCESS: Styles.BUTTON_SUCCESS,
            self.NEUTRAL: Styles.BUTTON_NEUTRAL,
            self.TEXT: Styles.BUTTON_TEXT,
        }
        self.setStyleSheet(style_map.get(style_type, Styles.BUTTON_PRIMARY))


class IconButton(QToolButton):
    """Icon-only button for actions like edit/delete."""
    
    def __init__(self, icon_name: str, tooltip: str = "", parent=None):
        super().__init__(parent)
        self._build_ui(icon_name, tooltip)
    
    def _build_ui(self, icon_name: str, tooltip: str):
        # Use simple text-based icons for cleaner look
        self.setText(self._get_icon_text(icon_name))
        
        # Set larger, readable font for better visibility
        font = QFont()
        font.setPointSize(16)
        font.setBold(False)
        self.setFont(font)
        
        if tooltip:
            self.setToolTip(tooltip)
        
        # Larger size for better visibility
        self.setMinimumSize(40, 40)
        self.setMaximumSize(48, 48)
        
        self.setAutoRaise(True)  # Cleaner look without border by default
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        
        # Ensure button is visible
        self.setVisible(True)
        self.setEnabled(True)
        
        # Simple, clean styling with larger icons
        self.setStyleSheet("""
            QToolButton {
                padding: 6px 8px;
                border-radius: 4px;
                border: none;
                background-color: transparent;
                color: #555555;
                min-width: 40px;
                min-height: 40px;
                font-size: 16px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
                color: #2c3e50;
            }
            QToolButton:pressed {
                background-color: #e0e0e0;
            }
        """)
    
    def _get_icon_text(self, icon_name: str) -> str:
        """Get simple text symbol for icon."""
        text_map = {
            "edit": "📝",      # Memo emoji for edit
            "delete": "✕",     # Simple X/delete symbol
            "add": "+",
            "refresh": "↻",
        }
        return text_map.get(icon_name.lower(), icon_name)


class StyledComboBox(QWidget):
    """Standardized combobox wrapper."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QComboBox
        self.combo = QComboBox()
        self.combo.setStyleSheet(Styles.COMBOBOX)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.combo)
    
    def addItem(self, text: str):
        """Add item to combobox."""
        self.combo.addItem(text)
    
    def currentText(self) -> str:
        """Get current text."""
        return self.combo.currentText()
    
    def currentTextChanged(self):
        """Get signal for text changes."""
        return self.combo.currentTextChanged
    
    def clear(self):
        """Clear combobox."""
        self.combo.clear()
    
    def setCurrentText(self, text: str):
        """Set current text."""
        self.combo.setCurrentText(text)
    
    def findText(self, text: str) -> int:
        """Find text index."""
        return self.combo.findText(text)
    
    def setCurrentIndex(self, index: int):
        """Set current index."""
        self.combo.setCurrentIndex(index)
    
    def count(self) -> int:
        """Get item count."""
        return self.combo.count()

