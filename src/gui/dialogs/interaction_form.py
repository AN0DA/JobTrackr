from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
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

from src.gui.dialogs.application_selector import ApplicationSelectorDialog
from src.gui.dialogs.contact_selector import ContactSelectorDialog
from src.services.application_service import ApplicationService
from src.services.contact_service import ContactService
from src.services.interaction_service import InteractionService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class InteractionForm(QDialog):
    """Form for adding and editing interactions with contacts."""

    INTERACTION_TYPES = [
        "PHONE_CALL",
        "EMAIL",
        "MEETING",
        "INTERVIEW",
        "LINKEDIN_MESSAGE",
        "COFFEE_CHAT",
        "NETWORKING_EVENT",
        "OTHER",
    ]

    def __init__(self, parent=None, contact_id=None, application_id=None, interaction_id=None):
        """
        Initialize the interaction form.

        Args:
            parent: Parent widget
            contact_id: ID of the contact associated with this interaction (optional)
            application_id: ID of the application associated with this interaction (optional)
            interaction_id: ID of the interaction to edit (if editing an existing interaction)
        """
        super().__init__(parent)
        self.main_window = parent.main_window if parent else None
        self.contact_id = contact_id
        self.application_id = application_id
        self.interaction_id = interaction_id
        self.interaction_data = None

        self.setWindowTitle("Interaction Form")
        self.resize(500, 400)

        self._init_ui()

        # Load data if editing
        if self.interaction_id:
            self.load_interaction_data()
        else:
            # Set defaults for new interaction
            self.datetime_input.setDateTime(datetime.now())

            # Pre-select contact and application if provided
            self._update_contact_display()
            self._update_application_display()

    def _init_ui(self):
        """Initialize the form UI."""
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        # Interaction type dropdown
        self.type_combo = QComboBox()
        self.type_combo.addItems(self.INTERACTION_TYPES)
        form_layout.addRow("Type:", self.type_combo)

        # Date and time picker
        self.datetime_input = QDateTimeEdit()
        self.datetime_input.setCalendarPopup(True)
        self.datetime_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        form_layout.addRow("Date & Time:", self.datetime_input)

        # Subject field
        self.subject_input = QLineEdit()
        form_layout.addRow("Subject:", self.subject_input)

        # Contact selection
        contact_layout = QHBoxLayout()
        self.contact_label = QLabel("No contact selected")
        contact_layout.addWidget(self.contact_label)

        self.select_contact_button = QPushButton("Select Contact")
        self.select_contact_button.clicked.connect(self.on_select_contact)
        contact_layout.addWidget(self.select_contact_button)

        self.clear_contact_button = QPushButton("Clear")
        self.clear_contact_button.clicked.connect(self.on_clear_contact)
        contact_layout.addWidget(self.clear_contact_button)

        form_layout.addRow("Contact:", contact_layout)

        # Application selection
        app_layout = QHBoxLayout()
        self.application_label = QLabel("No application selected")
        app_layout.addWidget(self.application_label)

        self.select_app_button = QPushButton("Select Application")
        self.select_app_button.clicked.connect(self.on_select_application)
        app_layout.addWidget(self.select_app_button)

        self.clear_app_button = QPushButton("Clear")
        self.clear_app_button.clicked.connect(self.on_clear_application)
        app_layout.addWidget(self.clear_app_button)

        form_layout.addRow("Application:", app_layout)

        # Notes field
        self.notes_input = QTextEdit()
        form_layout.addRow("Notes:", self.notes_input)

        layout.addLayout(form_layout)

        # Bottom buttons
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.on_save)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def load_interaction_data(self):
        """Load interaction data for editing."""
        try:
            service = InteractionService()
            self.interaction_data = service.get(self.interaction_id)

            if not self.interaction_data:
                QMessageBox.warning(self, "Error", f"Interaction {self.interaction_id} not found")
                return

            # Set values
            interaction_type = self.interaction_data.get("interaction_type", "")
            index = self.type_combo.findText(interaction_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)

            # Set date and time
            if self.interaction_data.get("date"):
                try:
                    date_obj = datetime.fromisoformat(self.interaction_data["date"].replace("Z", "+00:00"))
                    self.datetime_input.setDateTime(date_obj)
                except (ValueError, TypeError):
                    self.datetime_input.setDateTime(datetime.now())

            # Set subject
            self.subject_input.setText(self.interaction_data.get("subject", ""))

            # Set notes
            self.notes_input.setText(self.interaction_data.get("notes", ""))

            # Set contact ID
            self.contact_id = self.interaction_data.get("contact_id")
            self._update_contact_display()

            # Set application ID
            self.application_id = self.interaction_data.get("application_id")
            self._update_application_display()

        except Exception as e:
            logger.error(f"Error loading interaction data: {e}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Failed to load interaction data: {str(e)}")

    def _update_contact_display(self):
        """Update the contact label with the current contact info."""
        if not self.contact_id:
            self.contact_label.setText("No contact selected")
            return

        try:
            service = ContactService()
            contact = service.get(self.contact_id)

            if contact:
                self.contact_label.setText(f"{contact.get('name', '')} (ID: {self.contact_id})")
            else:
                self.contact_label.setText(f"Unknown Contact (ID: {self.contact_id})")

        except Exception as e:
            logger.error(f"Error getting contact info: {e}", exc_info=True)
            self.contact_label.setText(f"Error getting contact (ID: {self.contact_id})")

    def _update_application_display(self):
        """Update the application label with the current application info."""
        if not self.application_id:
            self.application_label.setText("No application selected")
            return

        try:
            service = ApplicationService()
            application = service.get(self.application_id)

            if application:
                job_title = application.get("job_title", "")
                company_name = application.get("company", {}).get("name", "")
                self.application_label.setText(f"{job_title} at {company_name} (ID: {self.application_id})")
            else:
                self.application_label.setText(f"Unknown Application (ID: {self.application_id})")

        except Exception as e:
            logger.error(f"Error getting application info: {e}", exc_info=True)
            self.application_label.setText(f"Error getting application (ID: {self.application_id})")

    @pyqtSlot()
    def on_select_contact(self):
        """Open dialog to select a contact."""
        dialog = ContactSelectorDialog(self)
        if dialog.exec():
            self.contact_id = dialog.selected_contact_id
            self._update_contact_display()

    @pyqtSlot()
    def on_clear_contact(self):
        """Clear the selected contact."""
        self.contact_id = None
        self.contact_label.setText("No contact selected")

    @pyqtSlot()
    def on_select_application(self):
        """Open dialog to select an application."""
        dialog = ApplicationSelectorDialog(self)
        if dialog.exec():
            self.application_id = dialog.selected_application_id
            self._update_application_display()

    @pyqtSlot()
    def on_clear_application(self):
        """Clear the selected application."""
        self.application_id = None
        self.application_label.setText("No application selected")

    @pyqtSlot()
    def on_save(self):
        """Save the interaction data."""
        # Check for required fields
        if not self.contact_id:
            QMessageBox.warning(self, "Missing Data", "Please select a contact for this interaction")
            return

        # Gather data
        interaction_data = {
            "interaction_type": self.type_combo.currentText(),
            "date": self.datetime_input.dateTime().toString(Qt.DateFormat.ISODate),
            "subject": self.subject_input.text(),
            "notes": self.notes_input.toPlainText(),
            "contact_id": self.contact_id,
        }

        # Add application ID if available
        if self.application_id:
            interaction_data["application_id"] = self.application_id

        try:
            service = InteractionService()

            if self.interaction_id:
                # Update existing interaction
                result = service.update(self.interaction_id, interaction_data)
                if result:
                    if self.main_window:
                        self.main_window.show_status_message("Interaction updated successfully")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "Failed to update interaction")
            else:
                # Create new interaction
                new_id = service.create(interaction_data)
                if new_id:
                    if self.main_window:
                        self.main_window.show_status_message("Interaction created successfully")
                    self.interaction_id = new_id
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "Failed to create interaction")

        except Exception as e:
            logger.error(f"Error saving interaction: {e}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Error saving interaction: {str(e)}")
