from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Select, Static

from src.config import ApplicationStatus
from src.services.application_service import ApplicationService
from src.tui.tabs.applications.application_form import ApplicationForm
from src.tui.widgets.confirmation_modal import ConfirmationModal
from src.tui.widgets.list_view import ListView


class ApplicationsList(ListView):
    """Applications listing and management screen."""

    BINDINGS = [
        ("a", "add_application", "Add Application"),
        ("d", "delete_application", "Delete"),
        ("e", "edit_application", "Edit"),
        ("v", "view_application", "View"),
        ("s", "change_status", "Change Status"),
    ]

    def __init__(self) -> None:
        """Initialize the applications listing."""
        columns = ["ID", "Job Title", "Company", "Position", "Status", "Applied Date"]
        super().__init__(
            service=ApplicationService(),
            columns=columns,
            title="Applications",
        )
        self.current_status = None

    def compose(self) -> ComposeResult:
        """Compose the applications screen layout."""
        with Container(classes="list-view-container"):
            # Header section
            with Container(classes="list-header"):
                # Filter bar
                with Horizontal(classes="filter-bar"):
                    with Vertical(classes="filter-section"):
                        yield Static("Status:", classes="filter-label")
                        yield Select(
                            self._get_status_options(),
                            value="All",
                            id="status-filter",
                            classes="filter-dropdown",
                        )

                    # Search section
                    with Horizontal(classes="search-section"):
                        yield Input(placeholder="Search applications...", id="app-search")
                        yield Button("🔍", id="search-button")

                    # Quick action buttons
                    with Horizontal(classes="action-section"):
                        yield Button("New Application", variant="primary", id="new-app")

            # Table section
            with Container(classes="table-container"):
                yield DataTable(id="applications-table")

            # Footer section
            with Horizontal(classes="list-footer"):
                with Horizontal(classes="action-buttons"):
                    yield Button("View", id="view-app", disabled=True)
                    yield Button("Edit", id="edit-app", disabled=True)
                    yield Button("Delete", id="delete-app", variant="error", disabled=True)

    def _get_status_options(self):
        """Get options for the status filter dropdown."""
        options = [(status.value, status.value) for status in ApplicationStatus]
        options.insert(0, ("All", "All"))
        return options

    def on_mount(self) -> None:
        """Set up the screen when mounted."""
        table = self.query_one("#applications-table", DataTable)
        table.add_columns(
            "ID",
            "Job Title",
            "Company",
            "Position",
            "Status",
            "Applied Date",
        )
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.can_focus = True

        # Enable sorting
        table.sort_column_click = True

        self.load_applications()

    def load_applications(self, status: str = None) -> None:
        """Load applications from the database with improved styling."""
        self.update_status("Loading applications...")
        self.current_status = status

        try:
            service = ApplicationService()

            # Get applications with proper filtering
            if status == "All" or status is None:
                applications = service.get_applications(
                    sort_by=self.sort_column.lower().replace(" ", "_"),
                    sort_desc=not self.sort_ascending,
                    limit=50,
                )
            else:
                applications = service.get_applications(
                    status=status,
                    sort_by=self.sort_column.lower().replace(" ", "_"),
                    sort_desc=not self.sort_ascending,
                    limit=50,
                )

            # Get reference to the data table
            table = self.query_one("#applications-table", DataTable)
            table.clear()

            # Convert to list for sorting
            apps_list = list(applications)

            # Check if we have any applications
            if not apps_list:
                # Handle empty state
                table.add_column_span = len(table.columns)
                self.update_status("No applications found")

                # Make sure action buttons are disabled
                view_btn = self.query_one("#view-app", Button)
                edit_btn = self.query_one("#edit-app", Button)
                delete_btn = self.query_one("#delete-app", Button)
                view_btn.disabled = True
                edit_btn.disabled = True
                delete_btn.disabled = True

                return

            # Add rows with styled status values
            for app in apps_list:
                # Format applied date for better readability
                try:
                    applied_date = datetime.fromisoformat(app["applied_date"])
                    formatted_date = applied_date.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    formatted_date = app["applied_date"]

                # Add the row with all values
                table.add_row(
                    str(app["id"]),
                    app["job_title"],
                    app.get("company", {}).get("name", ""),
                    app["position"],
                    app["status"],
                    formatted_date,
                )

            # Update status message with count
            count = len(apps_list)
            status_message = f"Loaded {count} application{'s' if count != 1 else ''}"
            self.update_status(status_message)

        except Exception as e:
            error_message = f"Error loading applications: {str(e)}"
            self.update_status(error_message)
            # Log the error for debugging
            import logging

            logging.error(error_message, exc_info=True)

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
            self.app.push_screen(ApplicationForm(on_saved=self.load_applications))

        elif button_id == "view-app" and table.cursor_row is not None:
            app_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(ApplicationForm(app_id=app_id, readonly=True))

        elif button_id == "edit-app" and table.cursor_row is not None:
            app_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(ApplicationForm(app_id=app_id, on_saved=self.load_applications))

        elif button_id == "delete-app" and table.cursor_row is not None:
            app_id = table.get_row_at(table.cursor_row)[0]
            self._confirm_delete_application(app_id)

        elif button_id == "search-button":
            search_term = self.query_one("#app-search", Input).value
            self.search_applications(search_term)

    def search_applications(self, search_term: str) -> None:
        """Search applications by keyword."""
        if not search_term:
            self.load_applications(self.current_status)
            return

        self.update_status(f"Searching for '{search_term}'...")

        try:
            service = ApplicationService()
            applications = service.search_applications(search_term)

            # Apply status filter if active
            if self.current_status:
                applications = [app for app in applications if app["status"] == self.current_status]

            table = self.query_one("#applications-table", DataTable)
            table.clear()

            # Add results to table
            for app in applications:
                # Format applied date
                try:
                    applied_date = datetime.fromisoformat(app["applied_date"])
                    formatted_date = applied_date.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    formatted_date = app["applied_date"]

                table.add_row(
                    str(app["id"]),
                    app["job_title"],
                    app.get("company", {}).get("name", ""),
                    app["position"],
                    app["status"],
                    formatted_date,
                )

            count = len(applications)
            self.update_status(f"Found {count} application{'s' if count != 1 else ''} matching '{search_term}'")

        except Exception as e:
            self.update_status(f"Search error: {str(e)}")

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

    def update_status(self, message: str) -> None:
        """Update status message in the footer."""
        self.app.sub_title = message

    def _confirm_delete_application(self, app_id: str) -> None:
        """Show a confirmation dialog for deleting an application."""

        def do_delete():
            service = ApplicationService()
            success = service.delete(int(app_id))

            if success:
                self.app.sub_title = f"Successfully deleted application #{app_id}"
                self.load_applications(self.current_status)
            else:
                self.app.sub_title = f"Application #{app_id} not found"

        self.app.push_screen(
            ConfirmationModal(
                title="Confirm Deletion",
                message=f"Are you sure you want to delete application #{app_id}?",
                confirm_text="Delete",
                cancel_text="Cancel",
                on_confirm=do_delete,
                dangerous=True,
            )
        )

    # Action methods for key bindings
    def action_add_application(self) -> None:
        """Open the application creation form."""
        self.app.push_screen(ApplicationForm(on_saved=self.load_applications))

    def action_delete_application(self) -> None:
        """Delete the selected application."""
        table = self.query_one("#applications-table", DataTable)
        if table.cursor_row is not None:
            app_id = table.get_row_at(table.cursor_row)[0]
            self._confirm_delete_application(app_id)

    def action_edit_application(self) -> None:
        """Edit the selected application."""
        table = self.query_one("#applications-table", DataTable)
        if table.cursor_row is not None:
            app_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(ApplicationForm(app_id=app_id, on_saved=self.load_applications))

    def action_view_application(self) -> None:
        """View the selected application."""
        table = self.query_one("#applications-table", DataTable)
        if table.cursor_row is not None:
            app_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(ApplicationForm(app_id=app_id, readonly=True))

    def action_change_status(self) -> None:
        """Change the status of the selected application."""
        table = self.query_one("#applications-table", DataTable)
        if table.cursor_row is not None:
            app_id = table.get_row_at(table.cursor_row)[0]
            status = table.get_row_at(table.cursor_row)[4]
            from src.tui.tabs.applications.status_transition import StatusTransitionDialog

            self.app.push_screen(StatusTransitionDialog(app_id, status, self.load_applications))

    def action_refresh_applications(self) -> None:
        """Refresh the applications list."""
        self.load_applications(self.current_status)
