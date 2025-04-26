from typing import Dict, Any

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import (
    Container,
    Horizontal,
    Vertical,
)
from textual.widgets import Static, Button, DataTable, TabPane, TabbedContent
from datetime import datetime

from src.services.application_service import ApplicationService
from src.services.change_record_service import ChangeRecordService
from src.services.interaction_service import InteractionService
from src.tui.tabs.applications.interaction_form import InteractionForm


class ApplicationDetail(Screen):
    """Detailed view of an application showing history and interactions."""

    def __init__(self, app_id: int):
        """Initialize the application detail screen."""
        super().__init__()
        self.app_id = app_id
        self.application_data = None

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        with Container(id="app-detail"):
            # Header with key info and status
            with Horizontal(id="app-header"):
                with Vertical(id="app-titles"):
                    yield Static("", id="app-job-title", classes="app-title")
                    yield Static("", id="app-company", classes="app-subtitle")
                    yield Static("", id="app-position", classes="app-subtitle")

                with Vertical(id="app-status-section", classes="status-container"):
                    yield Static("STATUS", classes="status-label")
                    yield Static("", id="app-status", classes="status-value")

            # Main content with tabs
            with TabbedContent(id="app-tabs"):
                with TabPane("Overview", id="tab-overview"):
                    # Use yield from to yield widgets from the generator
                    yield from self._compose_overview()

                with TabPane("Timeline", id="tab-timeline"):
                    # Use yield from
                    yield from self._compose_timeline()

                with TabPane("Interactions", id="tab-interactions"):
                    # Use yield from
                    yield from self._compose_interactions()

                with TabPane("Contacts", id="tab-contacts"):
                    # Use yield from
                    yield from self._compose_contacts()

            # Footer with actions
            with Horizontal(id="app-actions", classes="action-bar"):
                yield Button("Back", id="back-button", variant="default")
                yield Button("Edit", id="edit-application")
                yield Button("Change Status", id="change-status", variant="primary")
                yield Button("Add Interaction", id="add-interaction")

    def _compose_overview(self) -> ComposeResult:
        """Compose the overview tab layout."""
        with Vertical(id="overview-content"):
            yield Static("Applied Date:", classes="label")
            yield Static("", id="app-applied-date")
            yield Static("Notes:", classes="label")
            # Use a container for notes to allow scrolling if needed
            with Container(id="notes-container"):
                yield Static("", id="notes-content")

    def _compose_timeline(self) -> ComposeResult:
        """Compose the timeline tab layout."""
        yield DataTable(id="timeline-table")

    def _compose_interactions(self) -> ComposeResult:
        """Compose the interactions tab layout."""
        yield DataTable(id="interactions-table")

    def _compose_contacts(self) -> ComposeResult:
        """Compose the contacts tab layout."""
        yield DataTable(id="contacts-table")

    def on_mount(self) -> None:
        """Set up tables and load data."""
        # Set up timeline table
        timeline_table = self.query_one("#timeline-table", DataTable)
        timeline_table.add_columns("Date", "Event Type", "Details")
        timeline_table.cursor_type = "row"

        # Set up interactions table
        interactions_table = self.query_one("#interactions-table", DataTable)
        interactions_table.add_columns("Date", "Type", "Details", "Actions")
        interactions_table.cursor_type = "row"

        # Set up contacts table
        contacts_table = self.query_one("#contacts-table", DataTable)
        contacts_table.add_columns("Name", "Title", "Email", "Phone")
        contacts_table.cursor_type = "row"

        # Load application data
        self.load_application_data()

        # Set timeline tab as active by default
        self.query_one(TabbedContent).active = "tab-timeline"

    def load_application_data(self) -> None:
        """Load application data and populate the view."""
        try:
            # Load basic application data
            app_service = ApplicationService()
            self.application_data = app_service.get_application(self.app_id)

            if not self.application_data:
                self.app.sub_title = f"Application {self.app_id} not found"
                return

            # Update header fields
            self.query_one("#app-job-title", Static).renderable = self.application_data[
                "job_title"
            ]
            self.query_one(
                "#app-position", Static
            ).renderable = self.application_data.get("position", "N/A")
            self.query_one("#app-status", Static).renderable = self.application_data[
                "status"
            ]
            applied_date_str = self.application_data.get("applied_date")
            if applied_date_str:
                try:
                    applied_date = datetime.fromisoformat(applied_date_str)
                    self.query_one(
                        "#app-applied-date", Static
                    ).renderable = applied_date.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    self.query_one(
                        "#app-applied-date", Static
                    ).renderable = "Invalid Date"
            else:
                self.query_one("#app-applied-date", Static).renderable = "N/A"

            # Update company info
            company_name = self.application_data.get("company", {}).get(
                "name", "Unknown"
            )
            self.query_one("#app-company", Static).renderable = company_name

            # Update notes content
            notes_content = self.application_data.get("notes", "No notes available.")
            self.query_one("#notes-content", Static).renderable = notes_content

            # Load timeline data
            self.load_timeline()

            # Load other tab data
            self.load_interactions()
            self.load_contacts()

            self.app.sub_title = (
                f"Loaded details for {self.application_data['job_title']}"
            )

        except Exception as e:
            self.app.sub_title = f"Error loading application details: {str(e)}"

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
                timeline_events.append(
                    {
                        "date": datetime.fromisoformat(change["timestamp"]),
                        "type": change["change_type"],
                        "details": change["notes"] or self._format_change(change),
                    }
                )

            # Add interactions
            for interaction in interactions:
                timeline_events.append(
                    {
                        "date": datetime.fromisoformat(interaction["date"]),
                        "type": "INTERACTION",
                        "details": f"{interaction['type']}: {interaction['notes'][:50] + '...' if interaction['notes'] and len(interaction['notes']) > 50 else interaction['notes'] or ''}",
                    }
                )

            # Sort by date descending
            timeline_events.sort(key=lambda x: x["date"], reverse=True)

            # Update timeline table
            timeline_table = self.query_one("#timeline-table", DataTable)
            timeline_table.clear()

            for event in timeline_events:
                timeline_table.add_row(
                    event["date"].strftime("%Y-%m-%d %H:%M"),
                    event["type"].replace("_", " "),
                    event["details"],
                )

        except Exception as e:
            self.app.sub_title = f"Error loading timeline: {str(e)}"

    def load_interactions(self) -> None:
        """Load and display interactions."""
        try:
            interaction_service = InteractionService()
            interactions = interaction_service.get_interactions(self.app_id)

            interactions_table = self.query_one("#interactions-table", DataTable)
            interactions_table.clear()

            for interaction in interactions:
                interactions_table.add_row(
                    datetime.fromisoformat(interaction["date"]).strftime("%Y-%m-%d"),
                    interaction["type"],
                    interaction["notes"] or "",
                    "Edit | Delete",  # Actions
                )

        except Exception as e:
            self.app.sub_title = f"Error loading interactions: {str(e)}"

    def load_contacts(self) -> None:
        """Load and display contacts."""
        # In a real implementation, we would fetch contacts associated with this application
        contacts_table = self.query_one("#contacts-table", DataTable)
        contacts_table.clear()

        # Just a placeholder for now
        contacts_table.add_row(
            "No contacts associated with this application", "", "", ""
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        # Action buttons
        if button_id == "back-button":
            self.app.pop_screen()

        elif button_id == "edit-application":
            from src.tui.tabs.applications.application_form import ApplicationForm

            self.app.push_screen(ApplicationForm(app_id=self.app_id))

        elif button_id == "change-status":
            from src.tui.tabs.applications.status_transition import (
                StatusTransitionDialog,
            )

            self.app.push_screen(
                StatusTransitionDialog(self.app_id, self.application_data["status"])
            )

        elif button_id == "add-interaction":
            self.app.push_screen(InteractionForm(application_id=self.app_id))

    def _format_change(self, change: Dict[str, Any]) -> str:
        """Format change record details for display."""
        if change["change_type"] == "STATUS_CHANGE":
            return f"Status changed from {change['old_value']} to {change['new_value']}"
        elif change["change_type"] == "APPLICATION_UPDATED":
            return "Application details were updated"
        else:
            if change["old_value"] and change["new_value"]:
                return f"Changed from {change['old_value']} to {change['new_value']}"
            elif change["new_value"]:
                return f"Set to {change['new_value']}"
            else:
                return "Change recorded"
