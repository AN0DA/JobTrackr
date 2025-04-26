"""Applications management screen for the Job Tracker TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Static, Button, DataTable, Select
from textual.screen import ModalScreen
from textual.widgets import Label

from src.services.application_service import ApplicationService
from src.tui.tabs.applications.application_form import ApplicationForm


class ApplicationsList(Static):
    """Applications listing and management screen."""

    BINDINGS = [
        ("a", "add_application", "Add Application"),
        ("d", "delete_application", "Delete"),
        ("e", "edit_application", "Edit"),
        ("v", "view_application", "View"),
        ("s", "change_status", "Change Status"),
        ("r", "refresh_applications", "Refresh"),
    ]

    def __init__(self):
        super().__init__()
        self.sort_column = "Applied Date"
        self.sort_ascending = False  # Default to newest first

    def compose(self) -> ComposeResult:
        """Compose the applications screen layout."""
        with Container():
            with Horizontal(id="filters"):
                yield Static("Filter by status:", classes="label")
                yield Select(
                    [
                        (status, status)
                        for status in [
                            "All",
                            "SAVED",
                            "APPLIED",
                            "PHONE_SCREEN",
                            "INTERVIEW",
                            "TECHNICAL_INTERVIEW",
                            "OFFER",
                            "ACCEPTED",
                            "REJECTED",
                            "WITHDRAWN",
                        ]
                    ],
                    value="All",
                    id="status-filter",
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
            "ID",
            "Job Title",
            "Company",
            "Position",
            "Location",
            "Status",
            "Applied Date",
        )
        table.cursor_type = "row"
        table.can_focus = True

        # Enable sorting
        table.sort_column_click = True

        self.load_applications()

    def load_applications(self, status: str = None) -> None:
        """Load applications from the database."""
        self.update_status("Loading applications...")

        try:
            service = ApplicationService()
            if status == "All" or status is None:
                applications = service.get_applications(limit=50)
            else:
                applications = service.get_applications(status=status, limit=50)

            table = self.query_one("#applications-table", DataTable)
            table.clear()

            # Convert to list for sorting
            apps_list = list(applications)

            # Apply current sort settings
            self._sort_applications(apps_list)

            for app in apps_list:
                table.add_row(
                    str(app["id"]),
                    app["job_title"],
                    app.get("company", {}).get("name", ""),
                    app["position"],
                    app.get("location", ""),
                    app["status"],
                    app["applied_date"],
                )

            self.update_status(f"Loaded {len(applications)} applications")
        except Exception as e:
            self.update_status(f"Error loading applications: {str(e)}")

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle status filter changes."""
        if event.select.id == "status-filter":
            status = event.value if event.value != "All" else None
            self.load_applications(status)

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
            self.app.push_screen(DeleteConfirmationModal(app_id))

    def update_status(self, message: str) -> None:
        """Update status message in the footer."""
        self.app.sub_title = message

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Enable buttons when a row is highlighted."""
        view_btn = self.query_one("#view-app", Button)
        edit_btn = self.query_one("#edit-app", Button)
        delete_btn = self.query_one("#delete-app", Button)

        view_btn.disabled = False
        edit_btn.disabled = False
        delete_btn.disabled = False

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Open the application detail view when a row is selected."""
        table = self.query_one("#applications-table", DataTable)
        # Use get_row with the RowKey provided by the event
        app_id = table.get_row(event.row_key)[0]

        # Open application detail view
        from src.tui.tabs.applications.application_detail import ApplicationDetail

        self.app.push_screen(ApplicationDetail(int(app_id)))

    def _sort_applications(self, applications):
        """Sort applications based on current sort settings."""
        # Define sort keys for each column
        sort_keys = {
            "ID": lambda app: int(app["id"]),
            "Job Title": lambda app: app["job_title"].lower(),
            "Company": lambda app: app.get("company", {}).get("name", "").lower(),
            "Position": lambda app: app["position"].lower(),
            "Location": lambda app: (app.get("location") or "").lower(),
            "Status": lambda app: app["status"],
            "Applied Date": lambda app: app["applied_date"],
        }

        # Get sort key function
        sort_key = sort_keys.get(self.sort_column, lambda app: app["applied_date"])

        # Sort applications
        applications.sort(key=sort_key, reverse=not self.sort_ascending)

    # Maintain all the original action methods
    def action_add_application(self) -> None:
        """Open the application creation form."""
        from src.tui.tabs.applications.application_form import ApplicationForm

        self.app.push_screen(ApplicationForm())

    def action_delete_application(self) -> None:
        """Delete the selected application."""
        table = self.query_one("#applications-table", DataTable)
        if table.cursor_row is not None:
            app_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(DeleteConfirmationModal(app_id))

    def action_edit_application(self) -> None:
        """Edit the selected application."""
        table = self.query_one("#applications-table", DataTable)
        if table.cursor_row is not None:
            app_id = table.get_row_at(table.cursor_row)[0]
            from src.tui.tabs.applications.application_form import ApplicationForm

            self.app.push_screen(ApplicationForm(app_id=app_id))

    def action_view_application(self) -> None:
        """View the selected application."""
        table = self.query_one("#applications-table", DataTable)
        if table.cursor_row is not None:
            app_id = table.get_row_at(table.cursor_row)[0]
            from src.tui.tabs.applications.application_form import ApplicationForm

            self.app.push_screen(ApplicationForm(app_id=app_id, readonly=True))

    def action_change_status(self) -> None:
        """Change the status of the selected application."""
        table = self.query_one("#applications-table", DataTable)
        if table.cursor_row is not None:
            app_id = table.get_row_at(table.cursor_row)[0]
            status = table.get_row_at(table.cursor_row)[5]
            from src.tui.tabs.applications.status_transition import (
                StatusTransitionDialog,
            )

            self.app.push_screen(StatusTransitionDialog(app_id, status))

    def action_refresh_applications(self) -> None:
        """Refresh the applications list."""
        self.load_applications()


class DeleteConfirmationModal(ModalScreen):
    """Confirmation dialog for deleting applications."""

    def __init__(self, app_id: str):
        super().__init__()
        self.app_id = app_id

    def compose(self) -> ComposeResult:
        yield Container(
            Label(f"Are you sure you want to delete application #{self.app_id}?"),
            Horizontal(
                Button("Cancel", variant="primary", id="cancel"),
                Button("Delete", variant="error", id="confirm"),
                id="buttons",
            ),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
        elif event.button.id == "confirm":
            self.delete_application()

    def delete_application(self) -> None:
        try:
            service = ApplicationService()
            success = service.delete_application(int(self.app_id))

            if success:
                self.app.sub_title = f"Successfully deleted application #{self.app_id}"
            else:
                self.app.sub_title = f"Application #{self.app_id} not found"

            self.app.pop_screen()

            # Refresh the applications list if it's visible
            app_list = self.app.query_one(ApplicationsList)
            if app_list:
                app_list.load_applications()

        except Exception as e:
            self.app.sub_title = f"Error deleting application: {str(e)}"
            self.app.pop_screen()
