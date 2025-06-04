from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.gui.components.data_table import DataTable
from src.gui.dialogs.contact_form import ContactForm
from src.gui.dialogs.interaction_form import InteractionForm
from src.services.contact_service import ContactService
from src.services.interaction_service import InteractionService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ContactDetailDialog(QDialog):
    """
    Dialog for viewing contact details.

    Displays all information, notes, interactions, and associated applications for a contact.
    """

    def __init__(self, parent=None, contact_id=None) -> None:
        """
        Initialize the contact detail dialog.

        Args:
            parent: Parent widget.
            contact_id: ID of the contact to display.
        """
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
        """
        Initialize the dialog UI, including header, tabs, and layout.
        """
        layout = QVBoxLayout(self)

        # Header with contact info
        header_layout = QHBoxLayout()

        # Contact identity
        self.identity_layout = QVBoxLayout()
        self.contact_name = QLabel("")
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setBold(True)
        self.contact_name.setFont(name_font)

        self.contact_title = QLabel("")
        title_font = QFont()
        title_font.setPointSize(12)
        self.contact_title.setFont(title_font)

        self.contact_company = QLabel("")

        self.identity_layout.addWidget(self.contact_name)
        self.identity_layout.addWidget(self.contact_title)
        self.identity_layout.addWidget(self.contact_company)

        # Action buttons
        action_layout = QVBoxLayout()
        self.edit_button = QPushButton("Edit Contact")
        self.edit_button.clicked.connect(self.on_edit_contact)

        self.add_interaction_button = QPushButton("Add Interaction")
        self.add_interaction_button.clicked.connect(self.on_add_interaction)

        action_layout.addWidget(self.edit_button)
        action_layout.addWidget(self.add_interaction_button)

        header_layout.addLayout(self.identity_layout, 2)
        header_layout.addLayout(action_layout, 1)

        layout.addLayout(header_layout)

        # Contact details
        details_layout = QFormLayout()

        self.email_label = QLabel("")
        self.email_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        details_layout.addRow("Email:", self.email_label)

        self.phone_label = QLabel("")
        self.phone_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        details_layout.addRow("Phone:", self.phone_label)

        self.linkedin_label = QLabel("")
        self.linkedin_label.setOpenExternalLinks(True)
        details_layout.addRow("LinkedIn:", self.linkedin_label)

        layout.addLayout(details_layout)

        # Tab widget
        self.tabs = QTabWidget()

        # Tab 1: Notes
        notes_tab = QWidget()
        notes_layout = QVBoxLayout(notes_tab)

        notes_layout.addWidget(QLabel("Notes:"))
        self.notes_display = QTextEdit()
        self.notes_display.setReadOnly(True)
        notes_layout.addWidget(self.notes_display)

        # Tab 2: Interactions
        interactions_tab = QWidget()
        interactions_layout = QVBoxLayout(interactions_tab)

        interactions_layout.addWidget(QLabel("Interactions"))

        # Interactions table
        self.interactions_table = DataTable(0, ["Date", "Type", "Subject", "Notes"])
        self.interactions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.interactions_table.setSelectionBehavior(DataTable.SelectionBehavior.SelectRows)
        self.interactions_table.doubleClicked.connect(self.on_interaction_double_clicked)
        interactions_layout.addWidget(self.interactions_table)

        # Interactions action buttons
        interaction_actions = QHBoxLayout()

        self.edit_interaction_button = QPushButton("Edit Interaction")
        self.edit_interaction_button.clicked.connect(self.on_edit_interaction)

        self.delete_interaction_button = QPushButton("Delete Interaction")
        self.delete_interaction_button.clicked.connect(self.on_delete_interaction)

        interaction_actions.addWidget(self.edit_interaction_button)
        interaction_actions.addWidget(self.delete_interaction_button)
        interaction_actions.addStretch()

        interactions_layout.addLayout(interaction_actions)

        # Tab 3: Applications
        applications_tab = QWidget()
        applications_layout = QVBoxLayout(applications_tab)

        applications_layout.addWidget(QLabel("Associated Applications"))

        # Applications table
        self.applications_table = DataTable(0, ["Job Title", "Company", "Status", "Applied Date"])
        self.applications_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.applications_table.setSelectionBehavior(DataTable.SelectionBehavior.SelectRows)
        self.applications_table.doubleClicked.connect(self.on_application_double_clicked)
        applications_layout.addWidget(self.applications_table)

        # Add tabs to widget
        self.tabs.addTab(notes_tab, "Notes")
        self.tabs.addTab(interactions_tab, "Interactions")
        self.tabs.addTab(applications_tab, "Applications")

        layout.addWidget(self.tabs)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)

        self.delete_button = QPushButton("Delete Contact")
        self.delete_button.clicked.connect(self.on_delete_contact)

        btn_layout.addWidget(self.delete_button)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_button)

        layout.addLayout(btn_layout)

    def load_contact_data(self) -> None:
        """
        Load all contact data and populate the UI fields and tabs.
        """
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
            self.contact_title.setText(self.contact_data.get("title", ""))

            # Get company name if available
            company_name = ""
            if self.contact_data.get("company"):
                company_name = self.contact_data["company"].get("name", "")
            self.contact_company.setText(company_name)

            # Update details
            self.email_label.setText(self.contact_data.get("email", ""))
            self.phone_label.setText(self.contact_data.get("phone", ""))

            # Update LinkedIn with clickable link
            linkedin = self.contact_data.get("linkedin", "")
            if linkedin:
                self.linkedin_label.setText(f"<a href='{linkedin}'>{linkedin}</a>")
            else:
                self.linkedin_label.setText("No LinkedIn profile provided")

            # Update notes
            self.notes_display.setText(self.contact_data.get("notes", ""))

            # Load interactions and applications
            self.load_interactions()
            self.load_applications()

            if self.main_window:
                self.main_window.show_status_message(f"Viewing contact: {self.contact_data.get('name', 'Unknown')}")

        except Exception as e:
            logger.error(f"Error loading contact data: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading contact data: {str(e)}")

    def load_interactions(self) -> None:
        """
        Load interactions for this contact and update the interactions table.
        """
        try:
            self.interactions_table.setRowCount(0)

            if not self.contact_id:
                return

            # Get interactions for this contact
            service = InteractionService()
            interactions = service.get_interactions_by_contact(self.contact_id)

            if not interactions:
                self.interactions_table.insertRow(0)
                self.interactions_table.setItem(0, 0, QTableWidgetItem("No interactions found"))
                self.interactions_table.setItem(0, 1, QTableWidgetItem(""))
                self.interactions_table.setItem(0, 2, QTableWidgetItem(""))
                self.interactions_table.setItem(0, 3, QTableWidgetItem(""))
                return

            for i, interaction in enumerate(interactions):
                self.interactions_table.insertRow(i)

                # Store the interaction ID for later retrieval
                date_item = QTableWidgetItem(interaction.get("date", "").split("T")[0])
                date_item.setData(Qt.ItemDataRole.UserRole, interaction.get("id"))
                self.interactions_table.setItem(i, 0, date_item)

                self.interactions_table.setItem(i, 1, QTableWidgetItem(interaction.get("interaction_type", "")))
                self.interactions_table.setItem(i, 2, QTableWidgetItem(interaction.get("subject", "")))

                # Truncate notes if too long
                notes = interaction.get("notes", "")
                if len(notes) > 50:
                    notes = notes[:50] + "..."
                self.interactions_table.setItem(i, 3, QTableWidgetItem(notes))

        except Exception as e:
            logger.error(f"Error loading interactions: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading interactions: {str(e)}")

    def load_applications(self) -> None:
        """
        Load applications associated with this contact and update the applications table.
        """
        try:
            self.applications_table.setRowCount(0)

            if not self.contact_id:
                return

            # Get applications associated with this contact
            service = ContactService()
            applications = service.get_associated_applications(self.contact_id)

            if not applications:
                self.applications_table.insertRow(0)
                self.applications_table.setItem(0, 0, QTableWidgetItem("No applications found"))
                self.applications_table.setItem(0, 1, QTableWidgetItem(""))
                self.applications_table.setItem(0, 2, QTableWidgetItem(""))
                self.applications_table.setItem(0, 3, QTableWidgetItem(""))
                return

            for i, app in enumerate(applications):
                self.applications_table.insertRow(i)

                # Store the application ID for later retrieval
                job_title_item = QTableWidgetItem(app.get("job_title", ""))
                job_title_item.setData(Qt.ItemDataRole.UserRole, app.get("id"))
                self.applications_table.setItem(i, 0, job_title_item)

                # Company name
                company_name = ""
                if app.get("company"):
                    company_name = app["company"].get("name", "")
                self.applications_table.setItem(i, 1, QTableWidgetItem(company_name))

                self.applications_table.setItem(i, 2, QTableWidgetItem(app.get("status", "")))

                # Format date
                applied_date = app.get("applied_date", "")
                if applied_date:
                    applied_date = applied_date.split("T")[0]
                self.applications_table.setItem(i, 3, QTableWidgetItem(applied_date))

        except Exception as e:
            logger.error(f"Error loading applications: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading applications: {str(e)}")

    @pyqtSlot()
    def on_edit_contact(self) -> None:
        """
        Open dialog to edit the contact and reload data on success.
        """
        dialog = ContactForm(self, self.contact_id)
        if dialog.exec():
            self.load_contact_data()

    @pyqtSlot()
    def on_add_interaction(self) -> None:
        """
        Open dialog to add a new interaction for this contact and reload interactions on success.
        """
        dialog = InteractionForm(self, self.contact_id)
        if dialog.exec():
            self.load_interactions()
            if self.main_window:
                self.main_window.show_status_message("Interaction added successfully")

    @pyqtSlot()
    def on_edit_interaction(self) -> None:
        """
        Open dialog to edit the selected interaction and reload interactions on success.
        """
        selected_rows = self.interactions_table.selectedItems()
        if not selected_rows:
            if self.main_window:
                self.main_window.show_status_message("No interaction selected")
            return

        interaction_id = self.interactions_table.item(selected_rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        if not interaction_id:
            return

        dialog = InteractionForm(self, self.contact_id, None, interaction_id)
        if dialog.exec():
            self.load_interactions()
            if self.main_window:
                self.main_window.show_status_message("Interaction updated successfully")

    @pyqtSlot()
    def on_interaction_double_clicked(self, index) -> None:
        """
        Open interaction form when an interaction is double clicked.
        """
        if self.interactions_table.item(index.row(), 0).text() == "No interactions found":
            return

        interaction_id = self.interactions_table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
        dialog = InteractionForm(self, self.contact_id, None, interaction_id)
        if dialog.exec():
            self.load_interactions()

    @pyqtSlot()
    def on_delete_interaction(self) -> None:
        """
        Delete the selected interaction and reload interactions on success.
        """
        selected_rows = self.interactions_table.selectedItems()
        if not selected_rows:
            if self.main_window:
                self.main_window.show_status_message("No interaction selected")
            return

        interaction_id = self.interactions_table.item(selected_rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        if not interaction_id:
            return

        reply = QMessageBox.question(
            self,
            "Delete Interaction",
            "Are you sure you want to delete this interaction?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                service = InteractionService()
                result = service.delete_interaction(interaction_id)

                if result:
                    if self.main_window:
                        self.main_window.show_status_message("Interaction deleted successfully")
                    self.load_interactions()
                else:
                    if self.main_window:
                        self.main_window.show_status_message("Failed to delete interaction")
            except Exception as e:
                logger.error(f"Error deleting interaction: {e}", exc_info=True)
                if self.main_window:
                    self.main_window.show_status_message(f"Error: {str(e)}")

    @pyqtSlot()
    def on_application_double_clicked(self, index) -> None:
        """
        Open application details dialog when an application is double clicked.
        """
        from src.gui.dialogs.application_detail import ApplicationDetailDialog

        if self.applications_table.item(index.row(), 0).text() == "No applications found":
            return

        application_id = self.applications_table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
        dialog = ApplicationDetailDialog(self, application_id)
        dialog.exec()

        # Refresh applications in case there were changes
        self.load_applications()

    @pyqtSlot()
    def on_delete_contact(self) -> None:
        """
        Delete this contact and close the dialog on success.
        """
        reply = QMessageBox.question(
            self,
            "Delete Contact",
            f"Are you sure you want to delete {self.contact_data.get('name', 'this contact')}?\n\n"
            f"This will also remove all associated interactions.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                service = ContactService()
                result = service.delete(self.contact_id)

                if result:
                    if self.main_window:
                        self.main_window.show_status_message("Contact deleted successfully")
                    self.accept()
                else:
                    if self.main_window:
                        self.main_window.show_status_message("Failed to delete contact")
            except Exception as e:
                logger.error(f"Error deleting contact: {e}", exc_info=True)
                if self.main_window:
                    self.main_window.show_status_message(f"Error: {str(e)}")
