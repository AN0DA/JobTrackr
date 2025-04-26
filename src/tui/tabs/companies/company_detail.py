"""Detail screen for viewing a company and its relationships."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Static, Button, DataTable, Label, TabbedContent, TabPane

from src.services.company_service import CompanyService
from src.services.application_service import ApplicationService
from src.tui.tabs.companies.relationship_form import CompanyRelationshipForm


class CompanyDetailScreen(Screen):
    """Screen for viewing details about a company."""

    def __init__(self, company_id: int):
        super().__init__()
        self.company_id = company_id
        self.company_data = None

    def compose(self) -> ComposeResult:
        with Container(id="company-detail"):
            with Horizontal(id="company-header"):
                with Vertical(id="company-identity"):
                    yield Static("", id="company-name", classes="company-title")
                    yield Static("", id="company-type", classes="company-type")

                with Vertical(id="header-actions"):
                    yield Button("Edit Company", id="edit-company")
                    yield Button(
                        "Add Relationship", id="add-relationship", variant="primary"
                    )

            with TabbedContent(id="company-tabs"):
                with TabPane("Overview", id="tab-overview"):
                    with Grid(id="company-info-grid", classes="info-grid"):
                        yield Label("Industry:", classes="field-label")
                        yield Static("", id="company-industry", classes="field-value")

                        yield Label("Website:", classes="field-label")
                        yield Static("", id="company-website", classes="field-value")

                        yield Label("Size:", classes="field-label")
                        yield Static("", id="company-size", classes="field-value")

                    yield Label("Notes:", classes="section-label")
                    with Container(id="notes-container", classes="notes-box"):
                        yield Static("", id="company-notes")

                with TabPane("Relationships", id="tab-relationships"):
                    yield Label("Company Relationships", classes="section-label")
                    yield DataTable(id="relationships-table")

                    with Container(id="relationship-viz", classes="viz-container"):
                        yield Static(
                            "Relationship Visualization:", classes="section-label"
                        )
                        yield Static(
                            "[Visualization would go here in a graphical UI]",
                            classes="placeholder",
                        )

                with TabPane("Applications", id="tab-applications"):
                    yield Label(
                        "Job Applications with this Company", classes="section-label"
                    )
                    yield DataTable(id="applications-table")

            with Horizontal(id="detail-actions"):
                yield Button("Back", id="back-button", variant="default")

    def on_mount(self) -> None:
        """Load company data when the screen is mounted."""
        # Set up tables
        relationships_table = self.query_one("#relationships-table", DataTable)
        relationships_table.add_columns(
            "Company", "Type", "Relationship", "Direction", "Actions"
        )
        relationships_table.cursor_type = "row"

        applications_table = self.query_one("#applications-table", DataTable)
        applications_table.add_columns(
            "ID", "Job Title", "Position", "Status", "Applied Date"
        )
        applications_table.cursor_type = "row"

        # Load company data
        self.load_company_data()

    def load_company_data(self) -> None:
        """Load all company data and populate the UI."""
        try:
            # Load company details
            service = CompanyService()
            self.company_data = service.get_company(self.company_id)

            if not self.company_data:
                self.app.sub_title = f"Company {self.company_id} not found"
                return

            # Update header
            self.query_one("#company-name", Static).update(self.company_data["name"])

            company_type = self.company_data.get("type", "DIRECT_EMPLOYER")
            self.query_one("#company-type", Static).update(f"Type: {company_type}")

            # Update overview fields
            self.query_one("#company-industry", Static).update(
                self.company_data.get("industry", "N/A")
            )
            self.query_one("#company-website", Static).update(
                self.company_data.get("website", "N/A")
            )
            self.query_one("#company-size", Static).update(
                self.company_data.get("size", "N/A")
            )

            # Update notes
            notes = self.company_data.get("notes", "No notes available.")
            self.query_one("#company-notes", Static).update(notes)

            # Load relationships
            self.load_relationships()

            # Load applications
            self.load_applications()

            self.app.sub_title = f"Viewing company: {self.company_data['name']}"

        except Exception as e:
            self.app.sub_title = f"Error loading company data: {str(e)}"

    def load_relationships(self) -> None:
        """Load company relationships."""
        try:
            service = CompanyService()
            relationships = service.get_related_companies(self.company_id)

            table = self.query_one("#relationships-table", DataTable)
            table.clear()

            if not relationships:
                table.add_row("No relationships found", "", "", "", "")
                return

            for rel in relationships:
                direction = "→" if rel["direction"] == "outgoing" else "←"
                table.add_row(
                    rel["company_name"],
                    rel["company_type"],
                    rel["relationship_type"],
                    direction,
                    "Edit | Delete",
                )

        except Exception as e:
            self.app.sub_title = f"Error loading relationships: {str(e)}"

    def load_applications(self) -> None:
        """Load job applications for this company."""
        try:
            # Note: This would require an actual method in ApplicationService
            # For now, we'll simulate with placeholder data
            app_service = ApplicationService()
            # This method doesn't exist in the provided code, but would be useful
            # applications = app_service.get_applications_by_company(self.company_id)

            # Placeholder example - in a real implementation we'd call the service
            applications = []

            table = self.query_one("#applications-table", DataTable)
            table.clear()

            if not applications:
                table.add_row("No applications found", "", "", "", "")

        except Exception as e:
            self.app.sub_title = f"Error loading applications: {str(e)}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "back-button":
            self.app.pop_screen()

        elif button_id == "edit-company":
            from src.tui.tabs.companies.company_form import CompanyForm

            def refresh_after_edit():
                self.load_company_data()

            self.app.push_screen(
                CompanyForm(
                    company_id=str(self.company_id), on_saved=refresh_after_edit
                )
            )

        elif button_id == "add-relationship":
            self.app.push_screen(
                CompanyRelationshipForm(
                    source_company_id=self.company_id, on_saved=self.load_relationships
                )
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in tables."""
        table_id = event.data_table.id

        if table_id == "relationships-table":
            # Handle relationship selection - could open edit dialog
            pass

        elif table_id == "applications-table":
            # Open application details
            from src.tui.tabs.applications.application_detail import ApplicationDetail

            row = event.data_table.get_row(event.row_key)
            if row[0] != "No applications found":
                app_id = int(row[0])
                self.app.push_screen(ApplicationDetail(app_id))
