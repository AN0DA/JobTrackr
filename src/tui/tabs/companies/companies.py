"""Companies management screen for the Job Tracker TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Input, Label, Select, Static

from src.db.models import CompanyType
from src.services.company_service import CompanyService
from src.tui.tabs.companies.company_detail import CompanyDetailScreen
from src.tui.tabs.companies.company_form import CompanyForm


class CompaniesList(Static):
    """Companies listing and management screen."""

    BINDINGS = [
        ("a", "add_company", "Add Company"),
        ("d", "delete_company", "Delete"),
        ("e", "edit_company", "Edit"),
        ("v", "view_company", "View"),
        ("r", "refresh_companies", "Refresh"),
    ]

    def __init__(self):
        super().__init__()
        self.sort_column = "Name"
        self.sort_ascending = True

    def compose(self) -> ComposeResult:
        """Compose the companies screen layout."""
        with Container(classes="list-view-container"):
            # Header section
            with Container(classes="list-header"):
                # Filter bar
                with Horizontal(classes="filter-bar"):
                    with Vertical(classes="filter-section"):
                        yield Static("Type:", classes="filter-label")
                        yield Select(
                            [(ct.value, ct.value) for ct in CompanyType] + [("All", "All")],
                            value="All",
                            id="type-filter",
                            classes="filter-dropdown",
                        )

                    # Search section
                    with Horizontal(classes="search-section"):
                        yield Input(
                            placeholder="Search companies...",
                            id="company-search",
                            classes="search-box",
                        )
                        yield Button("🔍", id="search-button")

                    # Quick action buttons
                    with Horizontal(classes="action-section"):
                        yield Button("New Company", variant="primary", id="new-company")

            # Table section
            with Container(classes="table-container"):
                yield DataTable(id="companies-table")

            # Footer section
            with Horizontal(classes="list-footer"):
                with Horizontal(classes="action-buttons"):
                    yield Button("View", id="view-company", disabled=True)
                    yield Button("Edit", id="edit-company", disabled=True)
                    yield Button("Delete", id="delete-company", variant="error", disabled=True)

    def on_mount(self) -> None:
        """Set up the screen when mounted."""
        table = self.query_one("#companies-table", DataTable)
        table.add_columns(
            "ID",
            "Name",
            "Industry",
            "Type",
            "Website",
            "Size",
        )
        table.cursor_type = "row"
        table.can_focus = True
        table.zebra_stripes = True

        # Enable sorting
        table.sort_column_click = True

        self.load_companies()

    def load_companies(self, company_type: str = None) -> None:
        """Load companies from the database."""
        self.update_status("Loading companies...")

        try:
            service = CompanyService()
            companies = service.get_companies()

            # Apply type filter if specified
            if company_type and company_type != "All":
                companies = [c for c in companies if c.get("type") == company_type]

            table = self.query_one("#companies-table", DataTable)
            table.clear()

            # Convert to list for sorting
            companies_list = list(companies)

            # Apply current sort settings
            self._sort_companies(companies_list)

            for company in companies_list:
                table.add_row(
                    str(company["id"]),
                    company["name"],
                    company.get("industry", ""),
                    company.get("type", "DIRECT_EMPLOYER"),
                    company.get("website", ""),
                    company.get("size", ""),
                )

            self.update_status(f"Loaded {len(companies)} companies")
        except Exception as e:
            self.update_status(f"Error loading companies: {str(e)}")

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle type filter changes."""
        if event.select.id == "type-filter":
            company_type = event.value if event.value != "All" else None
            self.load_companies(company_type)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission."""
        if event.input.id == "company-search":
            self.search_companies(event.input.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        table = self.query_one("#companies-table", DataTable)

        if button_id == "new-company":
            self.app.push_screen(CompanyForm(on_saved=self.load_companies))

        elif button_id == "view-company" and table.cursor_row is not None:
            app_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(CompanyDetailScreen(int(app_id)))

        elif button_id == "edit-company" and table.cursor_row is not None:
            app_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(CompanyForm(company_id=app_id, on_saved=self.load_companies))

        elif button_id == "delete-company" and table.cursor_row is not None:
            app_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(DeleteConfirmationModal(app_id, self.load_companies))

        elif button_id == "search-button":
            search_term = self.query_one("#company-search", Input).value
            self.search_companies(search_term)

    def search_companies(self, search_term: str) -> None:
        """Search companies by name or industry."""
        if not search_term:
            self.load_companies()
            return

        self.update_status(f"Searching for '{search_term}'...")

        try:
            service = CompanyService()
            all_companies = service.get_companies()

            # Simple case-insensitive search
            search_term = search_term.lower()
            filtered_companies = [
                c
                for c in all_companies
                if search_term in c["name"].lower()
                or (c.get("industry") and search_term in c.get("industry", "").lower())
                or (c.get("notes") and search_term in c.get("notes", "").lower())
            ]

            table = self.query_one("#companies-table", DataTable)
            table.clear()

            for company in filtered_companies:
                table.add_row(
                    str(company["id"]),
                    company["name"],
                    company.get("industry", ""),
                    company.get("type", "DIRECT_EMPLOYER"),
                    company.get("website", ""),
                    company.get("size", ""),
                )

            self.update_status(f"Found {len(filtered_companies)} companies matching '{search_term}'")

        except Exception as e:
            self.update_status(f"Search error: {str(e)}")

    def update_status(self, message: str) -> None:
        """Update status message in the footer."""
        self.app.sub_title = message

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Enable buttons when a row is highlighted."""
        view_btn = self.query_one("#view-company", Button)
        edit_btn = self.query_one("#edit-company", Button)
        delete_btn = self.query_one("#delete-company", Button)

        view_btn.disabled = False
        edit_btn.disabled = False
        delete_btn.disabled = False

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Open the company detail view when a row is selected."""
        table = self.query_one("#companies-table", DataTable)
        company_id = table.get_row(event.row_key)[0]
        self.app.push_screen(CompanyDetailScreen(int(company_id)))

    def _sort_companies(self, companies):
        """Sort companies based on current sort settings."""
        # Define sort keys for each column
        sort_keys = {
            "ID": lambda c: int(c["id"]),
            "Name": lambda c: c["name"].lower(),
            "Industry": lambda c: (c.get("industry") or "").lower(),
            "Type": lambda c: c.get("type", ""),
            "Website": lambda c: (c.get("website") or "").lower(),
            "Size": lambda c: c.get("size", ""),
        }

        # Get sort key function
        sort_key = sort_keys.get(self.sort_column, lambda c: c["name"].lower())

        # Sort companies
        companies.sort(key=sort_key, reverse=not self.sort_ascending)

    def action_add_company(self) -> None:
        """Open the company creation form."""
        self.app.push_screen(CompanyForm(on_saved=self.load_companies))

    def action_delete_company(self) -> None:
        """Delete the selected company."""
        table = self.query_one("#companies-table", DataTable)
        if table.cursor_row is not None:
            company_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(DeleteConfirmationModal(company_id, self.load_companies))

    def action_edit_company(self) -> None:
        """Edit the selected company."""
        table = self.query_one("#companies-table", DataTable)
        if table.cursor_row is not None:
            company_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(CompanyForm(company_id=company_id, on_saved=self.load_companies))

    def action_view_company(self) -> None:
        """View the selected company."""
        table = self.query_one("#companies-table", DataTable)
        if table.cursor_row is not None:
            company_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(CompanyDetailScreen(int(company_id)))

    def action_refresh_companies(self) -> None:
        """Refresh the companies list."""
        self.load_companies()


class DeleteConfirmationModal(ModalScreen):
    """Confirmation dialog for deleting companies."""

    def __init__(self, company_id: str, on_delete=None):
        super().__init__()
        self.company_id = company_id
        self.on_delete = on_delete

    def compose(self) -> ComposeResult:
        yield Container(
            Label(f"Are you sure you want to delete company #{self.company_id}?"),
            Label(
                "This will permanently remove the company and all its relationships.",
                classes="warning-text",
            ),
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
            self.delete_company()

    def delete_company(self) -> None:
        try:
            service = CompanyService()
            success = service.delete_company(int(self.company_id))

            if success:
                self.app.sub_title = f"Successfully deleted company #{self.company_id}"
            else:
                self.app.sub_title = f"Company #{self.company_id} not found"

            self.app.pop_screen()

            # Run callback after deletion
            if self.on_delete:
                self.on_delete()

        except Exception as e:
            self.app.sub_title = f"Error deleting company: {str(e)}"
            self.app.pop_screen()
