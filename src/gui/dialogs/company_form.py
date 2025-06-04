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

from src.config import CompanyType
from src.services.company_service import CompanyService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CompanyForm(QDialog):
    """
    Dialog for creating or editing a company.

    Allows the user to enter or edit company details and save the company.
    """

    def __init__(self, parent=None, company_id=None, readonly=False) -> None:
        """
        Initialize the company form dialog.

        Args:
            parent: Parent widget.
            company_id: ID of the company to edit (None for new company).
            readonly (bool): If True, the form is read-only.
        """
        super().__init__(parent)
        self.main_window = parent.main_window if parent else None
        self.company_id = company_id
        self.readonly = readonly

        title = "View Company" if readonly else "Edit Company" if company_id else "New Company"
        self.setWindowTitle(title)
        self.resize(500, 400)

        self._init_ui()

        # Load data if editing
        if self.company_id:
            self.load_company()

    def _init_ui(self) -> None:
        """
        Initialize the form UI components.
        """
        layout = QVBoxLayout(self)

        # Form layout for company fields
        form_layout = QFormLayout()

        # Company name
        self.name_input = QLineEdit()
        self.name_input.setReadOnly(self.readonly)
        form_layout.addRow("Company Name*:", self.name_input)

        # Website
        self.website_input = QLineEdit()
        self.website_input.setReadOnly(self.readonly)
        form_layout.addRow("Website:", self.website_input)

        # Company type
        self.type_select = QComboBox()
        for company_type in CompanyType:
            self.type_select.addItem(company_type.value)
        self.type_select.setEnabled(not self.readonly)
        form_layout.addRow("Company Type:", self.type_select)

        # Industry
        self.industry_input = QLineEdit()
        self.industry_input.setReadOnly(self.readonly)
        form_layout.addRow("Industry:", self.industry_input)

        # Size
        self.size_input = QLineEdit()
        self.size_input.setPlaceholderText("e.g. 1-50, 51-200, 201-500, etc.")
        self.size_input.setReadOnly(self.readonly)
        form_layout.addRow("Size:", self.size_input)

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
            self.save_btn.clicked.connect(self.save_company)
            btn_layout.addWidget(self.save_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_company(self) -> None:
        """
        Load company data for editing and populate the form fields.
        """
        try:
            service = CompanyService()
            company_data = service.get(int(self.company_id))

            if not company_data:
                if self.main_window:
                    self.main_window.show_status_message(f"Company {self.company_id} not found")
                return

            # Populate form fields
            self.name_input.setText(company_data["name"])

            if company_data.get("website"):
                self.website_input.setText(company_data["website"])

            if company_data.get("industry"):
                self.industry_input.setText(company_data["industry"])

            if company_data.get("size"):
                self.size_input.setText(company_data["size"])

            if company_data.get("type"):
                index = self.type_select.findText(company_data["type"])
                if index >= 0:
                    self.type_select.setCurrentIndex(index)

            if company_data.get("notes"):
                self.notes_input.setPlainText(company_data["notes"])

        except Exception as e:
            logger.error(f"Error loading company: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error: {str(e)}")

    def save_company(self) -> None:
        """
        Save the company data from the form.
        """
        try:
            # Collect data from form
            name = self.name_input.text().strip()
            website = self.website_input.text().strip()
            company_type = self.type_select.currentText()
            industry = self.industry_input.text().strip()
            size = self.size_input.text().strip()
            notes = self.notes_input.toPlainText().strip()

            # Validate required fields
            if not name:
                QMessageBox.warning(self, "Validation Error", "Company name is required")
                self.name_input.setFocus()
                return

            # Prepare data
            company_data = {
                "name": name,
                "website": website or None,
                "industry": industry or None,
                "size": size or None,
                "type": company_type,
                "notes": notes or None,
            }

            service = CompanyService()

            if self.company_id:
                # Update existing company
                service.update(int(self.company_id), company_data)
                message = "Company updated successfully"
            else:
                # Create new company
                result = service.create(company_data)
                self.company_id = result["id"]
                message = "Company created successfully"

            if self.main_window:
                self.main_window.show_status_message(message)

            self.accept()

        except Exception as e:
            logger.error(f"Error saving company: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error saving company: {str(e)}")
