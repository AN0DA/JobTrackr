from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.config import FONT_SIZES, UI_COLORS


class DialogHeader(QWidget):
    """
    Standardized header for dialogs.

    Displays a title and optional subtitle with consistent styling and layout.
    """

    def __init__(self, title, subtitle=None, parent=None):
        """
        Initialize the dialog header widget.

        Args:
            title (str): The main title text.
            subtitle (str, optional): Optional subtitle text.
            parent: Parent widget.
        """
        super().__init__(parent)

        self.setStyleSheet(f"""
            DialogHeader {{
                background-color: {UI_COLORS["card"]};
                border-bottom: 1px solid #E5E7EB;
                padding-bottom: 8px;
                margin-bottom: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title
        self.title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(FONT_SIZES["2xl"])
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label)

        # Subtitle if provided
        if subtitle:
            self.subtitle_label = QLabel(subtitle)
            subtitle_font = QFont()
            subtitle_font.setPointSize(FONT_SIZES["md"])
            self.subtitle_label.setFont(subtitle_font)
            self.subtitle_label.setStyleSheet(f"color: {UI_COLORS['secondary']};")
            layout.addWidget(self.subtitle_label)
