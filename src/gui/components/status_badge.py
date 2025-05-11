from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel

from src.config import STATUS_COLORS


class StatusBadge(QLabel):
    """A badge to display application status with consistent styling."""

    def __init__(self, status, parent=None):
        """Initialize status badge.

        Args:
            status: Status text to display
            parent: Parent widget
        """
        super().__init__(status, parent)
        self.status = status
        self._apply_style()

    def _apply_style(self):
        """Apply styling based on status."""
        color = STATUS_COLORS.get(self.status, STATUS_COLORS["SAVED"])

        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color}30;
                color: {color};
                border: 1px solid {color}50;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
            }}
        """)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(100)
