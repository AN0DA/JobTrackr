from typing import Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, DataTable, Input, Static

from src.services.base_service import BaseService


class ListView(Static):
    """Base class for list views like ApplicationsList, CompaniesList, etc."""

    def __init__(
        self,
        service: BaseService,
        columns: list[str],
        title: str = "Items",
        _id: str | None = None,
    ):
        """Initialize the list view.

        Args:
            service: Service class to use for data operations
            columns: List of columns to display
            title: Title of the list view
            _id: Optional widget ID
        """
        super().__init__(id=_id)
        self.service = service
        self.columns = columns
        self.title = title
        self.sort_column = columns[0] if columns else "id"
        self.sort_ascending = True

    def compose(self) -> ComposeResult:
        """Compose the list view layout."""
        with Container(classes="list-view-container"):
            # Header section
            with Container(classes="list-header"):
                yield Static(self.title, classes="list-title")

                # Quick action buttons
                with Horizontal(classes="action-section"):
                    yield Button(
                        f"New {self.service.entity_name.capitalize()}",
                        variant="primary",
                        id=f"new-{self.service.entity_name}",
                    )

                    # Search section
                    yield Input(
                        placeholder=f"Search {self.title.lower()}...",
                        id="search-input",
                        classes="search-box",
                    )
                    yield Button("🔍", id="search-button")

            # Table section
            with Container(classes="table-container"):
                yield DataTable(id=f"{self.service.entity_name.lower()}-table")

            # Footer section
            with Horizontal(classes="list-footer"):
                with Horizontal(classes="action-buttons"):
                    yield Button("View", id="view-item", disabled=True)
                    yield Button("Edit", id="edit-item", disabled=True)
                    yield Button("Delete", id="delete-item", variant="error", disabled=True)

    def on_mount(self) -> None:
        """Set up the screen when mounted."""
        table = self.query_one(DataTable)
        
        # Only add columns if they don't already exist to prevent duplication
        if not table.columns:
            table.add_columns(*self.columns)
            
        table.cursor_type = "row"
        table.can_focus = True
        table.zebra_stripes = True

        # Enable sorting
        table.sort_column_click = True

        self.load_data()

    def load_data(self) -> None:
        """Load data from the service."""
        self.update_status(f"Loading {self.title.lower()}...")

        try:
            items = self.service.get_all(
                sort_by=self.sort_column.lower().replace(" ", "_"),
                sort_desc=not self.sort_ascending,
                limit=50,
            )

            table = self.query_one(DataTable)
            table.clear()

            if not items:
                self.update_status(f"No {self.title.lower()} found")
                self._disable_actions()
                return

            for item in items:
                # This method needs to be implemented by subclasses to format rows
                row_data = self._format_row(item)
                table.add_row(*row_data)

            self.update_status(f"Loaded {len(items)} {self.title.lower()}")

        except Exception as e:
            self.update_status(f"Error loading data: {str(e)}")

    def _format_row(self, item: dict[str, Any]) -> list[str]:
        """Format an item for display in the table.

        Subclasses should implement this method to format items for their specific needs.
        """
        raise NotImplementedError("Subclasses must implement _format_row")

    def update_status(self, message: str) -> None:
        """Update status message in the footer."""
        self.app.sub_title = message

    def _disable_actions(self) -> None:
        """Disable action buttons."""
        view_btn = self.query_one("#view-item", Button)
        edit_btn = self.query_one("#edit-item", Button)
        delete_btn = self.query_one("#delete-item", Button)

        view_btn.disabled = True
        edit_btn.disabled = True
        delete_btn.disabled = True
