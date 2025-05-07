from datetime import datetime

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
    QScrollArea,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.config import FONT_SIZES, UI_COLORS
from src.gui.components.data_table import DataTable
from src.gui.components.status_badge import StatusBadge
from src.gui.components.styled_button import StyledButton
from src.gui.dialogs.application_form import ApplicationForm
from src.gui.dialogs.contact_selector import ContactSelectorDialog
from src.gui.dialogs.interaction_form import InteractionForm
from src.gui.dialogs.status_transition import StatusTransitionDialog
from src.services.application_service import ApplicationService
from src.services.change_record_service import ChangeRecordService
from src.services.contact_service import ContactService
from src.services.interaction_service import InteractionService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ApplicationDetailDialog(QDialog):
    """Dialog for viewing application details."""

    def __init__(self, parent=None, app_id=None) -> None:
        super().__init__(parent)
        self.main_window = parent.main_window if parent else None
        self.app_id = app_id
        self.application_data = None

        self.setWindowTitle("Application Details")
        self.resize(800, 600)

        self._init_ui()

        # Load data
        if self.app_id:
            self.load_application_data()

    def _init_ui(self) -> None:
        """Initialize the dialog UI with improved styling."""
        layout = QVBoxLayout(self)

        # Header section with application info and status
        header = QWidget()
        header.setStyleSheet(f"background-color: {UI_COLORS['card']}; border-radius: 8px;")
        header_layout = QHBoxLayout(header)

        # Application identity section
        self.identity_layout = QVBoxLayout()

        self.app_job_title = QLabel("")
        title_font = QFont()
        title_font.setPointSize(FONT_SIZES["2xl"])
        title_font.setBold(True)
        self.app_job_title.setFont(title_font)

        self.app_company = QLabel("")
        company_font = QFont()
        company_font.setPointSize(FONT_SIZES["lg"])
        self.app_company.setFont(company_font)

        self.app_position_location = QLabel("")

        self.identity_layout.addWidget(self.app_job_title)
        self.identity_layout.addWidget(self.app_company)
        self.identity_layout.addWidget(self.app_position_location)

        # Status section
        status_layout = QVBoxLayout()
        self.app_status = StatusBadge("")  # Using our new component
        self.app_applied_date = QLabel("")
        self.app_applied_date.setAlignment(Qt.AlignmentFlag.AlignCenter)

        status_layout.addWidget(QLabel("STATUS"))
        status_layout.addWidget(self.app_status)
        status_layout.addWidget(self.app_applied_date)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        header_layout.addLayout(self.identity_layout, 2)
        header_layout.addLayout(status_layout, 1)

        layout.addWidget(header)

        # Quick action buttons - using our new styled buttons
        action_layout = QHBoxLayout()
        self.edit_button = StyledButton("📝 Edit", "secondary")
        self.status_button = StyledButton("📊 Change Status", "primary")
        self.add_interaction_button = StyledButton("💬 Add Interaction", "secondary")
        self.add_contact_button = StyledButton("👤 Add Contact", "secondary")

        self.edit_button.clicked.connect(self.on_edit_application)
        self.status_button.clicked.connect(self.on_change_status)
        self.add_interaction_button.clicked.connect(self.on_add_interaction)
        self.add_contact_button.clicked.connect(self.on_add_contact)

        action_layout.addWidget(self.edit_button)
        action_layout.addWidget(self.status_button)
        action_layout.addWidget(self.add_interaction_button)
        action_layout.addWidget(self.add_contact_button)

        layout.addLayout(action_layout)

        # Tab widget for different sections
        self.tabs = QTabWidget()

        # Tab 1: Overview
        overview_tab = QWidget()
        overview_scroll = QScrollArea()
        overview_scroll.setWidgetResizable(True)
        overview_scroll.setWidget(overview_tab)

        overview_layout = QVBoxLayout(overview_tab)

        # Key details grid
        overview_form = QFormLayout()
        self.applied_date_label = QLabel("")
        overview_form.addRow("Applied Date:", self.applied_date_label)

        self.salary_label = QLabel("")
        overview_form.addRow("Salary:", self.salary_label)

        self.link_label = QLabel("")
        self.link_label.setOpenExternalLinks(True)
        overview_form.addRow("Link:", self.link_label)

        overview_layout.addLayout(overview_form)

        # Status history section
        overview_layout.addWidget(QLabel("Status History:"))
        self.status_history_table = DataTable(0, ["Date", "Status", "Notes"])
        self.status_history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.status_history_table.setMinimumHeight(150)
        overview_layout.addWidget(self.status_history_table)

        # Notes section
        overview_layout.addWidget(QLabel("Notes:"))
        self.notes_display = QTextEdit()
        self.notes_display.setReadOnly(True)
        overview_layout.addWidget(self.notes_display)

        # Tab 2: Timeline
        timeline_tab = QScrollArea()
        timeline_tab.setWidgetResizable(True)
        timeline_content = QWidget()
        timeline_layout = QVBoxLayout(timeline_content)

        self.timeline_table = DataTable(0, ["Date", "Event Type", "Details"])
        self.timeline_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        timeline_layout.addWidget(self.timeline_table)

        timeline_tab.setWidget(timeline_content)

        # Tab 3: Contacts
        contacts_tab = QWidget()
        contacts_layout = QVBoxLayout(contacts_tab)

        contacts_layout.addWidget(QLabel("Associated Contacts"))

        # Contacts table
        self.contacts_table = DataTable(0, ["ID", "Name", "Title", "Email", "Phone"])
        self.contacts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.contacts_table.setSelectionBehavior(DataTable.SelectionBehavior.SelectRows)
        self.contacts_table.doubleClicked.connect(self.on_contact_double_clicked)
        contacts_layout.addWidget(self.contacts_table)

        # Contacts actions buttons
        contacts_actions = QHBoxLayout()
        self.add_contact_button = QPushButton("Add Contact")
        self.add_contact_button.clicked.connect(self.on_add_contact)

        self.remove_contact_button = QPushButton("Remove Contact")
        self.remove_contact_button.clicked.connect(self.on_remove_contact)

        self.new_interaction_button = QPushButton("Add Interaction")
        self.new_interaction_button.clicked.connect(self.on_add_interaction)

        contacts_actions.addWidget(self.add_contact_button)
        contacts_actions.addWidget(self.remove_contact_button)
        contacts_actions.addWidget(self.new_interaction_button)
        contacts_actions.addStretch()
        contacts_layout.addLayout(contacts_actions)

        # Tab 4: Interactions
        interactions_tab = QWidget()
        interactions_layout = QVBoxLayout(interactions_tab)

        interactions_layout.addWidget(QLabel("Interactions"))

        # Interactions table
        self.interactions_table = DataTable(0, ["Date/Time", "Type", "Contact", "Details"])
        self.interactions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.interactions_table.setSelectionBehavior(DataTable.SelectionBehavior.SelectRows)
        interactions_layout.addWidget(self.interactions_table)

        # Interactions actions
        interactions_actions = QHBoxLayout()
        self.edit_interaction_button = QPushButton("Edit")
        self.edit_interaction_button.clicked.connect(self.on_edit_interaction)

        self.delete_interaction_button = QPushButton("Delete")
        self.delete_interaction_button.clicked.connect(self.on_delete_interaction)

        interactions_actions.addWidget(self.edit_interaction_button)
        interactions_actions.addWidget(self.delete_interaction_button)
        interactions_actions.addStretch()
        interactions_layout.addLayout(interactions_actions)

        # Add tabs to widget
        self.tabs.addTab(overview_scroll, "Overview")
        self.tabs.addTab(timeline_tab, "Timeline")
        self.tabs.addTab(contacts_tab, "Contacts")
        self.tabs.addTab(interactions_tab, "Interactions")

        layout.addWidget(self.tabs)

        # Bottom action buttons
        btn_layout = QHBoxLayout()
        self.back_button = QPushButton("⬅️ Back")
        self.back_button.clicked.connect(self.accept)

        self.copy_link_button = QPushButton("📋 Copy Link")
        self.copy_link_button.clicked.connect(self.on_copy_link)

        self.delete_button = QPushButton("🗑️ Delete")
        self.delete_button.clicked.connect(self.on_delete_application)

        btn_layout.addWidget(self.back_button)
        btn_layout.addStretch()
        btn_layout.addWidget(self.copy_link_button)
        btn_layout.addWidget(self.delete_button)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_application_data(self) -> None:
        """Load application data and populate the UI."""
        try:
            # Load application details
            service = ApplicationService()
            self.application_data = service.get(self.app_id)

            if not self.application_data:
                if self.main_window:
                    self.main_window.show_status_message(f"Application {self.app_id} not found")
                return

            # Update header fields
            self.app_job_title.setText(self.application_data["job_title"])

            # Show position and location together
            position = self.application_data.get("position", "")
            location = self.application_data.get("location", "")

            position_location = f"{position} | {location}" if location else position
            self.app_position_location.setText(position_location)

            # Update company info
            company_name = self.application_data.get("company", {}).get("name", "Unknown")
            self.app_company.setText(company_name)

            # Status with styling
            status = self.application_data["status"]
            self.app_status.setText(status)

            # Set status color based on value
            if status == "SAVED":
                self.app_status.setStyleSheet("color: gray;")
            elif status == "APPLIED":
                self.app_status.setStyleSheet("color: blue;")
            elif status in ["PHONE_SCREEN", "INTERVIEW", "TECHNICAL_INTERVIEW"]:
                self.app_status.setStyleSheet("color: orange;")
            elif status == "OFFER":
                self.app_status.setStyleSheet("color: green;")
            elif status == "ACCEPTED":
                self.app_status.setStyleSheet("color: green; font-weight: bold;")
            elif status in ["REJECTED", "WITHDRAWN"]:
                self.app_status.setStyleSheet("color: red;")

            # Format and display applied date
            applied_date_str = self.application_data.get("applied_date")
            if applied_date_str:
                try:
                    applied_date = datetime.fromisoformat(applied_date_str)
                    formatted_date = applied_date.strftime("%Y-%m-%d")
                    self.app_applied_date.setText(f"Applied: {formatted_date}")
                    self.applied_date_label.setText(formatted_date)
                except (ValueError, TypeError):
                    self.app_applied_date.setText("Invalid Date")
                    self.applied_date_label.setText("Invalid Date")
            else:
                self.app_applied_date.setText("No date")
                self.applied_date_label.setText("Not specified")

            # Update salary
            salary = self.application_data.get("salary", "Not specified")
            self.salary_label.setText(salary)

            # Update link with proper formatting
            link = self.application_data.get("link", "")
            if link:
                self.link_label.setText(f"<a href='{link}'>{link}</a>")
            else:
                self.link_label.setText("No link provided")

            # Update job description
            description = self.application_data.get("description", "No description available.")
            self.job_description.setPlainText(description)

            # Update notes
            notes = self.application_data.get("notes", "No notes available.")
            self.notes_display.setPlainText(notes)

            # Load other data
            self.load_status_history()
            self.load_timeline()
            self.load_interactions()
            self.load_contacts()

            if self.main_window:
                self.main_window.show_status_message(
                    f"Application details: {self.application_data['job_title']} at {company_name}"
                )

        except Exception as e:
            logger.error(f"Error loading application data: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading application details: {str(e)}")

    def load_status_history(self) -> None:
        """Load status history from change records."""
        try:
            change_service = ChangeRecordService()
            changes = change_service.get_change_records(self.app_id)

            # Filter only status changes
            status_changes = [change for change in changes if change["change_type"] == "STATUS_CHANGE"]

            # Clear existing table
            self.status_history_table.setRowCount(0)

            if not status_changes:
                # Show initial status
                self.status_history_table.insertRow(0)

                applied_date = self.application_data.get("applied_date", "Unknown")
                if isinstance(applied_date, str):
                    applied_date = applied_date.split("T")[0]

                self.status_history_table.setItem(0, 0, QTableWidgetItem(applied_date))
                self.status_history_table.setItem(
                    0, 1, QTableWidgetItem(self.application_data.get("status", "APPLIED"))
                )
                self.status_history_table.setItem(0, 2, QTableWidgetItem("Initial application status"))
                return

            # Sort by timestamp descending
            status_changes.sort(key=lambda x: x["timestamp"], reverse=True)

            for i, change in enumerate(status_changes):
                self.status_history_table.insertRow(i)

                date = change["timestamp"].split("T")[0]
                self.status_history_table.setItem(i, 0, QTableWidgetItem(date))
                self.status_history_table.setItem(i, 1, QTableWidgetItem(change["new_value"]))
                self.status_history_table.setItem(i, 2, QTableWidgetItem(change.get("notes", "")))

        except Exception as e:
            logger.error(f"Error loading status history: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading status history: {str(e)}")

    def load_timeline(self) -> None:
        """Load and display timeline events."""
        try:
            # Get change records
            change_service = ChangeRecordService()
            changes = change_service.get_change_records(self.app_id)

            # Get interactions for the timeline
            interaction_service = InteractionService()
            interactions = interaction_service.get_interactions(self.app_id)

            # Combine all events into a timeline
            timeline_events = []

            # Add change records
            for change in changes:
                event_date = datetime.fromisoformat(change["timestamp"])
                event_type = change["change_type"]

                # Format details
                if event_type == "STATUS_CHANGE":
                    details = f"Status changed from {change['old_value']} to {change['new_value']}"
                elif event_type == "APPLICATION_UPDATED":
                    details = "Application details were updated"
                else:
                    if change.get("old_value") and change.get("new_value"):
                        details = f"Changed from {change['old_value']} to {change['new_value']}"
                    elif change.get("new_value"):
                        details = f"Set to {change['new_value']}"
                    else:
                        details = "Change recorded"

                # Add to timeline with icon indicator
                timeline_events.append(
                    {
                        "date": event_date,
                        "type": event_type.replace("_", " "),
                        "details": change.get("notes", "") or details,
                        "icon": self._get_event_icon(event_type),
                    }
                )

            # Add interactions
            for interaction in interactions:
                event_date = datetime.fromisoformat(interaction["date"])
                details = (
                    f"{interaction['type']}: "
                    f"{interaction['notes'][:50] + '...' if interaction['notes'] and len(interaction['notes']) > 50 else interaction['notes'] or ''}"
                )

                timeline_events.append({"date": event_date, "type": "INTERACTION", "details": details, "icon": "💬"})

            # Add application creation as first event
            if "created_at" in self.application_data:
                creation_date = datetime.fromisoformat(self.application_data.get("created_at", ""))
                timeline_events.append(
                    {
                        "date": creation_date,
                        "type": "APPLICATION CREATED",
                        "details": f"Application created for {self.application_data['job_title']}",
                        "icon": "📝",
                    }
                )

            # Sort by date descending
            timeline_events.sort(key=lambda x: x["date"], reverse=True)

            # Update timeline table
            self.timeline_table.setRowCount(0)

            for i, event in enumerate(timeline_events):
                self.timeline_table.insertRow(i)

                formatted_date = event["date"].strftime("%Y-%m-%d %H:%M")
                self.timeline_table.setItem(i, 0, QTableWidgetItem(formatted_date))
                self.timeline_table.setItem(i, 1, QTableWidgetItem(f"{event['icon']} {event['type']}"))
                self.timeline_table.setItem(i, 2, QTableWidgetItem(event["details"]))

        except Exception as e:
            logger.error(f"Error loading timeline: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading timeline: {str(e)}")

    def _get_event_icon(self, event_type) -> str:
        """Get an icon for a timeline event type."""
        icons = {
            "STATUS_CHANGE": "🔄",
            "INTERACTION_ADDED": "💬",
            "CONTACT_ADDED": "👤",
            "APPLICATION_UPDATED": "📝",
            "NOTE_ADDED": "📝",
            "DOCUMENT_ADDED": "📄",
        }
        return icons.get(event_type, "📌")

    def load_interactions(self) -> None:
        """Load interactions associated with this application."""
        try:
            self.interactions_table.setRowCount(0)

            if not self.app_id:
                return

            # Get interactions for this application
            service = InteractionService()
            interactions = service.get_interactions(self.app_id)

            if not interactions:
                self.interactions_table.insertRow(0)
                self.interactions_table.setItem(0, 0, QTableWidgetItem("No interactions found"))
                self.interactions_table.setItem(0, 1, QTableWidgetItem(""))
                self.interactions_table.setItem(0, 2, QTableWidgetItem(""))
                self.interactions_table.setItem(0, 3, QTableWidgetItem(""))
                return

            for i, interaction in enumerate(interactions):
                self.interactions_table.insertRow(i)

                # Format date
                date_str = interaction["date"].split("T")[0] if interaction.get("date") else ""
                time_str = interaction["date"].split("T")[1][:5] if interaction.get("date") else ""
                datetime_str = f"{date_str} {time_str}" if date_str else ""

                # Store the interaction ID for later retrieval
                id_item = QTableWidgetItem(datetime_str)
                id_item.setData(Qt.ItemDataRole.UserRole, interaction.get("id"))
                self.interactions_table.setItem(i, 0, id_item)

                self.interactions_table.setItem(i, 1, QTableWidgetItem(interaction.get("type", "")))

                # Get contact info if available
                contact_info = ""
                if interaction.get("contacts"):
                    contact_info = ", ".join([c["name"] for c in interaction["contacts"]])
                self.interactions_table.setItem(i, 2, QTableWidgetItem(contact_info))

                self.interactions_table.setItem(i, 3, QTableWidgetItem(interaction.get("notes", "")))

        except Exception as e:
            logger.error(f"Error loading interactions: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading interactions: {str(e)}")

    def load_contacts(self) -> None:
        """Load contacts associated with this application."""
        try:
            self.contacts_table.setRowCount(0)

            if not self.app_id:
                return

            # Get contacts associated with this application
            service = ContactService()
            contacts = service.get_contacts_for_application(self.app_id)

            if not contacts:
                self.contacts_table.insertRow(0)
                self.contacts_table.setItem(0, 0, QTableWidgetItem("No contacts found"))
                self.contacts_table.setItem(0, 1, QTableWidgetItem(""))
                self.contacts_table.setItem(0, 2, QTableWidgetItem(""))
                self.contacts_table.setItem(0, 3, QTableWidgetItem(""))
                self.contacts_table.setItem(0, 4, QTableWidgetItem(""))
                return

            for i, contact in enumerate(contacts):
                self.contacts_table.insertRow(i)

                # Store the contact ID for later retrieval
                id_item = QTableWidgetItem(str(contact.get("id", "")))
                id_item.setData(Qt.ItemDataRole.UserRole, contact.get("id"))
                self.contacts_table.setItem(i, 0, id_item)

                self.contacts_table.setItem(i, 1, QTableWidgetItem(contact.get("name", "")))
                self.contacts_table.setItem(i, 2, QTableWidgetItem(contact.get("title", "")))
                self.contacts_table.setItem(i, 3, QTableWidgetItem(contact.get("email", "")))
                self.contacts_table.setItem(i, 4, QTableWidgetItem(contact.get("phone", "")))

        except Exception as e:
            logger.error(f"Error loading contacts: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading contacts: {str(e)}")

    @pyqtSlot()
    def on_edit_application(self) -> None:
        """Open dialog to edit the application."""
        dialog = ApplicationForm(self, self.app_id)
        if dialog.exec():
            self.load_application_data()

    @pyqtSlot()
    def on_change_status(self) -> None:
        """Open dialog to change application status."""
        dialog = StatusTransitionDialog(self, self.app_id, self.application_data["status"])
        if dialog.exec():
            self.load_application_data()

    @pyqtSlot()
    def on_add_interaction(self) -> None:
        """Open dialog to add a new interaction for this application."""
        # Get the selected contact ID if a contact is selected
        selected_rows = self.contacts_table.selectedItems()
        contact_id = None

        if selected_rows:
            contact_id_item = self.contacts_table.item(selected_rows[0].row(), 0)
            if contact_id_item and contact_id_item.text() != "No contacts found":
                contact_id = contact_id_item.data(Qt.ItemDataRole.UserRole)

        # If no contact is selected, we can still create an interaction with the application
        # but we need to select a contact in the form
        dialog = InteractionForm(self, contact_id, self.app_id)
        if dialog.exec():
            self.load_interactions()
            if self.main_window:
                self.main_window.show_status_message("Interaction added successfully")

    @pyqtSlot()
    def on_add_contact(self) -> None:
        """Open dialog to add a contact to this application."""
        dialog = ContactSelectorDialog(self)
        if dialog.exec():
            contact_id = dialog.selected_contact_id

            if not contact_id:
                if self.main_window:
                    self.main_window.show_status_message("No contact selected")
                return

            # Associate the contact with this application
            try:
                service = ContactService()
                result = service.add_contact_to_application(self.app_id, contact_id)

                if result:
                    if self.main_window:
                        self.main_window.show_status_message("Contact added to application")
                    self.load_contacts()
                else:
                    if self.main_window:
                        self.main_window.show_status_message("Failed to add contact to application")
            except Exception as e:
                logger.error(f"Error adding contact to application: {e}", exc_info=True)
                if self.main_window:
                    self.main_window.show_status_message(f"Error: {str(e)}")

    @pyqtSlot()
    def on_remove_contact(self) -> None:
        """Remove the selected contact from this application."""
        selected_rows = self.contacts_table.selectedItems()
        if not selected_rows:
            if self.main_window:
                self.main_window.show_status_message("No contact selected")
            return

        contact_id = self.contacts_table.item(selected_rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        if not contact_id:
            return

        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Remove Contact",
            "Are you sure you want to remove this contact from the application?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                service = ContactService()
                result = service.remove_contact_from_application(self.app_id, contact_id)

                if result:
                    if self.main_window:
                        self.main_window.show_status_message("Contact removed from application")
                    self.load_contacts()
                else:
                    if self.main_window:
                        self.main_window.show_status_message("Failed to remove contact from application")
            except Exception as e:
                logger.error(f"Error removing contact from application: {e}", exc_info=True)
                if self.main_window:
                    self.main_window.show_status_message(f"Error: {str(e)}")

    @pyqtSlot()
    def on_contact_double_clicked(self, index) -> None:
        """Open contact details when double clicked."""
        from src.gui.dialogs.contact_detail import ContactDetailDialog

        if self.contacts_table.item(index.row(), 0).text() == "No contacts found":
            return

        contact_id = self.contacts_table.item(index.row(), 0).data(Qt.ItemDataRole.UserRole)
        dialog = ContactDetailDialog(self, contact_id)
        dialog.exec()

        # Refresh contacts in case there were changes
        self.load_contacts()

    @pyqtSlot()
    def on_edit_interaction(self) -> None:
        """Open dialog to edit the selected interaction."""
        selected_rows = self.interactions_table.selectedItems()
        if not selected_rows:
            if self.main_window:
                self.main_window.show_status_message("No interaction selected")
            return

        interaction_id = self.interactions_table.item(selected_rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        if not interaction_id:
            return

        dialog = InteractionForm(self, None, self.app_id, interaction_id)
        if dialog.exec():
            self.load_interactions()
            if self.main_window:
                self.main_window.show_status_message("Interaction updated successfully")

    @pyqtSlot()
    def on_delete_interaction(self) -> None:
        """Delete the selected interaction."""
        selected_rows = self.interactions_table.selectedItems()
        if not selected_rows:
            if self.main_window:
                self.main_window.show_status_message("No interaction selected")
            return

        interaction_id = self.interactions_table.item(selected_rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        if not interaction_id:
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Interaction",
            "Are you sure you want to delete this interaction?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            service = InteractionService()
            success = service.delete_interaction(interaction_id)

            if success:
                self.load_interactions()
                if self.main_window:
                    self.main_window.show_status_message("Interaction deleted successfully")
            else:
                if self.main_window:
                    self.main_window.show_status_message("Failed to delete interaction")

    @pyqtSlot()
    def on_copy_link(self) -> None:
        """Copy application link to clipboard."""
        from PyQt6.QtWidgets import QApplication

        link = self.application_data.get("link", "")
        if link:
            QApplication.clipboard().setText(link)
            if self.main_window:
                self.main_window.show_status_message("Link copied to clipboard")
        else:
            if self.main_window:
                self.main_window.show_status_message("No link available")

    @pyqtSlot()
    def on_delete_application(self) -> None:
        """Delete this application."""
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete this application?\n\n"
            f"Title: {self.application_data['job_title']}\n"
            f"Company: {self.application_data.get('company', {}).get('name', 'Unknown')}\n\n"
            f"This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                service = ApplicationService()
                success = service.delete(self.app_id)

                if success:
                    if self.main_window:
                        self.main_window.show_status_message(f"Application {self.app_id} deleted")
                    self.accept()
                else:
                    if self.main_window:
                        self.main_window.show_status_message("Failed to delete application")
            except Exception as e:
                logger.error(f"Error deleting application: {e}", exc_info=True)
                if self.main_window:
                    self.main_window.show_status_message(f"Error: {str(e)}")
