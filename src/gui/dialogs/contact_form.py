from typing import Any

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

from src.services.company_service import CompanyService
from src.services.contact_service import ContactService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ContactForm(QDialog):
    """Dialog for creating or editing a contact."""

    def __init__(self, parent=None, contact_id=None, readonly=False) -> None:
        super().__init__(parent)
        self.main_window = parent.main_window if parent else None
        self.contact_id = contact_id
        self.readonly = readonly
        self.companies: list[dict[str, Any]] = []

        title = "View Contact" if readonly else "Edit Contact" if contact_id else "New Contact"
        self.setWindowTitle(title)
        self.resize(500, 400)

        self._init_ui()

        # Load data if editing
        if self.contact_id:
            self.load_contact()

    def _init_ui(self) -> None:
        """Initialize the form UI."""
        layout = QVBoxLayout(self)

        # Form layout for contact fields
        form_layout = QFormLayout()

        # Contact name
        self.name_input = QLineEdit()
        self.name_input.setReadOnly(self.readonly)
        form_layout.addRow("Name*:", self.name_input)

        # Title
        self.title_input = QLineEdit()
        self.title_input.setReadOnly(self.readonly)
        form_layout.addRow("Title:", self.title_input)

        # Company selection with new company button
        company_layout = QHBoxLayout()
        self.company_select = QComboBox()
        self.company_select.setEnabled(not self.readonly)
        company_layout.addWidget(self.company_select)

        if not self.readonly:
            self.new_company_btn = QPushButton("+ New")
            self.new_company_btn.clicked.connect(self.on_new_company)
            company_layout.addWidget(self.new_company_btn)

        form_layout.addRow("Company:", company_layout)

        # Contact information
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@example.com")
        self.email_input.setReadOnly(self.readonly)
        form_layout.addRow("Email:", self.email_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("(123) 456-7890")
        self.phone_input.setReadOnly(self.readonly)
        form_layout.addRow("Phone:", self.phone_input)

        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setReadOnly(self.readonly)
        form_layout.addRow("Notes:", self.notes_input)

        layout.addLayout(form_layout)

        # Required fields note
        layout.addWidget(QLabel("* Required fields"))

        # Button row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        if not self.readonly:
            self.save_btn = QPushButton("Save")
            self.save_btn.clicked.connect(self.save_contact)
            btn_layout.addWidget(self.save_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Load companies for dropdown
        self.load_companies()

    def load_companies(self) -> None:
        """Load companies for the dropdown."""
        try:
            service = CompanyService()
            self.companies = service.get_all()

            self.company_select.clear()
            self.company_select.addItem("No Company", "")
            for company in self.companies:
                self.company_select.addItem(company["name"], company["id"])

        except Exception as e:
            logger.error(f"Error loading companies: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading companies: {str(e)}")

    def load_contact(self) -> None:
        """Load contact data for editing."""
        try:
            service = ContactService()
            contact_data = service.get(int(self.contact_id))

            if not contact_data:
                if self.main_window:
                    self.main_window.show_status_message(f"Contact {self.contact_id} not found")
                return

            # Populate form fields
            self.name_input.setText(contact_data["name"])

            if contact_data.get("title"):
                self.title_input.setText(contact_data["title"])

            if contact_data.get("email"):
                self.email_input.setText(contact_data["email"])

            if contact_data.get("phone"):
                self.phone_input.setText(contact_data["phone"])

            if contact_data.get("notes"):
                self.notes_input.setPlainText(contact_data["notes"])

            # Set company if available
            if contact_data.get("company") and contact_data["company"].get("id"):
                company_id = contact_data["company"]["id"]
                index = self.company_select.findData(company_id)
                if index >= 0:
                    self.company_select.setCurrentIndex(index)

        except Exception as e:
            logger.error(f"Error loading contact: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading contact: {str(e)}")

    def save_contact(self) -> None:
        """Save the contact data."""
        try:
            # Collect data from form
            name = self.name_input.text().strip()
            title = self.title_input.text().strip()
            company_id = self.company_select.currentData()
            email = self.email_input.text().strip()
            phone = self.phone_input.text().strip()
            notes = self.notes_input.toPlainText().strip()

            # Validate required fields
            if not name:
                QMessageBox.warning(self, "Validation Error", "Contact name is required")
                self.name_input.setFocus()
                return

            # Prepare data
            contact_data = {
                "name": name,
                "title": title or None,
                "company_id": int(company_id) if company_id else None,
                "email": email or None,
                "phone": phone or None,
                "notes": notes or None,
            }

            service = ContactService()

            if self.contact_id:
                # Update existing contact
                service.update(int(self.contact_id), contact_data)
                message = "Contact updated successfully"
            else:
                # Create new contact
                result = service.create(contact_data)
                self.contact_id = result["id"]
                message = "Contact created successfully"

            if self.main_window:
                self.main_window.show_status_message(message)

            self.accept()

        except Exception as e:
            logger.error(f"Error saving contact: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error saving contact: {str(e)}")

    def on_new_company(self) -> None:
        """Open dialog to create a new company."""
        from src.gui.dialogs.company_form import CompanyForm

        dialog = CompanyForm(self)
        if dialog.exec():
            self.load_companies()
