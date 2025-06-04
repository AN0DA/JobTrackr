from PyQt6.QtWidgets import QPushButton

from src.config import UI_COLORS


class StyledButton(QPushButton):
    """
    Custom styled button with consistent appearance.

    Supports multiple button types (primary, secondary, danger, success, text)
    with configurable colors and styles from the UI_COLORS configuration.
    """

    TYPES = {
        "primary": {
            "background": UI_COLORS["primary"],
            "text": "#FFFFFF",
            "border": UI_COLORS["primary"],
            "hover_bg": "#1A56DB",
        },
        "secondary": {
            "background": "#FFFFFF",
            "text": UI_COLORS["dark"],
            "border": UI_COLORS["secondary"],
            "hover_bg": UI_COLORS["light"],
        },
        "danger": {
            "background": UI_COLORS["danger"],
            "text": "#FFFFFF",
            "border": UI_COLORS["danger"],
            "hover_bg": "#BE123C",
        },
        "success": {
            "background": UI_COLORS["success"],
            "text": "#FFFFFF",
            "border": UI_COLORS["success"],
            "hover_bg": "#059669",
        },
        "text": {
            "background": "transparent",
            "text": UI_COLORS["primary"],
            "border": "transparent",
            "hover_bg": UI_COLORS["light"],
        },
    }

    def __init__(self, text="", button_type="primary", icon=None, parent=None):
        """
        Initialize styled button.

        Args:
            text (str): Button text.
            button_type (str): Type of button (primary, secondary, danger, success, text).
            icon: Optional icon to display.
            parent: Parent widget.
        """
        super().__init__(text, parent)
        self.button_type = button_type

        if icon:
            self.setIcon(icon)

        self._apply_style()

    def _apply_style(self):
        """
        Apply the style to the button based on its type.
        """
        style = self.TYPES.get(self.button_type, self.TYPES["primary"])

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {style["background"]};
                color: {style["text"]};
                border: 1px solid {style["border"]};
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }}

            QPushButton:hover {{
                background-color: {style["hover_bg"]};
            }}

            QPushButton:disabled {{
                background-color: #E5E7EB;
                color: #9CA3AF;
                border-color: #E5E7EB;
            }}
        """)
