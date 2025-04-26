"""Custom widget for displaying statistics."""

from textual.app import ComposeResult
from textual.widgets import Static


class StatsCard(Static):
    """A card displaying a statistic with a label and value."""

    def __init__(self, title: str, value: str, _id: str = None):
        """Initialize the stats card.

        Args:
            title: The label to display
            value: The value to display
            _id: Optional widget ID
        """
        super().__init__(id=_id)
        self.title = title
        self.value = value

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static(self.title, classes="stats-title")
        yield Static(self.value, classes="stats-value")

    def update_value(self, value: str) -> None:
        """Update the displayed value."""
        self.query_one(".stats-value", Static).update(value)
