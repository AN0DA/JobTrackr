from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.gui.components.data_table import DataTable
from src.services.contact_service import ContactService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ContactDetailDialog(QDialog):
    """Dialog for viewing contact details."""

    def __init__(self, parent=None, contact_id=None) -> None:
        super().__init__(parent)
        self.main_window = parent.main_window if parent else None
        self.contact_id = contact_id
        self.contact_data = None

        self.setWindowTitle("Contact Details")
        self.resize(700, 500)

        self._init_ui()

        # Load data
        if self.contact_id:
            self.load_contact_data()

    def _init_ui(self) -> None:
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)

        # Header section with contact info and buttons
        header_layout = QHBoxLayout()

        # Contact identity section
        self.identity_layout = QVBoxLayout()
        self.contact_name = QLabel("")
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setBold(True)
        self.contact_name.setFont(name_font)

        self.contact_title = QLabel("")
        self.identity_layout.addWidget(self.contact_name)
        self.identity_layout.addWidget(self.contact_title)

        # Header actions
        actions_layout = QVBoxLayout()
        self.edit_button = QPushButton("Edit Contact")
        self.edit_button.clicked.connect(self.on_edit_contact)
        actions_layout.addWidget(self.edit_button)

        header_layout.addLayout(self.identity_layout, 2)
        header_layout.addLayout(actions_layout, 1)
        layout.addLayout(header_layout)

        # Contact info grid
        info_form = QFormLayout()
        self.company_label = QLabel("")
        info_form.addRow("Company:", self.company_label)

        self.email_label = QLabel("")
        info_form.addRow("Email:", self.email_label)

        self.phone_label = QLabel("")
        info_form.addRow("Phone:", self.phone_label)

        layout.addLayout(info_form)

        # Notes section
        layout.addWidget(QLabel("Notes:"))
        self.notes_display = QTextEdit()
        self.notes_display.setReadOnly(True)
        layout.addWidget(self.notes_display)

        # Tab widget for applications and interactions
        self.tabs = QTabWidget()

        # Tab 1: Associated Applications
        applications_tab = QWidget()
        applications_layout = QVBoxLayout(applications_tab)

        applications_layout.addWidget(QLabel("Associated Applications"))

        # Applications table
        self.applications_table = DataTable(0, ["ID", "Job Title", "Position", "Status", "Applied Date"])
        self.applications_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.applications_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.applications_table.doubleClicked.connect(self.on_application_double_clicked)
        applications_layout.addWidget(self.applications_table)

        # Tab 2: Recent Interactions
        interactions_tab = QWidget()
        interactions_layout = QVBoxLayout(interactions_tab)

        interactions_layout.addWidget(QLabel("Recent Interactions"))

        # Interactions table
        self.interactions_table = DataTable(0, ["Date", "Type", "Application", "Details"])
        self.interactions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.interactions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        interactions_layout.addWidget(self.interactions_table)

        # Add tabs to widget
        self.tabs.addTab(applications_tab, "Applications")
        self.tabs.addTab(interactions_tab, "Interactions")

        layout.addWidget(self.tabs)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.add_to_app_button = QPushButton("Add to Application")
        self.add_to_app_button.clicked.connect(self.on_add_to_application)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)

        btn_layout.addWidget(self.add_to_app_button)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_button)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_contact_data(self) -> None:
        """Load all contact data and populate the UI."""
        try:
            # Load contact details
            service = ContactService()
            self.contact_data = service.get(self.contact_id)

            if not self.contact_data:
                if self.main_window:
                    self.main_window.show_status_message(f"Contact {self.contact_id} not found")
                return

            # Update header
            self.contact_name.setText(self.contact_data.get("name", "Unknown"))

            # Make sure title is a string
            title = self.contact_data.get("title", "")
            if title is None:
                title = "No title"
            self.contact_title.setText(title)

            # Update fields - ensure we always use strings for display
            company = self.contact_data.get("company", {})
            company_name = company.get("name", "") if company else ""
            if not company_name:
                company_name = "Not associated with a company"
            self.company_label.setText(company_name)

            email = self.contact_data.get("email", "")
            if email is None or email == "":
                email = "No email provided"
            self.email_label.setText(email)

            phone = self.contact_data.get("phone", "")
            if phone is None or phone == "":
                phone = "No phone provided"
            self.phone_label.setText(phone)

            # Update notes
            notes = self.contact_data.get("notes", "")
            if notes is None or notes == "":
                notes = "No notes available."
            self.notes_display.setText(notes)

            # Load applications (placeholder for now)
            self.load_applications()

            # Load interactions (placeholder for now)
            self.load_interactions()

            if self.main_window:
                self.main_window.show_status_message(f"Viewing contact: {self.contact_data.get('name', 'Unknown')}")

        except Exception as e:
            logger.error(f"Error loading contact data: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading contact data: {str(e)}")

    def load_applications(self) -> None:
        """Load applications associated with this contact (placeholder)."""
        self.applications_table.setRowCount(0)

        # Placeholder row for no applications
        self.applications_table.insertRow(0)
        self.applications_table.setItem(0, 0, QTableWidgetItem("No applications found"))
        self.applications_table.setItem(0, 1, QTableWidgetItem(""))
        self.applications_table.setItem(0, 2, QTableWidgetItem(""))
        self.applications_table.setItem(0, 3, QTableWidgetItem(""))
        self.applications_table.setItem(0, 4, QTableWidgetItem(""))

    def load_interactions(self) -> None:
        """Load interactions associated with this contact (placeholder)."""
        self.interactions_table.setRowCount(0)

        # Placeholder row for no interactions
        self.interactions_table.insertRow(0)
        self.interactions_table.setItem(0, 0, QTableWidgetItem("No interactions found"))
        self.interactions_table.setItem(0, 1, QTableWidgetItem(""))
        self.interactions_table.setItem(0, 2, QTableWidgetItem(""))
        self.interactions_table.setItem(0, 3, QTableWidgetItem(""))

    @pyqtSlot()
    def on_edit_contact(self) -> None:
        """Open dialog to edit the contact."""
        from src.gui.dialogs.contact_form import ContactForm

        dialog = ContactForm(self, self.contact_id)
        if dialog.exec():
            self.load_contact_data()

    @pyqtSlot()
    def on_add_to_application(self) -> None:
        """Open dialog to add contact to an application."""
        if self.main_window:
            self.main_window.show_status_message("Adding contact to application not yet implemented")

    @pyqtSlot()
    def on_application_double_clicked(self, index) -> None:
        """Open application details when double clicked."""
        from src.gui.dialogs.application_detail import ApplicationDetailDialog

        if self.applications_table.item(index.row(), 0).text() == "No applications found":
            return

        app_id = int(self.applications_table.item(index.row(), 0).text())
        dialog = ApplicationDetailDialog(self, app_id)
        dialog.exec()
