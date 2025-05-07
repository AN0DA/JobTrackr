from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from src.services.contact_service import ContactService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ContactSelectorDialog(QDialog):
    """Dialog for selecting a contact to associate with an application or other entity."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent.main_window if parent else None
        self.selected_contact_id = None

        self.setWindowTitle("Select Contact")
        self.resize(600, 400)

        self._init_ui()
        self.load_contacts()

    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter name, email, title, etc.")
        self.search_input.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Contacts table
        layout.addWidget(QLabel("Select a contact:"))
        self.contacts_table = QTableWidget(0, 5)
        self.contacts_table.setHorizontalHeaderLabels(["ID", "Name", "Title", "Email", "Company"])
        self.contacts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.contacts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.contacts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.contacts_table.doubleClicked.connect(self.on_table_double_clicked)
        layout.addWidget(self.contacts_table)

        # Bottom buttons with "Add New Contact" option
        button_layout = QHBoxLayout()

        self.new_contact_button = QPushButton("Add New Contact")
        self.new_contact_button.clicked.connect(self.on_add_new_contact)

        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.on_select)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.new_contact_button)
        button_layout.addStretch()
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_contacts(self, search_term=None):
        """Load contacts with optional search filtering."""
        try:
            self.contacts_table.setRowCount(0)

            # Get contacts from service
            service = ContactService()
            contacts = service.search_contacts(search_term) if search_term else service.get_contacts()

            if not contacts:
                self.contacts_table.insertRow(0)
                self.contacts_table.setItem(0, 0, QTableWidgetItem("No contacts found"))
                self.contacts_table.setItem(0, 1, QTableWidgetItem(""))
                self.contacts_table.setItem(0, 2, QTableWidgetItem(""))
                self.contacts_table.setItem(0, 3, QTableWidgetItem(""))
                self.contacts_table.setItem(0, 4, QTableWidgetItem(""))
                return

            # Populate table
            for i, contact in enumerate(contacts):
                self.contacts_table.insertRow(i)

                # Store the contact ID for later retrieval
                id_item = QTableWidgetItem(str(contact.get("id", "")))
                id_item.setData(Qt.ItemDataRole.UserRole, contact.get("id"))
                self.contacts_table.setItem(i, 0, id_item)

                self.contacts_table.setItem(i, 1, QTableWidgetItem(contact.get("name", "")))
                self.contacts_table.setItem(i, 2, QTableWidgetItem(contact.get("title", "")))
                self.contacts_table.setItem(i, 3, QTableWidgetItem(contact.get("email", "")))

                # Get company name if available
                company_name = ""
                if contact.get("company"):
                    company_name = contact["company"].get("name", "")
                self.contacts_table.setItem(i, 4, QTableWidgetItem(company_name))

        except Exception as e:
            logger.error(f"Error loading contacts: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading contacts: {str(e)}")

    @pyqtSlot(str)
    def on_search(self, text):
        """Handle search input changes."""
        if not text:
            self.load_contacts()
        else:
            self.load_contacts(text)

    @pyqtSlot()
    def on_select(self):
        """Handle select button click."""
        selected_rows = self.contacts_table.selectedItems()
        if not selected_rows:
            if self.main_window:
                self.main_window.show_status_message("No contact selected")
            return

        # Get the contact ID from the first column
        contact_id_item = self.contacts_table.item(selected_rows[0].row(), 0)
        if not contact_id_item or contact_id_item.text() == "No contacts found":
            return

        self.selected_contact_id = contact_id_item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    @pyqtSlot()
    def on_table_double_clicked(self, index):
        """Handle double-click on table row."""
        if self.contacts_table.item(index.row(), 0).text() == "No contacts found":
            return

        contact_id_item = self.contacts_table.item(index.row(), 0)
        self.selected_contact_id = contact_id_item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    @pyqtSlot()
    def on_add_new_contact(self):
        """Open dialog to add a new contact."""
        from src.gui.dialogs.contact_form import ContactForm

        dialog = ContactForm(self)
        if dialog.exec():
            # Reload contacts with the newly added one
            self.load_contacts()

            # If we can get the ID of the newly created contact, select it
            if dialog.contact_id:
                self.selected_contact_id = dialog.contact_id
                self.accept()
