"""Custom widget for displaying a list of reminders."""

from textual.widgets import Static, DataTable
from textual.app import ComposeResult
from typing import List, Dict, Any


class ReminderList(Static):
    """A widget displaying a list of reminders."""

    def __init__(self, title: str, id: str = None):
        """Initialize the reminder list.

        Args:
            title: The title to display
            id: Optional widget ID
        """
        super().__init__(id=id)
        self.title = title

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static(self.title, classes="list-title")
        yield DataTable(id=f"{self.id}-table" if self.id else None)

    def on_mount(self) -> None:
        """Set up the table when mounted."""
        table = self.query_one(DataTable)
        table.add_columns("Title", "Date", "Completed")
        table.cursor_type = "row"

    def update_reminders(self, reminders: List[Dict[str, Any]]) -> None:
        """Update the reminders displayed in the list."""
        table = self.query_one(DataTable)
        table.clear()

        if not reminders:
            table.add_row("No upcoming reminders", "", "")
            return

        for reminder in reminders:
            table.add_row(
                reminder["title"],
                reminder["date"],
                "✓" if reminder["completed"] else "✗",
            )
