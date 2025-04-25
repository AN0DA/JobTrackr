"""Search dialog for finding applications."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Horizontal
from textual.widgets import Button, Label, Input, DataTable

from src.services.application_service import ApplicationService


class SearchDialog(ModalScreen):
    """Dialog for searching applications."""

    def compose(self) -> ComposeResult:
        with Container(id="search-dialog"):
            yield Label("Search Applications", id="dialog-title")

            with Horizontal(id="search-form"):
                yield Input(placeholder="Enter search term...", id="search-input")
                yield Button("Search", variant="primary", id="perform-search")

            yield DataTable(id="search-results")

            yield Button("Close", id="close-search")

    def on_mount(self) -> None:
        """Set up the results table."""
        table = self.query_one("#search-results", DataTable)
        table.add_columns("ID", "Job Title", "Company", "Position", "Status")
        table.cursor_type = "row"
        table.zebra_stripes = True

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in search input."""
        if event.input.id == "search-input":
            self.perform_search()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "perform-search":
            self.perform_search()

        elif button_id == "close-search":
            self.app.pop_screen()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Open the selected application."""
        table = self.query_one("#search-results", DataTable)
        app_id = table.get_row_at(event.row_key)[0]

        # Close search dialog
        self.app.pop_screen()

        # Open application form
        from src.tui.application_form import ApplicationForm

        self.app.push_screen(ApplicationForm(app_id=app_id))

    def perform_search(self) -> None:
        """Search for applications matching the search term."""
        search_term = self.query_one("#search-input", Input).value

        if not search_term:
            self.app.sub_title = "Please enter a search term"
            return

        try:
            self.app.sub_title = f"Searching for '{search_term}'..."

            service = ApplicationService()
            results = service.search_applications(search_term)

            table = self.query_one("#search-results", DataTable)
            table.clear()

            for app in results:
                table.add_row(
                    str(app["id"]),
                    app["job_title"],
                    app.get("company", {}).get("name", ""),
                    app["position"],
                    app["status"],
                )

            count = len(results)
            self.app.sub_title = f"Found {count} result{'s' if count != 1 else ''}"

        except Exception as e:
            self.app.sub_title = f"Search error: {str(e)}"
