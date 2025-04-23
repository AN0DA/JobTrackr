"""Applications management screen for the Job Tracker TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static, Button, DataTable, Select

from src.tui.api_client import APIClient
from src.tui.application_form import ApplicationForm


class ApplicationsList(Static):
    """Applications listing and management screen."""

    def compose(self) -> ComposeResult:
        """Compose the applications screen layout."""
        with Container():
            with Horizontal(id="filters"):
                yield Static("Filter by status:", classes="label")
                yield Select(
                    [(status, status) for status in [
                        "All", "SAVED", "APPLIED", "PHONE_SCREEN", "INTERVIEW",
                        "TECHNICAL_INTERVIEW", "OFFER", "ACCEPTED", "REJECTED", "WITHDRAWN"
                    ]],
                    value="All",
                    id="status-filter"
                )
                yield Button("New Application", variant="primary", id="new-app")

            yield DataTable(id="applications-table")

            with Horizontal(id="actions"):
                yield Button("View", id="view-app", disabled=True)
                yield Button("Edit", id="edit-app", disabled=True)
                yield Button("Delete", id="delete-app", variant="error", disabled=True)

    def on_mount(self) -> None:
        """Set up the screen when mounted."""
        table = self.query_one("#applications-table", DataTable)
        table.add_columns(
            "ID", "Job Title", "Company", "Position", "Location", "Status", "Applied Date"
        )

        self.load_applications()

    async def load_applications(self, status: str = None) -> None:
        """Load applications from the API."""
        self.update_status("Loading applications...")

        try:
            client = APIClient()
            if status == "All" or status is None:
                applications = await client.get_applications()
            else:
                applications = await client.get_applications(status=status)

            table = self.query_one("#applications-table", DataTable)
            table.clear()

            for app in applications:
                table.add_row(
                    app["id"],
                    app["jobTitle"],
                    app.get("company", {}).get("name", ""),
                    app["position"],
                    app.get("location", ""),
                    app["status"],
                    app["appliedDate"]
                )

            self.update_status(f"Loaded {len(applications)} applications")
        except Exception as e:
            self.update_status(f"Error loading applications: {str(e)}")

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle status filter changes."""
        if event.select.id == "status-filter":
            status = event.value if event.value != "All" else None
            self.load_applications(status)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Enable buttons when a row is selected."""
        view_btn = self.query_one("#view-app", Button)
        edit_btn = self.query_one("#edit-app", Button)
        delete_btn = self.query_one("#delete-app", Button)

        view_btn.disabled = False
        edit_btn.disabled = False
        delete_btn.disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        table = self.query_one("#applications-table", DataTable)

        if button_id == "new-app":
            self.app.push_screen(ApplicationForm())

        elif button_id == "view-app" and table.cursor_row is not None:
            app_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(ApplicationForm(app_id=app_id, readonly=True))

        elif button_id == "edit-app" and table.cursor_row is not None:
            app_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(ApplicationForm(app_id=app_id))

        elif button_id == "delete-app" and table.cursor_row is not None:
            app_id = table.get_row_at(table.cursor_row)[0]
            # Show confirmation dialog and delete if confirmed
            # For now just log the action
            self.update_status(f"Would delete application {app_id}")

    def update_status(self, message: str) -> None:
        """Update status message in the footer."""
        self.app.sub_title = message