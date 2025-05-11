from PyQt6.QtWidgets import QDialog, QFormLayout, QHBoxLayout, QLabel, QVBoxLayout

from src.gui.components.styled_button import StyledButton
from src.utils.logging import get_logger

logger = get_logger(__name__)


class BaseFormDialog(QDialog):
    """Base class for all form dialogs to ensure consistency."""

    def __init__(self, parent=None, entity_id=None, readonly=False):
        super().__init__(parent)
        self.main_window = parent.main_window if parent else None
        self.entity_id = entity_id
        self.readonly = readonly
        self.data = {}

        mode = "View" if readonly else "Edit" if entity_id else "New"
        self.entity_type = "Item"  # Override in subclass
        self.setWindowTitle(f"{mode} {self.entity_type}")

        self._init_ui()

        if self.entity_id:
            self.load_data()

    def _init_ui(self):
        """Initialize the form UI with consistent layout."""
        self.layout = QVBoxLayout(self)

        # Form layout for fields
        self.form_layout = QFormLayout()
        self.layout.addLayout(self.form_layout)

        # Required fields note if not readonly
        if not self.readonly:
            self.layout.addWidget(QLabel("* Required fields"))

        # Consistent button layout
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        if not self.readonly:
            self.save_btn = StyledButton("Save", "primary")
            self.save_btn.clicked.connect(self.save_data)
            btn_layout.addWidget(self.save_btn)

        self.close_btn = StyledButton("Close", "secondary")
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.close_btn)

        self.layout.addLayout(btn_layout)

    def add_form_field(self, label, widget, required=False):
        """Add a field to the form with consistent styling."""
        if required and not self.readonly:
            label = f"{label}*"
        self.form_layout.addRow(label, widget)

    def load_data(self):
        """Load entity data - override in subclass."""
        pass

    def save_data(self):
        """Save entity data - override in subclass."""
        pass
