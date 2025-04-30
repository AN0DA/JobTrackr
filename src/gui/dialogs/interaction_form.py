from datetime import datetime, timedelta

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from src.config import InteractionType
from src.services.interaction_service import InteractionService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class InteractionForm(QDialog):
    """Dialog for creating or editing an interaction."""

    def __init__(self, parent=None, interaction_id=None, application_id=None) -> None:
        super().__init__(parent)
        self.main_window = parent.main_window if parent else None
        self.interaction_id = interaction_id
        self.application_id = application_id

        title = "Edit Interaction" if interaction_id else "New Interaction"
        self.setWindowTitle(title)
        self.resize(500, 400)

        self._init_ui()

        # Load data if editing
        if self.interaction_id:
            self.load_interaction()

    def _init_ui(self) -> None:
        """Initialize the form UI."""
        layout = QVBoxLayout(self)

        # Form layout for interaction fields
        form_layout = QFormLayout()

        # Interaction type
        self.type_select = QComboBox()
        for itype in InteractionType:
            self.type_select.addItem(itype.value)
        form_layout.addRow("Interaction Type:", self.type_select)

        # Date field
        self.date_input = QLineEdit()
        self.date_input.setText(datetime.now().strftime("%Y-%m-%d"))
        form_layout.addRow("Date:", self.date_input)

        # Quick date buttons
        quick_date_layout = QHBoxLayout()
        self.today_btn = QPushButton("Today")
        self.yesterday_btn = QPushButton("Yesterday")
        self.two_days_ago_btn = QPushButton("-2 Days")
        self.week_ago_btn = QPushButton("-1 Week")

        self.today_btn.clicked.connect(lambda: self.set_quick_date(0))
        self.yesterday_btn.clicked.connect(lambda: self.set_quick_date(1))
        self.two_days_ago_btn.clicked.connect(lambda: self.set_quick_date(2))
        self.week_ago_btn.clicked.connect(lambda: self.set_quick_date(7))

        quick_date_layout.addWidget(self.today_btn)
        quick_date_layout.addWidget(self.yesterday_btn)
        quick_date_layout.addWidget(self.two_days_ago_btn)
        quick_date_layout.addWidget(self.week_ago_btn)

        form_layout.addRow("Quick Date:", quick_date_layout)

        # Notes field
        form_layout.addRow("Notes:", QLabel())
        self.notes_input = QTextEdit()
        form_layout.addWidget(self.notes_input)

        layout.addLayout(form_layout)

        # Button row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_interaction)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_interaction(self) -> None:
        """Load interaction data if editing."""
        try:
            service = InteractionService()
            interaction = service.get(self.interaction_id)

            if not interaction:
                if self.main_window:
                    self.main_window.show_status_message(f"Interaction {self.interaction_id} not found")
                return

            # Set interaction type
            index = self.type_select.findText(interaction["type"])
            if index >= 0:
                self.type_select.setCurrentIndex(index)

            # Format the date
            date = datetime.fromisoformat(interaction["date"]).strftime("%Y-%m-%d")
            self.date_input.setText(date)

            # Set notes
            if interaction.get("notes"):
                self.notes_input.setPlainText(interaction["notes"])

            # Store the application ID if it exists
            self.application_id = interaction.get("application_id")

        except Exception as e:
            logger.error(f"Error loading interaction: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading interaction: {str(e)}")

    def set_quick_date(self, days_ago) -> None:
        """Set date to a quick option."""
        date = datetime.now() - timedelta(days=days_ago)
        self.date_input.setText(date.strftime("%Y-%m-%d"))

    @pyqtSlot()
    def save_interaction(self) -> None:
        """Save the interaction data."""
        try:
            # Get form values
            interaction_type = self.type_select.currentText()
            date = self.date_input.text().strip()
            notes = self.notes_input.toPlainText().strip()

            # Validate required fields
            if not interaction_type:
                QMessageBox.warning(self, "Validation Error", "Interaction type is required")
                self.type_select.setFocus()
                return

            if not date:
                QMessageBox.warning(self, "Validation Error", "Date is required")
                self.date_input.setFocus()
                return

            if not self.application_id:
                QMessageBox.warning(self, "Validation Error", "Application ID is required")
                return

            # Prepare data
            interaction_data = {
                "type": interaction_type,
                "date": date,
                "notes": notes or None,
                "application_id": self.application_id,
            }

            # Save interaction
            service = InteractionService()

            if self.interaction_id:
                service.update(self.interaction_id, interaction_data)
                message = "Interaction updated successfully"
            else:
                service.create(interaction_data)
                message = "Interaction created successfully"

            if self.main_window:
                self.main_window.show_status_message(message)

            self.accept()

        except Exception as e:
            logger.error(f"Error saving interaction: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error saving interaction: {str(e)}")
