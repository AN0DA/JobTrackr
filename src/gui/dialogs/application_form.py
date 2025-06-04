from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.config import ApplicationStatus
from src.services.application_service import ApplicationService
from src.services.company_service import CompanyService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ApplicationForm(QDialog):
    """
    Dialog for creating or editing a job application.

    Allows the user to enter or edit job application details, select a company, and save the application.
    """

    def __init__(self, parent=None, app_id=None, readonly=False):
        """
        Initialize the application form dialog.

        Args:
            parent: Parent widget.
            app_id: ID of the application to edit (None for new application).
            readonly (bool): If True, the form is read-only.
        """
        super().__init__(parent)
        self.app_id = app_id
        self.readonly = readonly
        self.companies = []
        self.application_data = {}

        title = "View Application" if readonly else "Edit Application" if app_id else "New Application"
        self.setWindowTitle(title)
        self.resize(700, 600)

        self._init_ui()

        # Load data if editing
        if self.app_id:
            self.load_application()

    def _init_ui(self):
        """
        Initialize the form UI components.
        """
        layout = QVBoxLayout(self)

        # Create tab widget for form sections
        self.tab_widget = QTabWidget()

        # Tab 1: Essential Information
        essential_tab = QWidget()
        essential_layout = QFormLayout(essential_tab)

        self.job_title_input = QLineEdit()
        self.job_title_input.setReadOnly(self.readonly)
        essential_layout.addRow("Job Title*:", self.job_title_input)

        # Company selection with new company button
        company_layout = QHBoxLayout()
        self.company_select = QComboBox()
        self.company_select.setEnabled(not self.readonly)
        company_layout.addWidget(self.company_select)

        if not self.readonly:
            self.new_company_btn = QPushButton("+ New Company")
            self.new_company_btn.clicked.connect(self.on_new_company)
            company_layout.addWidget(self.new_company_btn)

        essential_layout.addRow("Company*:", company_layout)

        self.position_input = QLineEdit()
        self.position_input.setReadOnly(self.readonly)
        essential_layout.addRow("Position*:", self.position_input)

        self.status_select = QComboBox()
        for status in ApplicationStatus:
            self.status_select.addItem(status.value)
        self.status_select.setEnabled(not self.readonly)
        essential_layout.addRow("Status*:", self.status_select)

        self.applied_date = QDateEdit()
        self.applied_date.setCalendarPopup(True)
        self.applied_date.setDate(QDate.currentDate())
        self.applied_date.setReadOnly(self.readonly)
        essential_layout.addRow("Applied Date*:", self.applied_date)

        # Tab 2: Additional Details
        details_tab = QWidget()
        details_layout = QFormLayout(details_tab)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("City, State or Remote")
        self.location_input.setReadOnly(self.readonly)
        details_layout.addRow("Location:", self.location_input)

        # Salary range
        salary_layout = QHBoxLayout()
        self.salary_min_input = QLineEdit()
        self.salary_min_input.setPlaceholderText("Min")
        self.salary_min_input.setReadOnly(self.readonly)
        salary_layout.addWidget(self.salary_min_input)

        self.salary_max_input = QLineEdit()
        self.salary_max_input.setPlaceholderText("Max")
        self.salary_max_input.setReadOnly(self.readonly)
        salary_layout.addWidget(self.salary_max_input)

        details_layout.addRow("Salary Range:", salary_layout)

        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText("Job posting URL")
        self.link_input.setReadOnly(self.readonly)
        details_layout.addRow("Job Link:", self.link_input)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Job description")
        self.description_input.setReadOnly(self.readonly)
        details_layout.addRow("Description:", self.description_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Additional notes")
        self.notes_input.setReadOnly(self.readonly)
        details_layout.addRow("Notes:", self.notes_input)

        # Add tabs to widget
        self.tab_widget.addTab(essential_tab, "Essential Info")
        self.tab_widget.addTab(details_tab, "Additional Details")

        layout.addWidget(self.tab_widget)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_application)
        btn_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Load companies
        self.load_companies()

    def load_companies(self):
        """
        Load companies for the company dropdown.
        """
        try:
            service = CompanyService()
            self.companies = service.get_all()

            self.company_select.clear()
            for company in self.companies:
                self.company_select.addItem(company["name"], company["id"])

        except Exception as e:
            logger.error(f"Error loading companies: {e}", exc_info=True)
            if self.parent():
                self.parent().main_window.show_status_message(f"Error loading companies: {str(e)}")

    def load_application(self):
        """
        Load application data for editing and populate the form fields.
        """
        try:
            service = ApplicationService()
            app_data = service.get(int(self.app_id))

            if not app_data:
                if self.parent():
                    self.parent().main_window.show_status_message(f"Application {self.app_id} not found")
                return

            # Store application data
            self.application_data = app_data

            # Populate form fields
            self.job_title_input.setText(app_data["job_title"])
            self.position_input.setText(app_data["position"])

            # Set status
            index = self.status_select.findText(app_data["status"])
            if index >= 0:
                self.status_select.setCurrentIndex(index)

            # Set date
            date_str = app_data["applied_date"].split("T")[0]
            parts = date_str.split("-")
            if len(parts) == 3:
                self.applied_date.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))

            # Set company
            if app_data.get("company") and "id" in app_data["company"]:
                company_id = app_data["company"]["id"]
                index = self.company_select.findData(company_id)
                if index >= 0:
                    self.company_select.setCurrentIndex(index)

            # Set optional fields
            if app_data.get("location"):
                self.location_input.setText(app_data["location"])

            if app_data.get("salary_min"):
                self.salary_min_input.setText(str(app_data["salary_min"]))
            if app_data.get("salary_max"):
                self.salary_max_input.setText(str(app_data["salary_max"]))

            if app_data.get("link"):
                self.link_input.setText(app_data["link"])

            if app_data.get("description"):
                self.description_input.setPlainText(app_data["description"])

            if app_data.get("notes"):
                self.notes_input.setPlainText(app_data["notes"])

        except Exception as e:
            logger.error(f"Error loading application: {e}", exc_info=True)
            if self.parent():
                self.parent().main_window.show_status_message(f"Error: {str(e)}")

    def save_application(self):
        """
        Save the application data from the form.
        """
        try:
            # Collect data from form
            job_title = self.job_title_input.text().strip()
            position = self.position_input.text().strip()
            status = self.status_select.currentText()
            applied_date = self.applied_date.date().toString(Qt.DateFormat.ISODate)
            company_id = self.company_select.currentData()

            # Validate required fields
            if not job_title:
                QMessageBox.warning(self, "Validation Error", "Job title is required")
                self.tab_widget.setCurrentIndex(0)
                self.job_title_input.setFocus()
                return

            if not position:
                QMessageBox.warning(self, "Validation Error", "Position is required")
                self.tab_widget.setCurrentIndex(0)
                self.position_input.setFocus()
                return

            if not company_id:
                QMessageBox.warning(self, "Validation Error", "Company is required")
                self.tab_widget.setCurrentIndex(0)
                self.company_select.setFocus()
                return

            # Prepare data
            app_data = {
                "job_title": job_title,
                "position": position,
                "status": status,
                "applied_date": applied_date,
                "company_id": company_id,
                "location": self.location_input.text().strip() or None,
                "salary_min": int(self.salary_min_input.text()) if self.salary_min_input.text().strip() else None,
                "salary_max": int(self.salary_max_input.text()) if self.salary_max_input.text().strip() else None,
                "link": self.link_input.text().strip() or None,
                "description": self.description_input.toPlainText().strip() or None,
                "notes": self.notes_input.toPlainText().strip() or None,
            }

            service = ApplicationService()

            if self.app_id:
                # Update existing application
                service.update(int(self.app_id), app_data)
                message = "Application updated successfully"
            else:
                # Create new application
                result = service.create(app_data)
                self.app_id = result["id"]
                message = "Application created successfully"

            if self.parent():
                self.parent().main_window.show_status_message(message)

            self.accept()

        except ValueError as e:
            logger.error(f"Validation error: {e}", exc_info=True)
            QMessageBox.warning(self, "Validation Error", "Please enter valid numbers for salary range")
        except Exception as e:
            logger.error(f"Error saving application: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error saving application: {str(e)}")

    def on_new_company(self):
        """
        Open a dialog to create a new company and reload the company list.
        """
        from src.gui.dialogs.company_form import CompanyForm

        dialog = CompanyForm(self)
        if dialog.exec():
            self.load_companies()
