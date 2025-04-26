"""Custom widget for displaying a list of applications."""

from typing import Any

from textual.app import ComposeResult
from textual.widgets import DataTable, Static


class ApplicationList(Static):
    """A widget displaying a list of applications."""

    def __init__(self, title: str, _id: str = None):
        """Initialize the application list.

        Args:
            title: The title to display
            _id: Optional widget ID
        """
        super().__init__(id=_id)
        self.title = title

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static(self.title, classes="list-title")
        yield DataTable(id=f"{self.id}-table" if self.id else None)

    def on_mount(self) -> None:
        """Set up the table when mounted."""
        table = self.query_one(DataTable)
        table.add_columns("Job Title", "Company", "Status", "Applied Date")
        table.cursor_type = "row"

    def update_applications(self, applications: list[dict[str, Any]]) -> None:
        """Update the applications displayed in the list."""
        table = self.query_one(DataTable)
        table.clear()

        if not applications:
            table.add_row("No applications found", "", "", "")
            return

        for app in applications:
            company_name = app.get("company", {}).get("name", "")
            table.add_row(app["job_title"], company_name, app["status"], app["applied_date"])
