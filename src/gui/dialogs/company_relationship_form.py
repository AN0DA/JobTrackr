from typing import Any

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from src.config import COMPANY_RELATIONSHIP_TYPES
from src.services.company_service import CompanyService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CompanyRelationshipForm(QDialog):
    """
    Dialog for creating or editing company relationships.

    Allows the user to enter or edit relationships between companies and save them.
    """

    def __init__(self, parent=None, source_company_id=None, relationship_id=None) -> None:
        """
        Initialize the company relationship form dialog.

        Args:
            parent: Parent widget.
            source_company_id: ID of the source company.
            relationship_id: ID of the relationship to edit (None for new relationship).
        """
        super().__init__(parent)
        self.main_window = parent.main_window if parent else None
        self.source_company_id = source_company_id
        self.relationship_id = relationship_id
        self.companies: list[dict[str, Any]] = []

        title = "Edit Relationship" if relationship_id else "Add Company Relationship"
        self.setWindowTitle(title)
        self.resize(500, 400)

        self._init_ui()

        # Load relationship data if editing
        if self.relationship_id:
            self.load_relationship()

    def _init_ui(self) -> None:
        """
        Initialize the form UI components.
        """
        layout = QVBoxLayout(self)

        # Form layout for relationship fields
        form_layout = QFormLayout()

        # Source company (read-only)
        self.source_company_input = QLineEdit()
        self.source_company_input.setReadOnly(True)
        form_layout.addRow("From Company:", self.source_company_input)

        # Relationship type
        self.relationship_type = QComboBox()
        for rel_type in COMPANY_RELATIONSHIP_TYPES:
            self.relationship_type.addItem(rel_type)
        form_layout.addRow("Relationship Type:", self.relationship_type)

        # Target company
        self.target_company = QComboBox()
        form_layout.addRow("To Company:", self.target_company)

        # Notes
        self.notes_input = QTextEdit()
        form_layout.addRow("Notes:", self.notes_input)

        layout.addLayout(form_layout)

        # Button row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_relationship)
        btn_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Load companies
        self.load_companies()

    def load_companies(self) -> None:
        """
        Load companies for the dropdowns and display.
        """
        try:
            service = CompanyService()

            # Get current company details for display
            source_company = service.get(self.source_company_id)
            if source_company:
                self.source_company_input.setText(source_company["name"])

            # Get all companies
            self.companies = service.get_all()

            # Remove the source company from options
            target_companies = [c for c in self.companies if c["id"] != self.source_company_id]

            # Update target company dropdown
            self.target_company.clear()
            for company in target_companies:
                self.target_company.addItem(company["name"], company["id"])

        except Exception as e:
            logger.error(f"Error loading companies: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading companies: {str(e)}")

    def load_relationship(self) -> None:
        """
        Load relationship data for editing and populate the form fields.
        """
        try:
            service = CompanyService()
            relationship = service.get_relationship(self.relationship_id)

            if not relationship:
                if self.main_window:
                    self.main_window.show_status_message(f"Relationship {self.relationship_id} not found")
                return

            # Set relationship type
            relationship_type = relationship.get("relationship_type")
            if relationship_type:
                index = self.relationship_type.findText(relationship_type)
                if index >= 0:
                    self.relationship_type.setCurrentIndex(index)

            # Set target company
            target_id = relationship.get("target_id")
            if target_id:
                index = self.target_company.findData(target_id)
                if index >= 0:
                    self.target_company.setCurrentIndex(index)

            # Set notes
            notes = relationship.get("notes")
            if notes:
                self.notes_input.setPlainText(notes)

            if self.main_window:
                self.main_window.show_status_message("Loaded relationship data for editing")

        except Exception as e:
            logger.error(f"Error loading relationship: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading relationship: {str(e)}")

    def save_relationship(self) -> None:
        """
        Save the relationship data from the form.
        """
        try:
            service = CompanyService()

            relationship_type = self.relationship_type.currentText()
            related_company_id = self.target_company.currentData()
            notes = self.notes_input.toPlainText().strip()

            # Validate inputs
            if not relationship_type:
                QMessageBox.warning(self, "Validation Error", "Please select a relationship type")
                self.relationship_type.setFocus()
                return

            if not related_company_id:
                QMessageBox.warning(self, "Validation Error", "Please select a target company")
                self.target_company.setFocus()
                return

            # Create or update the relationship
            if self.relationship_id:
                # Update logic would go here when implemented
                if self.main_window:
                    self.main_window.show_status_message("Relationship update not yet implemented")
            else:
                service.create_relationship(
                    source_id=self.source_company_id,
                    target_id=related_company_id,
                    relationship_type=relationship_type,
                    notes=notes or None,
                )
                if self.main_window:
                    self.main_window.show_status_message("Relationship created successfully")

            self.accept()

        except Exception as e:
            logger.error(f"Error saving relationship: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error saving relationship: {str(e)}")
