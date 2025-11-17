"""
Style Module
Personal Budget Management System – Centralized UI Styles

This module contains all QSS (Qt Style Sheets) styles used throughout the application.
All inline styles should be replaced with references to this module for consistency
and easier maintenance.
"""


class Styles:
    """Centralized style definitions for the entire application."""
    
    # ============================================================
    # Colors
    # ============================================================
    COLOR_PRIMARY = "#2c3e50"
    COLOR_SECONDARY = "#7f8c8d"
    COLOR_SUCCESS = "#27ae60"
    COLOR_DANGER = "#e74c3c"
    COLOR_WARNING = "#f39c12"
    COLOR_INFO = "#3498db"
    COLOR_PURPLE = "#9b59b6"
    COLOR_BACKGROUND = "#f5f5f5"
    COLOR_CARD_BG = "#ffffff"
    COLOR_BORDER = "#bdc3c7"
    COLOR_LIGHT_BG = "#f8f9fa"
    COLOR_HOVER = "#e6eaf1"
    
    # ============================================================
    # Main Window
    # ============================================================
    MAIN_WINDOW = """
        QMainWindow {
            background-color: #f5f5f5;
        }
    """
    
    APPLICATION = """
        QApplication { 
            font-family: 'Inter', 'Segoe UI', Arial, sans-serif; 
        }
        QWidget { 
            font-size: 13px; 
        }
        QPushButton { 
            padding: 9px 14px; 
            border-radius: 8px; 
            background: #2f6fed; 
            color: #ffffff; 
            border: none; 
        }
        QPushButton:hover { 
            background: #245add; 
        }
        QPushButton#HeaderBtn { 
            background: #f0f3f8; 
            color: #2c3e50; 
        }
        QPushButton#HeaderBtn:hover { 
            background: #e6eaf1; 
        }
        QPushButton#NavBtn { 
            text-align: left; 
            background: transparent; 
            color: #2c3e50; 
            padding: 10px 12px; 
        }
        QPushButton#NavBtn:hover { 
            background: #f5f7fb; 
        }
        QTableWidget { 
            selection-background-color: #e6efff; 
        }
        QHeaderView::section { 
            background: #f5f7fb; 
            color: #2c3e50; 
            border: none; 
            padding: 10px; 
            font-weight: 600; 
        }
        QScrollArea { 
            background: transparent; 
        }
    """
    
    # ============================================================
    # Header & Navigation
    # ============================================================
    HEADER_BAR = """
        #HeaderBar { 
            background: #ffffff; 
            border: 1px solid #e6e8eb; 
            border-radius: 8px; 
        }
    """
    
    SIDEBAR = """
        #Sidebar { 
            background: #ffffff; 
            border: 1px solid #e6e8eb; 
            border-radius: 8px; 
            min-width: 220px; 
        }
    """
    
    FOOTER = """
        #Footer { 
            background: #ffffff; 
            border: 1px solid #e6e8eb; 
            border-radius: 8px; 
        }
    """
    
    # ============================================================
    # Labels
    # ============================================================
    LABEL_TITLE = "color: #2c3e50; margin-bottom: 10px;"
    LABEL_TITLE_LARGE = "color: #2c3e50; margin-bottom: 4px; font-size: 26px;"
    LABEL_SUBTITLE = "color: #7f8c8d; margin-bottom: 24px;"
    LABEL_SECTION = "font-size: 18px; font-weight: bold; color: #2c3e50;"
    LABEL_BODY = "font-weight: 600; font-size: 14px; color: #2c3e50;"
    LABEL_SECONDARY = "color: #7f8c8d; font-size: 14px;"
    LABEL_INFO = "color: #7f8c8d; font-size: 12px; font-style: italic;"
    
    # ============================================================
    # Buttons
    # ============================================================
    BUTTON_PRIMARY = """
        QPushButton {
            background-color: #2f6fed;
            color: white;
            padding: 9px 14px;
            border-radius: 8px;
            border: none;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #245add;
        }
    """
    
    BUTTON_SUCCESS = """
        QPushButton {
            background-color: #27ae60;
            color: white;
            padding: 10px 16px;
            border: none;
            border-radius: 6px;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #229954;
        }
    """
    
    BUTTON_DANGER = """
        QPushButton {
            background-color: #e74c3c;
            color: white;
            padding: 10px 16px;
            border: none;
            border-radius: 6px;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #c0392b;
        }
    """
    
    BUTTON_NEUTRAL = """
        QPushButton {
            background-color: #95a5a6;
            color: white;
            padding: 10px 16px;
            border: none;
            border-radius: 6px;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #7f8c8d;
        }
    """
    
    BUTTON_SECONDARY = """
        QPushButton {
            background-color: #34495e;
            color: white;
            padding: 8px 14px;
            border: none;
            border-radius: 6px;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #2c3e50;
        }
    """
    
    BUTTON_TEXT = """
        QPushButton {
            background: transparent;
            color: #2f6fed;
            border: none;
            padding: 4px 8px;
            text-align: left;
        }
        QPushButton:hover {
            color: #245add;
            text-decoration: underline;
        }
    """
    
    BUTTON_BACK = """
        QToolButton { 
            padding-right: 8px; 
        }
        QToolButton:hover { 
            color: #245add; 
        }
    """
    
    # ============================================================
    # Input Fields
    # ============================================================
    LINE_EDIT = """
        QLineEdit {
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        QLineEdit:focus {
            border-color: #3498db;
        }
    """
    
    LINE_EDIT_READONLY = """
        QLineEdit {
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            background-color: #ecf0f1;
            color: #7f8c8d;
        }
    """
    
    COMBOBOX = """
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
    """
    
    TEXT_EDIT = """
        QTextEdit {
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        QTextEdit:focus {
            border-color: #3498db;
        }
    """
    
    CHECKBOX = "color: #2c3e50;"
    
    # ============================================================
    # Tables
    # ============================================================
    TABLE = """
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
        QTableWidget::item {
            padding: 10px;
        }
    """
    
    # ============================================================
    # Group Boxes
    # ============================================================
    GROUPBOX = """
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
    """
    
    GROUPBOX_FORM = """
        QGroupBox {
            border: 2px solid #bdc3c7;
            border-radius: 10px;
            padding: 20px;
            background-color: #f8f9fa;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
    """
    
    # ============================================================
    # Tab Widget
    # ============================================================
    TAB_WIDGET = """
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
    """
    
    # ============================================================
    # Metric Cards
    # ============================================================
    METRIC_CARD = """
        QWidget {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 10px;
            margin: 5px;
        }
    """
    
    METRIC_TITLE = """
        QLabel {
            color: #7f8c8d;
            font-size: 14px;
            font-weight: bold;
        }
    """
    
    @staticmethod
    def get_metric_value_style(variant: str) -> str:
        """Get metric value label style based on variant."""
        colors = {
            "danger": "#e74c3c",
            "success": "#27ae60",
            "info": "#3498db",
            "purple": "#9b59b6",
            "warning": "#f39c12"
        }
        color = colors.get(variant, "#2c3e50")
        return f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 20px;
                border-radius: 10px;
                font-size: 24px;
                font-weight: bold;
            }}
        """
    
    # ============================================================
    # Progress Bars
    # ============================================================
    PROGRESS_BAR = """
        QProgressBar {
            border: 1px solid #ddd;
            border-radius: 4px;
            text-align: center;
            background-color: #f0f0f0;
            min-height: 24px;
            max-height: 24px;
        }
        QProgressBar::chunk {
            border-radius: 3px;
        }
    """
    
    @staticmethod
    def get_progress_bar_style(percent: int) -> str:
        """Get progress bar chunk style based on percentage."""
        if percent >= 100:
            return "QProgressBar::chunk { background-color: #e74c3c; }"
        elif percent >= 75:
            return "QProgressBar::chunk { background-color: #f39c12; }"
        else:
            return "QProgressBar::chunk { background-color: #27ae60; }"
    
    @staticmethod
    def get_savings_progress_style(percent: int) -> str:
        """Get savings progress bar chunk style based on percentage."""
        if percent >= 100:
            return "QProgressBar::chunk { background-color: #27ae60; }"
        elif percent >= 50:
            return "QProgressBar::chunk { background-color: #3498db; }"
        else:
            return "QProgressBar::chunk { background-color: #e67e22; }"
    
    # ============================================================
    # Activity Frame
    # ============================================================
    ACTIVITY_FRAME = """
        QFrame {
            background-color: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
        }
    """
    
    # ============================================================
    # Stat Labels
    # ============================================================
    STAT_LABEL_BLUE = """
        QLabel {
            background: #3498db;
            color: white;
            padding: 8px 14px;
            border-radius: 6px;
            font-weight: bold;
        }
    """
    
    STAT_LABEL_RED = """
        QLabel {
            background: #e74c3c;
            color: white;
            padding: 8px 14px;
            border-radius: 6px;
            font-weight: bold;
        }
    """
    
    STAT_LABEL_GREEN = """
        QLabel {
            background: #27ae60;
            color: white;
            padding: 8px 14px;
            border-radius: 6px;
            font-weight: bold;
        }
    """
    
    # ============================================================
    # Welcome & Streak Labels
    # ============================================================
    WELCOME_LABEL = "color: #2c3e50; margin-bottom: 10px; font-size: 26px;"
    STREAK_LABEL = "color: #2c3e50; font-size: 13px; margin-top: -10px;"
    
    # ============================================================
    # Search Input
    # ============================================================
    SEARCH_INPUT = """
        QLineEdit {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
        }
        QLineEdit:focus {
            border-color: #3498db;
        }
    """
    
    # ============================================================
    # Dropdown (ComboBox variant)
    # ============================================================
    DROPDOWN = """
        QComboBox {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            min-width: 150px;
        }
        QComboBox:focus {
            border-color: #3498db;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QComboBox QAbstractItemView {
            border: 1px solid #ddd;
            border-radius: 4px;
            selection-background-color: #3498db;
            selection-color: white;
        }
    """
    
    # ============================================================
    # Menu
    # ============================================================
    MENU = """
        QMenu {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 5px;
        }
        QMenu::item {
            padding: 8px 20px;
            border-radius: 4px;
        }
        QMenu::item:selected {
            background-color: #3498db;
            color: white;
        }
    """


# Convenience function to get combined styles
def combine_styles(*styles: str) -> str:
    """Combine multiple style strings into one."""
    return "\n".join(styles)

