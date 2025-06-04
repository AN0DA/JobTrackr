from typing import Any

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.db.database import get_session
from src.gui.components.data_table import DataTable
from src.gui.dialogs.contact_detail import ContactDetailDialog
from src.gui.dialogs.contact_form import ContactForm
from src.services.company_service import CompanyService
from src.services.contact_service import ContactService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ContactsTab(QWidget):
    """
    Tab for managing contacts.

    Provides UI and logic for listing, searching, filtering, viewing, editing, and deleting contacts.
    """

    def __init__(self, parent=None) -> None:
        """
        Initialize the contacts tab.

        Args:
            parent: Parent widget (main window).
        """
        super().__init__(parent)
        self.main_window = parent
        self.companies: list[dict[str, Any]] = []
        self.company_filter = None
        self._init_ui()
        self.load_companies()  # Load companies first before contacts

    def _init_ui(self) -> None:
        """
        Initialize the contacts tab UI components and layout.
        """
        layout = QVBoxLayout(self)

        # Header section with filters
        header_layout = QHBoxLayout()

        # Company filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Company:"))
        self.company_filter_combo = QComboBox()
        self.company_filter_combo.currentTextChanged.connect(self.on_company_filter_changed)
        filter_layout.addWidget(self.company_filter_combo)

        # Search box
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search contacts...")
        self.search_input.returnPressed.connect(self.on_search)
        self.search_button = QPushButton("🔍")
        self.search_button.clicked.connect(self.on_search)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)

        # New contact button
        self.new_contact_button = QPushButton("New Contact")
        self.new_contact_button.clicked.connect(self.on_new_contact)

        # Add all components to header
        header_layout.addLayout(filter_layout)
        header_layout.addLayout(search_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.new_contact_button)

        layout.addLayout(header_layout)

        # Table for contacts
        self.table = DataTable(0, ["ID", "Name", "Title", "Company", "Email", "Phone"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemDoubleClicked.connect(self.on_row_double_clicked)
        layout.addWidget(self.table)

        # Action buttons
        actions_layout = QHBoxLayout()
        self.view_button = QPushButton("View")
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        self.view_button.clicked.connect(self.on_view_contact)
        self.edit_button.clicked.connect(self.on_edit_contact)
        self.delete_button.clicked.connect(self.on_delete_contact)

        # Initially disable buttons until selection
        self.view_button.setEnabled(False)
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)

        actions_layout.addStretch()
        actions_layout.addWidget(self.view_button)
        actions_layout.addWidget(self.edit_button)
        actions_layout.addWidget(self.delete_button)
        layout.addLayout(actions_layout)

        self.setLayout(layout)

        # Connect selection signal
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

    def load_companies(self) -> None:
        """
        Load companies for the company filter dropdown.
        """
        try:
            service = CompanyService()
            self.companies = service.get_all()

            # Create options list
            self.company_filter_combo.clear()
            self.company_filter_combo.addItem("All Companies")

            for company in self.companies:
                self.company_filter_combo.addItem(company["name"], company["id"])

            self.company_filter_combo.addItem("No Company", "None")

            # Now load contacts after company filter is set up
            self.load_contacts()

        except Exception as e:
            logger.error(f"Error loading companies: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading companies: {str(e)}")

    def load_contacts(self, company_id=None) -> None:
        """
        Load contacts, optionally filtered by company.

        Args:
            company_id: ID of the company to filter by, or None for all.
        """
        try:
            self.main_window.show_status_message("Loading contacts...")
            self.company_filter = company_id

            service = ContactService()
            session = get_session()
            try:
                contacts = service.get_all()
            finally:
                session.close()

            # Apply company filter if specified
            if company_id:
                contacts = [c for c in contacts if c.get("company", {}).get("id") == company_id]

            # Clear and update table
            self.table.setRowCount(0)

            if not contacts:
                self.main_window.show_status_message("No contacts found")
                return

            for i, contact in enumerate(contacts):
                self.table.insertRow(i)

                # Add items to the row
                self.table.setItem(i, 0, QTableWidgetItem(str(contact["id"])))
                self.table.setItem(i, 1, QTableWidgetItem(contact["name"]))
                self.table.setItem(i, 2, QTableWidgetItem(contact.get("title", "")))
                company_name = contact.get("company", {}).get("name", "")
                self.table.setItem(i, 3, QTableWidgetItem(company_name))
                self.table.setItem(i, 4, QTableWidgetItem(contact.get("email", "")))
                self.table.setItem(i, 5, QTableWidgetItem(contact.get("phone", "")))

            count = len(contacts)
            self.main_window.show_status_message(f"Loaded {count} contact{'s' if count != 1 else ''}")

        except Exception as e:
            logger.error(f"Error loading contacts: {e}", exc_info=True)
            self.main_window.show_status_message(f"Error loading contacts: {str(e)}")

    def search_contacts(self, search_term) -> None:
        """
        Search contacts by name, email, or title, and update the table.

        Args:
            search_term: The search string to filter contacts.
        """
        try:
            if not search_term:
                self.load_contacts(self.company_filter)
                return

            self.main_window.show_status_message(f"Searching for '{search_term}'...")

            service = ContactService()
            session = get_session()
            try:
                contacts = service.search_contacts(search_term, session=session)
            finally:
                session.close()

            # Apply company filter if active
            if self.company_filter:
                if self.company_filter == "None":
                    # Filter for contacts without company
                    contacts = [c for c in contacts if not c.get("company")]
                else:
                    filter_id = int(self.company_filter)
                    contacts = [c for c in contacts if c.get("company", {}).get("id") == filter_id]

            # Update table
            self.table.setRowCount(0)

            if not contacts:
                self.main_window.show_status_message(f"No contacts found matching '{search_term}'")
                return

            for i, contact in enumerate(contacts):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(str(contact["id"])))
                self.table.setItem(i, 1, QTableWidgetItem(contact["name"]))
                self.table.setItem(i, 2, QTableWidgetItem(contact.get("title", "")))
                company_name = contact.get("company", {}).get("name", "")
                self.table.setItem(i, 3, QTableWidgetItem(company_name))
                self.table.setItem(i, 4, QTableWidgetItem(contact.get("email", "")))
                self.table.setItem(i, 5, QTableWidgetItem(contact.get("phone", "")))

            count = len(contacts)
            self.main_window.show_status_message(
                f"Found {count} contact{'s' if count != 1 else ''} matching '{search_term}'"
            )

        except Exception as e:
            logger.error(f"Error searching contacts: {e}", exc_info=True)
            self.main_window.show_status_message(f"Search error: {str(e)}")

    def get_selected_contact_id(self) -> int | None:
        """
        Get the ID of the currently selected contact.

        Returns:
            The selected contact's ID, or None if no selection.
        """
        selected_items = self.table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        id_item = self.table.item(row, 0)
        if id_item:
            return int(id_item.text())
        return None

    def refresh_data(self) -> None:
        """
        Refresh the contacts data in the table.
        """
        self.load_contacts(self.company_filter)

    @pyqtSlot()
    def on_selection_changed(self) -> None:
        """
        Enable or disable action buttons based on table selection.
        """
        has_selection = bool(self.table.selectedItems())
        self.view_button.setEnabled(has_selection)
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    @pyqtSlot(str)
    def on_company_filter_changed(self, company_name) -> None:
        """
        Handle changes to the company filter dropdown.

        Args:
            company_name: The selected company name from the filter.
        """
        index = self.company_filter_combo.currentIndex()
        company_id = self.company_filter_combo.itemData(index)

        if company_name == "All Companies":
            self.load_contacts(None)
        else:
            self.load_contacts(company_id)

    @pyqtSlot()
    def on_search(self) -> None:
        """
        Handle search button click or return key in search box.
        """
        search_term = self.search_input.text().strip()
        self.search_contacts(search_term)

    @pyqtSlot()
    def on_new_contact(self) -> None:
        """
        Open dialog to create a new contact and refresh the table on success.
        """
        dialog = ContactForm(self)
        if dialog.exec():
            self.refresh_data()

    @pyqtSlot()
    def on_view_contact(self) -> None:
        """
        Open dialog to view the selected contact's details.
        """
        contact_id = self.get_selected_contact_id()
        if contact_id:
            dialog = ContactDetailDialog(self, contact_id)
            dialog.exec()

    @pyqtSlot()
    def on_edit_contact(self) -> None:
        """
        Open dialog to edit the selected contact and refresh the table on success.
        """
        contact_id = self.get_selected_contact_id()
        if contact_id:
            dialog = ContactForm(self, contact_id)
            if dialog.exec():
                self.refresh_data()

    @pyqtSlot()
    def on_delete_contact(self) -> None:
        """
        Delete the selected contact and refresh the table on success.
        """
        contact_id = self.get_selected_contact_id()
        if not contact_id:
            return

        # Get contact name for confirmation message
        row = self.table.selectedItems()[0].row()
        contact_name = self.table.item(row, 1).text()

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete contact '{contact_name}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                service = ContactService()
                success = service.delete(contact_id)

                if success:
                    self.main_window.show_status_message(f"Contact '{contact_name}' deleted successfully")
                    self.refresh_data()
                else:
                    self.main_window.show_status_message(f"Failed to delete contact {contact_id}")
            except Exception as e:
                logger.error(f"Error deleting contact: {e}", exc_info=True)
                self.main_window.show_status_message(f"Error: {str(e)}")

    @pyqtSlot(QTableWidgetItem)
    def on_row_double_clicked(self, item) -> None:
        """
        Open dialog to view the contact's details when a row is double clicked.
        """
        row = item.row()
        contact_id = int(self.table.item(row, 0).text())
        dialog = ContactDetailDialog(self, contact_id)
        dialog.exec()
        self.refresh_data()
