from collections.abc import Callable

from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Label, Static, TabbedContent, TabPane

from src.services.application_service import ApplicationService
from src.services.company_service import CompanyService
from src.tui.tabs.companies.relationship_form import CompanyRelationshipForm
from src.tui.widgets.confirmation_modal import ConfirmationModal


class CompanyDetailScreen(Screen):
    """Screen for viewing details about a company."""

    def __init__(self, company_id: int, on_updated: Callable | None = None):
        """Initialize company detail screen.

        Args:
            company_id: ID of company to display
            on_updated: Optional callback when company is updated
        """
        super().__init__()
        self.company_id = company_id
        self.company_data = None
        self.on_updated = on_updated

    def compose(self) -> ComposeResult:
        with Container(id="company-detail"):
            with Horizontal(id="company-header"):
                with Vertical(id="company-identity"):
                    yield Static("", id="company-name", classes="company-title")
                    yield Static("", id="company-type", classes="company-type")

                with Vertical(id="header-actions"):
                    yield Button("Edit Company", id="edit-company")
                    yield Button("Add Relationship", id="add-relationship", variant="primary")

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
                        yield Static("Relationship Visualization:", classes="section-label")
                        yield Static(
                            "[Visualization would go here in a graphical UI]",
                            classes="placeholder",
                        )

                with TabPane("Applications", id="tab-applications"):
                    yield Label("Job Applications with this Company", classes="section-label")
                    yield DataTable(id="applications-table")

            with Horizontal(id="detail-actions"):
                yield Button("Back", id="back-button", variant="default")

    def on_mount(self) -> None:
        """Load company data when the screen is mounted."""
        # Set up tables
        relationships_table = self.query_one("#relationships-table", DataTable)
        relationships_table.add_columns("Company", "Type", "Relationship", "Direction", "Actions")
        relationships_table.cursor_type = "row"

        applications_table = self.query_one("#applications-table", DataTable)
        applications_table.add_columns("ID", "Job Title", "Position", "Status", "Applied Date")
        applications_table.cursor_type = "row"

        # Load company data
        self.load_company_data()

    def load_company_data(self) -> None:
        """Load all company data and populate the UI."""
        try:
            # Load company details
            service = CompanyService()
            self.company_data = service.get(self.company_id)

            if not self.company_data:
                self.app.sub_title = f"Company {self.company_id} not found"
                return

            # Update header
            self.query_one("#company-name", Static).update(self.company_data.get("name", "Unknown"))

            # Make sure company type is a string
            company_type = self.company_data.get("type", "")
            if company_type is None:
                company_type = "DIRECT_EMPLOYER"
            self.query_one("#company-type", Static).update(f"Type: {company_type}")

            # Update overview fields - ensure we always use strings for display
            industry = self.company_data.get("industry", "")
            if industry is None or industry == "":
                industry = "Not specified"
            self.query_one("#company-industry", Static).update(industry)

            website = self.company_data.get("website", "")
            if website is None or website == "":
                website = "No website provided"
            self.query_one("#company-website", Static).update(website)

            size = self.company_data.get("size", "")
            if size is None or size == "":
                size = "Not specified"
            self.query_one("#company-size", Static).update(size)

            # Update notes
            notes = self.company_data.get("notes", "")
            if notes is None or notes == "":
                notes = "No notes available."
            self.query_one("#company-notes", Static).update(notes)

            # Load relationships
            self.load_relationships()

            # Load applications
            self.load_applications()

            self.app.sub_title = f"Viewing company: {self.company_data.get('name', 'Unknown')}"

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
                    rel.get("company_type", ""),
                    rel["relationship_type"],
                    direction,
                    "Edit | Delete",
                )

        except Exception as e:
            self.app.sub_title = f"Error loading relationships: {str(e)}"

    def load_applications(self) -> None:
        """Load job applications for this company."""
        try:
            # Now properly fetch applications from the service
            app_service = ApplicationService()
            applications = app_service.get_applications_by_company(self.company_id)

            table = self.query_one("#applications-table", DataTable)
            table.clear()

            if not applications:
                table.add_row("No applications found", "", "", "", "")
                return

            for app in applications:
                table.add_row(
                    str(app["id"]),
                    app["job_title"],
                    app["position"],
                    app["status"],
                    app["applied_date"],
                )
        except Exception as e:
            self.app.sub_title = f"Error loading applications: {str(e)}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "back-button":
            self.app.pop_screen()
            # Call the on_updated callback if provided
            if self.on_updated:
                self.on_updated()

        elif button_id == "edit-company":
            from src.tui.tabs.companies.company_form import CompanyForm

            self.app.push_screen(CompanyForm(company_id=str(self.company_id), on_saved=self.load_company_data))

        elif button_id == "add-relationship":
            self.app.push_screen(
                CompanyRelationshipForm(source_company_id=self.company_id, on_saved=self.load_relationships)
            )

    def _confirm_delete_relationship(self, relationship_id: str) -> None:
        """Show confirmation dialog for relationship deletion."""

        def do_delete():
            try:
                # This would need a delete_relationship method in the company service
                # For now it's just a placeholder
                self.app.sub_title = "Relationship deletion not implemented yet"
                self.load_relationships()
            except Exception as e:
                self.app.sub_title = f"Error deleting relationship: {str(e)}"

        self.app.push_screen(
            ConfirmationModal(
                title="Confirm Deletion",
                message="Are you sure you want to delete this relationship?",
                confirm_text="Delete",
                cancel_text="Cancel",
                on_confirm=do_delete,
                dangerous=True,
            )
        )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in tables."""
        table_id = event.data_table.id

        if table_id == "relationships-table":
            # Handle relationship selection - placeholder for future implementation
            # For full implementation, we would get the relationship ID and show actions
            pass

        elif table_id == "applications-table":
            # Open application details
            from src.tui.tabs.applications.application_detail import ApplicationDetail

            row = event.data_table.get_row(event.row_key)
            if row[0] != "No applications found":
                app_id = int(row[0])
                self.app.push_screen(ApplicationDetail(app_id, on_updated=self.load_applications))
