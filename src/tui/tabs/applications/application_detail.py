"""Application detail view screen with enhanced UI and features."""

from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from textual.app import ComposeResult
from textual.containers import (
    Container,
    Grid,
    Horizontal,
    ScrollableContainer,
    Vertical,
)
from textual.screen import Screen
from textual.widgets import Button, DataTable, Label, MarkdownViewer, Static, TabbedContent, TabPane

from src.config import ApplicationStatus, InteractionType
from src.services.application_service import ApplicationService
from src.services.change_record_service import ChangeRecordService
from src.services.contact_service import ContactService
from src.services.interaction_service import InteractionService
from src.tui.tabs.applications.interaction_form import InteractionForm
from src.tui.widgets.confirmation_modal import ConfirmationModal


class ApplicationDetail(Screen):
    """Detailed view of an application showing all relevant information."""

    def __init__(self, app_id: int, on_updated: Callable | None = None):
        """Initialize the application detail screen.

        Args:
            app_id: The ID of the application to display
            on_updated: Callback function to run when application is updated
        """
        super().__init__()
        self.app_id = app_id
        self.application_data = None
        self.contacts = []
        self.interactions = []
        self.on_updated = on_updated

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        with Container(classes="detail-view"):
            with Horizontal(classes="detail-header"):
                with Vertical(id="app-titles"):
                    yield Static("", id="app-job-title", classes="detail-title")
                    yield Static("", id="app-company", classes="detail-subtitle")
                    yield Static("", id="app-position-location", classes="detail-subtitle")

                with Vertical(id="app-status-section", classes="status-container"):
                    yield Static("STATUS", classes="status-label")
                    yield Static("", id="app-status", classes="status-value")
                    yield Static("", id="app-applied-date", classes="date-value")

            # Quick action button bar
            with Horizontal(classes="quick-actions"):
                yield Button("📝 Edit", id="edit-application", variant="default")
                yield Button("📊 Status", id="change-status", variant="primary")
                yield Button("💬 Add Interaction", id="add-interaction", variant="success")
                yield Button("👤 Add Contact", id="add-contact", variant="warning")

            # Main content with tabs
            with TabbedContent(classes="detail-tabs"):
                with TabPane("Overview", id="tab-overview"):
                    yield from self._compose_overview()

                with TabPane("Timeline", id="tab-timeline"):
                    yield from self._compose_timeline()

                with TabPane("Interactions", id="tab-interactions"):
                    yield from self._compose_interactions()

                with TabPane("Contacts", id="tab-contacts"):
                    yield from self._compose_contacts()

                with TabPane("Job Details", id="tab-job-details"):
                    yield from self._compose_job_details()

            # Footer with actions
            with Horizontal(classes="action-bar"):
                yield Button("⬅️ Back", id="back-button", variant="default")
                yield Button("📋 Copy Link", id="copy-link")
                yield Button("🗑️ Delete", id="delete-application", variant="error")

    def _compose_overview(self) -> ComposeResult:
        """Compose the overview tab layout."""
        with ScrollableContainer(classes="tab-content"):
            # Key application details in a grid
            with Grid(classes="info-grid"):
                yield Label("Applied Date:", classes="field-label")
                yield Static("", id="overview-applied-date", classes="field-value")

                yield Label("Position:", classes="field-label")
                yield Static("", id="overview-position", classes="field-value")
                
                yield Label("Salary:", classes="field-label")
                yield Static("", id="overview-salary", classes="field-value")

                yield Label("Location:", classes="field-label") 
                yield Static("", id="overview-location", classes="field-value")

                yield Label("Link:", classes="field-label")
                yield Static("", id="overview-link", classes="field-value")

                yield Label("Last Updated:", classes="field-label")
                yield Static("", id="overview-updated", classes="field-value")

            # Status history
            yield Label("Status History:", classes="section-label")
            yield DataTable(id="status-history-table", classes="detail-table")

            # Notes section
            yield Label("Notes:", classes="section-label")
            with Container(classes="notes-box"):
                yield Static("", id="notes-content")

            # Upcoming actions
            yield Label("Upcoming Actions:", classes="section-label")
            with Container(id="upcoming-actions"):
                # Will be populated dynamically
                pass

    def _compose_timeline(self) -> ComposeResult:
        """Compose the timeline tab layout."""
        with ScrollableContainer(classes="tab-content"):
            yield DataTable(id="timeline-table", classes="detail-table")

    def _compose_interactions(self) -> ComposeResult:
        """Compose the interactions tab layout."""
        with Vertical(classes="tab-content"):
            with Horizontal(id="interactions-header"):
                yield Label("Application Interactions", classes="tab-subtitle")
                yield Button("+ New Interaction", id="new-interaction", variant="success")

            with ScrollableContainer():
                yield DataTable(id="interactions-table", classes="detail-table")

    def _compose_contacts(self) -> ComposeResult:
        """Compose the contacts tab layout."""
        with Vertical(classes="tab-content"):
            with Horizontal(id="contacts-header"):
                yield Label("Associated Contacts", classes="tab-subtitle")
                yield Button("+ Add Contact", id="new-contact", variant="success")

            with ScrollableContainer():
                yield DataTable(id="contacts-table", classes="detail-table")

    def _compose_job_details(self) -> ComposeResult:
        """Compose the job details tab layout."""
        with ScrollableContainer(classes="tab-content"):
            yield Label("Job Description:", classes="section-label")
            yield MarkdownViewer(id="job-description-md")

    def on_mount(self) -> None:
        """Set up tables and load data."""
        # Set up status history table
        status_history = self.query_one("#status-history-table", DataTable)
        status_history.add_columns("Date", "Status", "Notes")
        status_history.zebra_stripes = True

        # Set up timeline table
        timeline_table = self.query_one("#timeline-table", DataTable)
        timeline_table.add_columns("Date", "Event Type", "Details")
        timeline_table.cursor_type = "row"
        timeline_table.zebra_stripes = True

        # Set up interactions table
        interactions_table = self.query_one("#interactions-table", DataTable)
        interactions_table.add_columns("ID", "Date", "Type", "Details", "Actions")
        interactions_table.cursor_type = "row"
        interactions_table.zebra_stripes = True

        # Set up contacts table
        contacts_table = self.query_one("#contacts-table", DataTable)
        contacts_table.add_columns("ID", "Name", "Title", "Email", "Phone", "Actions")
        contacts_table.cursor_type = "row"
        contacts_table.zebra_stripes = True

        # Load application data
        self.load_application_data()

        # Set overview tab as active by default
        self.query_one(TabbedContent).active = "tab-overview"

    def load_application_data(self) -> None:
        """Load application data and populate the view."""
        try:
            # Load basic application data
            app_service = ApplicationService()
            self.application_data = app_service.get(self.app_id)

            if not self.application_data:
                self.app.sub_title = f"Application {self.app_id} not found"
                return

            # Update header fields
            self.query_one("#app-job-title", Static).renderable = self.application_data["job_title"]

            # Show position and location together for better space usage
            position = self.application_data.get("position", "")
            location = self.application_data.get("location", "")
            if location:
                position_location = f"{position} | {location}"
            else:
                position_location = position
            self.query_one("#app-position-location", Static).renderable = position_location

            # Status with styling
            status = self.application_data["status"]
            status_widget = self.query_one("#app-status", Static)
            status_widget.renderable = status
            status_widget.classes = f"status-value status-{status}"

            # Format and display applied date
            applied_date_str = self.application_data.get("applied_date")
            if applied_date_str:
                try:
                    applied_date = datetime.fromisoformat(applied_date_str)
                    formatted_date = applied_date.strftime("%Y-%m-%d")
                    self.query_one("#app-applied-date", Static).renderable = f"Applied: {formatted_date}"
                    self.query_one("#overview-applied-date", Static).renderable = formatted_date
                except (ValueError, TypeError):
                    self.query_one("#app-applied-date", Static).renderable = "Invalid Date"
                    self.query_one("#overview-applied-date", Static).renderable = "Invalid Date"
            else:
                self.query_one("#app-applied-date", Static).renderable = "No date"
                self.query_one("#overview-applied-date", Static).renderable = "Not specified"

            # Update company info
            company_name = self.application_data.get("company", {}).get("name", "Unknown")
            self.query_one("#app-company", Static).renderable = company_name

            # Update overview fields (previously missing)
            self.query_one("#overview-position", Static).renderable = position or "Not specified"
            self.query_one("#overview-location", Static).renderable = location or "Not specified"
            self.query_one("#overview-salary", Static).renderable = self.application_data.get("salary", "Not specified")

            # Updated date
            updated_date_str = self.application_data.get("updated_at")
            if updated_date_str:
                try:
                    updated_date = datetime.fromisoformat(updated_date_str)
                    formatted_updated = updated_date.strftime("%Y-%m-%d %H:%M")
                    self.query_one("#overview-updated", Static).renderable = formatted_updated
                except (ValueError, TypeError):
                    self.query_one("#overview-updated", Static).renderable = "Unknown"
            else:
                self.query_one("#overview-updated", Static).renderable = "Not available"

            # Update link with proper formatting
            link = self.application_data.get("link", "")
            if link:
                self.query_one("#overview-link", Static).renderable = link
            else:
                self.query_one("#overview-link", Static).renderable = "No link provided"

            # Update job description content with markdown support
            description = self.application_data.get("description", "No description available.")
            markdown_viewer = self.query_one("#job-description-md", MarkdownViewer)
            markdown_viewer.document = description

            # Update notes content
            notes_content = self.application_data.get("notes", "No notes available.")
            self.query_one("#notes-content", Static).renderable = notes_content

            # Load all data for tabs
            self.load_timeline()
            self.load_interactions()
            self.load_contacts()
            self.load_status_history()
            self.generate_upcoming_actions()

            self.app.sub_title = f"Application details: {self.application_data['job_title']} at {company_name}"

        except Exception as e:
            self.app.sub_title = f"Error loading application details: {str(e)}"

    def load_status_history(self) -> None:
        """Load status history from change records."""
        try:
            change_service = ChangeRecordService()
            changes = change_service.get_change_records(self.app_id)

            # Filter only status changes
            status_changes = [change for change in changes if change["change_type"] == "STATUS_CHANGE"]

            # Update status history table
            status_table = self.query_one("#status-history-table", DataTable)
            status_table.clear()

            if not status_changes:
                # If no status changes, add the current status as the initial one
                applied_date_str = self.application_data.get("applied_date", "")
                date_display = applied_date_str[:10] if applied_date_str else "Unknown"
                
                status_table.add_row(
                    date_display,
                    self.application_data.get("status", "APPLIED"),
                    "Initial application status"
                )
                return

            # Sort by timestamp descending
            for change in sorted(status_changes, key=lambda x: x["timestamp"], reverse=True):
                status_table.add_row(
                    change["timestamp"][:10],  # Just the date portion
                    change["new_value"],
                    change.get("notes", "")
                )

        except Exception as e:
            self.app.sub_title = f"Error loading status history: {str(e)}"
            status_table = self.query_one("#status-history-table", DataTable)
            status_table.clear()
            status_table.add_row("Error", f"Could not load status history: {str(e)}", "")

    def generate_upcoming_actions(self) -> None:
        """Generate and display upcoming recommended actions."""
        try:
            upcoming_actions = self.query_one("#upcoming-actions", Container)
            upcoming_actions.remove_children()

            status = self.application_data.get("status", "")
            applied_date_str = self.application_data.get("applied_date")

            if not applied_date_str:
                upcoming_actions.mount(Static("No date information available"))
                return

            applied_date = datetime.fromisoformat(applied_date_str)
            today = datetime.now()
            days_since_applied = (today - applied_date).days

            actions = []

            # Status-based actions
            if status == "APPLIED" and days_since_applied > 7:
                actions.append(("Follow up on application", "high"))
            elif status == "PHONE_SCREEN":
                actions.append(("Prepare for phone screen", "medium"))
            elif status == "INTERVIEW" or status == "TECHNICAL_INTERVIEW":
                actions.append(("Prepare for interview", "high"))
                actions.append(("Research the company", "medium"))
            elif status == "OFFER":
                actions.append(("Review offer details", "high"))
                actions.append(("Prepare negotiation points", "high"))

            # Generic actions based on time
            if days_since_applied > 14 and status in ["APPLIED", "PHONE_SCREEN"]:
                actions.append(("Check application status", "medium"))
                
            # Follow-up actions based on interactions
            last_interaction = None
            for interaction in self.interactions:
                interaction_date = datetime.fromisoformat(interaction["date"])
                if not last_interaction or interaction_date > datetime.fromisoformat(last_interaction["date"]):
                    last_interaction = interaction
                    
            if last_interaction:
                last_date = datetime.fromisoformat(last_interaction["date"])
                days_since_interaction = (today - last_date).days
                if days_since_interaction > 7 and status in ["INTERVIEW", "TECHNICAL_INTERVIEW", "PHONE_SCREEN"]:
                    actions.append((f"Follow up on {last_interaction['type'].lower()}", "high"))

            # Add actions to container
            if not actions:
                upcoming_actions.mount(Static("No pending actions"))
                return

            for action, priority in actions:
                action_container = Horizontal(classes=f"action-item priority-{priority}")
                action_container.mount(Static(f"• {action}", classes="action-text"))
                upcoming_actions.mount(action_container)

        except Exception as e:
            self.app.sub_title = f"Error generating actions: {str(e)}"
            upcoming_actions = self.query_one("#upcoming-actions", Container)
            upcoming_actions.remove_children()
            upcoming_actions.mount(Static(f"Error: {str(e)}"))

    def load_timeline(self) -> None:
        """Load and display timeline events."""
        try:
            # Get change records
            change_service = ChangeRecordService()
            changes = change_service.get_change_records(self.app_id)

            # Get interactions for the timeline
            interaction_service = InteractionService()
            self.interactions = interaction_service.get_interactions(self.app_id)

            # Combine all events into a timeline
            timeline_events = []

            # Add change records
            for change in changes:
                timeline_events.append(
                    {
                        "date": datetime.fromisoformat(change["timestamp"]),
                        "type": change["change_type"],
                        "details": change["notes"] or self._format_change(change),
                        "icon": self._get_event_icon(change["change_type"])
                    }
                )

            # Add interactions
            for interaction in self.interactions:
                timeline_events.append(
                    {
                        "date": datetime.fromisoformat(interaction["date"]),
                        "type": "INTERACTION",
                        "details": f"{interaction['type']}: {interaction['notes'][:50] + '...' if interaction['notes'] and len(interaction['notes']) > 50 else interaction['notes'] or ''}",
                        "icon": "💬"
                    }
                )

            # Add application creation as first event
            creation_date_str = self.application_data.get("created_at", "")
            if creation_date_str:
                creation_date = datetime.fromisoformat(creation_date_str)
                timeline_events.append({
                    "date": creation_date,
                    "type": "APPLICATION_CREATED",
                    "details": f"Application created for {self.application_data['job_title']}",
                    "icon": "📝"
                })

            # Sort by date descending
            timeline_events.sort(key=lambda x: x["date"], reverse=True)

            # Update timeline table
            timeline_table = self.query_one("#timeline-table", DataTable)
            timeline_table.clear()

            if not timeline_events:
                timeline_table.add_row("No events", "", "")
                return

            for event in timeline_events:
                timeline_table.add_row(
                    event["date"].strftime("%Y-%m-%d %H:%M"),
                    f"{event['icon']} {event['type'].replace('_', ' ')}",
                    event["details"],
                )

        except Exception as e:
            self.app.sub_title = f"Error loading timeline: {str(e)}"
            timeline_table = self.query_one("#timeline-table", DataTable)
            timeline_table.clear()
            timeline_table.add_row("Error", f"Could not load timeline: {str(e)}", "")

    def _get_event_icon(self, event_type: str) -> str:
        """Get an icon for a timeline event type."""
        icons = {
            "STATUS_CHANGE": "🔄",
            "INTERACTION_ADDED": "💬",
            "CONTACT_ADDED": "👤",
            "APPLICATION_UPDATED": "📝",
            "NOTE_ADDED": "📝",
            "DOCUMENT_ADDED": "📄"
        }
        return icons.get(event_type, "📌")

    def load_interactions(self) -> None:
        """Load and display interactions."""
        try:
            interaction_service = InteractionService()
            self.interactions = interaction_service.get_interactions(self.app_id)

            interactions_table = self.query_one("#interactions-table", DataTable)
            interactions_table.clear()

            if not self.interactions:
                interactions_table.add_row("", "No interactions recorded", "", "", "")
                return

            for interaction in self.interactions:
                # Format contacts if available
                contacts_str = ""
                if interaction.get("contacts"):
                    contacts_str = ", ".join([c["name"] for c in interaction["contacts"]])

                # Format date for better readability
                date_str = datetime.fromisoformat(interaction["date"]).strftime("%Y-%m-%d")
                
                # Truncate notes if too long
                notes = interaction["notes"] or ""
                if len(notes) > 50:
                    notes = notes[:47] + "..."

                interactions_table.add_row(
                    str(interaction["id"]),  # Store ID for editing/deleting
                    date_str,
                    interaction["type"],
                    notes,
                    "✏️ Edit | 🗑️ Delete",  # Actions
                )

        except Exception as e:
            self.app.sub_title = f"Error loading interactions: {str(e)}"
            interactions_table = self.query_one("#interactions-table", DataTable)
            interactions_table.clear()
            interactions_table.add_row("", f"Error: {str(e)}", "", "", "")

    def load_contacts(self) -> None:
        """Load and display associated contacts."""
        try:
            contact_service = ContactService()
            
            # In a real implementation, we would have a method to get contacts for an application
            # For now, we'll try to get contacts from the company as a proxy
            contacts_table = self.query_one("#contacts-table", DataTable)
            contacts_table.clear()
            
            # Get contacts from company
            company_id = None
            if self.application_data and self.application_data.get("company"):
                company_id = self.application_data["company"].get("id")
                
            if company_id:
                self.contacts = contact_service.get_contacts(company_id=company_id)
                
                if self.contacts:
                    for contact in self.contacts:
                        contacts_table.add_row(
                            str(contact["id"]),
                            contact["name"],
                            contact.get("title", ""),
                            contact.get("email", ""),
                            contact.get("phone", ""),
                            "✏️ Edit | 🗑️ Delete"  # Actions
                        )
                    return
            
            # If no contacts found or could not retrieve them
            contacts_table.add_row(
                "",
                "No contacts associated",
                "",
                "",
                "",
                ""
            )

        except Exception as e:
            self.app.sub_title = f"Error loading contacts: {str(e)}"
            contacts_table = self.query_one("#contacts-table", DataTable)
            contacts_table.clear()
            contacts_table.add_row(
                "",
                f"Error: {str(e)}",
                "",
                "",
                "",
                ""
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        # Navigation buttons
        if button_id == "back-button":
            self.app.pop_screen()
            # Call the on_updated callback if provided
            if self.on_updated:
                self.on_updated()

        # Action buttons
        elif button_id == "edit-application":
            from src.tui.tabs.applications.application_form import ApplicationForm
            self.app.push_screen(ApplicationForm(app_id=self.app_id, on_saved=self.load_application_data))

        elif button_id == "change-status":
            from src.tui.tabs.applications.status_transition import StatusTransitionDialog
            self.app.push_screen(
                StatusTransitionDialog(
                    self.app_id, self.application_data["status"], on_updated=self.load_application_data
                )
            )

        elif button_id in ["add-interaction", "new-interaction"]:
            self.app.push_screen(InteractionForm(application_id=self.app_id, on_saved=self.load_application_data))

        elif button_id in ["add-contact", "new-contact"]:
            self._show_contact_selection()

        elif button_id == "copy-link":
            self._copy_application_link()

        elif button_id == "delete-application":
            self._confirm_delete_application()

    def _copy_application_link(self) -> None:
        """Copy the application link to clipboard (or show appropriate message)."""
        link = self.application_data.get("link", "")
        if link:
            # In a TUI environment, direct clipboard access isn't possible
            # Instead, show the link for manual copying
            self.app.sub_title = f"Link to copy: {link}"
        else:
            self.app.sub_title = "No link available for this application"

    def _show_contact_selection(self) -> None:
        """Show dialog to select a contact to associate with this application."""
        # This would be implemented to open a contact selector
        # For now, we'll just show a more detailed message
        
        if not self.application_data.get("company", {}).get("id"):
            self.app.sub_title = "This application must be associated with a company first"
            return
            
        # In a complete implementation, we would:
        # 1. Show a dialog with existing contacts from the company
        # 2. Allow selection or creation of a new contact
        # 3. Associate the selected contact with this application
        
        self.app.sub_title = "Contact selection feature will be implemented in a future update"
        
    def _confirm_delete_application(self) -> None:
        """Confirm and delete the application."""
        def delete_confirmed():
            try:
                service = ApplicationService()
                success = service.delete(self.app_id)
                if success:
                    self.app.sub_title = f"Application {self.app_id} deleted"
                    self.app.pop_screen()
                    if self.on_updated:
                        self.on_updated()
                else:
                    self.app.sub_title = "Failed to delete application"
            except Exception as e:
                self.app.sub_title = f"Error deleting application: {str(e)}"

        job_title = self.application_data.get("job_title", "Unknown")
        company_name = self.application_data.get("company", {}).get("name", "Unknown")
        
        self.app.push_screen(
            ConfirmationModal(
                title="Confirm Deletion",
                message=(
                    f"Are you sure you want to delete this application?\n\n"
                    f"Title: {job_title}\n"
                    f"Company: {company_name}\n\n"
                    "This action cannot be undone."
                ),
                confirm_text="Delete",
                cancel_text="Cancel",
                on_confirm=delete_confirmed,
                dangerous=True
            )
        )

    def _edit_interaction(self, interaction_id: int) -> None:
        """Edit an interaction."""
        self.app.push_screen(
            InteractionForm(
                interaction_id=interaction_id,
                application_id=self.app_id,
                on_saved=self.load_application_data
            )
        )

    def _delete_interaction(self, interaction_id: int) -> None:
        """Delete an interaction with confirmation."""
        def confirm_delete():
            try:
                service = InteractionService()
                success = service.delete(interaction_id)
                if success:
                    self.app.sub_title = "Interaction deleted successfully"
                    self.load_application_data()  # Refresh all data
                else:
                    self.app.sub_title = "Failed to delete interaction"
            except Exception as e:
                self.app.sub_title = f"Error deleting interaction: {str(e)}"

        # Find interaction details for confirmation message
        interaction_details = "this interaction"
        for interaction in self.interactions:
            if interaction["id"] == interaction_id:
                interaction_details = f"{interaction['type']} on {interaction['date'][:10]}"
                break
                
        self.app.push_screen(
            ConfirmationModal(
                title="Confirm Deletion",
                message=f"Are you sure you want to delete {interaction_details}?",
                confirm_text="Delete",
                cancel_text="Cancel",
                on_confirm=confirm_delete,
                dangerous=True
            )
        )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in data tables."""
        table_id = event.data_table.id
        row = event.data_table.get_row(event.row_key)

        if table_id == "interactions-table":
            # Skip if this is the "No interactions" placeholder row
            if not row[0] or row[1] == "No interactions recorded" or row[1].startswith("Error:"):
                return
                
            # Get the column with actions (last column)
            actions_col = len(row) - 1
            
            # Show a menu of actions
            def handle_edit():
                self._edit_interaction(int(row[0]))
                
            def handle_delete():
                self._delete_interaction(int(row[0]))
                
            self.app.push_screen(
                ConfirmationModal(
                    title=f"Interaction: {row[2]}",
                    message=f"Date: {row[1]}\nDetails: {row[3]}",
                    confirm_text="Edit",
                    cancel_text="Delete",
                    on_confirm=handle_edit,
                    on_cancel=handle_delete
                )
            )
                
        elif table_id == "contacts-table":
            # Skip placeholder rows
            if not row[0] or row[1] == "No contacts associated" or row[1].startswith("Error:"):
                return
                
            # In a complete implementation, we could:
            # 1. Show contact details
            # 2. Provide options to edit/remove the contact association
            
            self.app.sub_title = f"Selected contact: {row[1]}"
            
        elif table_id == "timeline-table":
            # Nothing to do for timeline events currently
            pass

    def _format_change(self, change: dict[str, Any]) -> str:
        """Format change record details for display."""
        if change["change_type"] == "STATUS_CHANGE":
            return f"Status changed from {change.get('old_value', 'unknown')} to {change.get('new_value', 'unknown')}"
        elif change["change_type"] == "APPLICATION_UPDATED":
            return "Application details were updated"
        elif change["change_type"] == "CONTACT_ADDED": 
            return f"Contact {change.get('new_value', '')} was added"
        elif change["change_type"] == "INTERACTION_ADDED":
            return f"Added {change.get('new_value', '')} interaction"
        else:
            if change.get("old_value") and change.get("new_value"):
                return f"Changed from {change['old_value']} to {change['new_value']}"
            elif change.get("new_value"):
                return f"Set to {change['new_value']}"
            else:
                return "Change recorded"
