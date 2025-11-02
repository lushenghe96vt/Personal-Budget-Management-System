from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal


class NotificationBanner(QWidget):
    """A dismissible, app-wide notification banner (info/success/warning/error)."""

    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self.hide)

        self._message_label = QLabel("")
        self._message_label.setWordWrap(True)
        self._message_label.setStyleSheet("font-size: 14px; font-weight: 600;")

        self._close_button = QPushButton("✖")
        self._close_button.setFixedWidth(32)
        self._close_button.clicked.connect(self._handle_close)

        layout = QHBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)
        layout.addWidget(self._message_label, 1)
        layout.addWidget(self._close_button, 0, Qt.AlignmentFlag.AlignRight)
        self.setLayout(layout)
        self.setMinimumHeight(52)

        self.hide()  # hidden by default

    def _handle_close(self):
        self.hide()
        self.closed.emit()

    def show_message(self, text: str, level: str = "info", auto_hide_ms: int = 7000):
        """Display a message with a style level: info, success, warning, error."""
        palette = {
            "info":    ("#e8f4fd", "#0b6fa4"),
            "success": ("#e8f8f1", "#1e7e34"),
            "warning": ("#fff8e6", "#ad7b00"),
            "error":   ("#fdecea", "#a12622"),
        }
        bg, fg = palette.get(level, palette["info"])
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg};
                border: 1px solid rgba(0,0,0,0.12);
                border-radius: 8px;
            }}
            QLabel {{ color: {fg}; font-weight: 600; }}
            QPushButton {{
                background: transparent; border: none; color: {fg};
                font-weight: bold; padding: 4px 8px;
            }}
            QPushButton:hover {{ background: rgba(0,0,0,0.05); border-radius: 4px; }}
        """)
        self._message_label.setText(text)
        self.show()

        self._auto_hide_timer.stop()
        if auto_hide_ms > 0:
            self._auto_hide_timer.start(auto_hide_ms)


