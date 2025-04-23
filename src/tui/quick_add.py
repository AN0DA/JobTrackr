"""Quick application creation dialog."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Button, Label, Input, Select
from datetime import datetime

from src.services.application_service import ApplicationService
from src.services.company_service import CompanyService


class QuickAddDialog(ModalScreen):
    """Dialog for quickly adding new job applications."""

    def compose(self) -> ComposeResult:
        with Container(id="quick-add-dialog"):
            yield Label("Quick Add Application", id="dialog-title")

            with Vertical(id="quick-form"):
                yield Label("Job Title:", classes="field-label")
                yield Input(placeholder="Software Engineer", id="job-title")

                yield Label("Company:", classes="field-label")
                with Horizontal():
                    yield Select([], id="company-select")
                    yield Button("+ New", variant="success", id="new-company")

                yield Label("Position:", classes="field-label")
                yield Input(placeholder="Senior Developer", id="position")

                yield Label("Status:", classes="field-label")
                yield Select(
                    [(status, status) for status in ["SAVED", "APPLIED"]],
                    value="SAVED",
                    id="status"
                )

                yield Label("Applied Date:", classes="field-label")
                yield Input(
                    placeholder="YYYY-MM-DD",
                    id="applied-date",
                    value=datetime.now().strftime("%Y-%m-%d")
                )

            with Horizontal(id="dialog-buttons"):
                yield Button("Cancel", id="cancel-quick-add")
                yield Button("Save", id="save-quick-add", variant="success")

    def on_mount(self) -> None:
        """Load companies when the dialog is mounted."""
        self.load_companies()

    def load_companies(self) -> None:
        """Load companies for the dropdown."""
        try:
            service = CompanyService()
            companies = service.get_companies()

            company_select = self.query_one("#company-select", Select)
            company_select.set_options([
                (company["name"], str(company["id"])) for company in companies
            ])

            # Select the first company if available
            if companies:
                company_select.value = str(companies[0]["id"])

        except Exception as e:
            self.app.sub_title = f"Error loading companies: {str(e)}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "cancel-quick-add":
            self.app.pop_screen()

        elif button_id == "new-company":
            # Import here to avoid circular import
            from src.tui.company_form import CompanyForm
            self.app.push_screen(CompanyForm(on_saved=self.load_companies))

        elif button_id == "save-quick-add":
            self.save_application()

    def save_application(self) -> None:
        """Save the new application."""
        try:
            # Get values from form
            job_title = self.query_one("#job-title", Input).value
            company_id = self.query_one("#company-select", Select).value
            position = self.query_one("#position", Input).value
            status = self.query_one("#status", Select).value
            applied_date = self.query_one("#applied-date", Input).value

            # Validate required fields
            if not job_title:
                self.app.sub_title = "Job title is required"
                return

            if not company_id:
                self.app.sub_title = "Company is required"
                return

            if not position:
                self.app.sub_title = "Position is required"
                return

            # Prepare data
            app_data = {
                "job_title": job_title,
                "company_id": int(company_id),
                "position": position,
                "status": status,
                "applied_date": applied_date,
            }

            # Create application
            service = ApplicationService()
            result = service.create_application(app_data)

            self.app.sub_title = f"Application '{job_title}' created successfully"
            self.app.pop_screen()

            # Refresh applications list if visible
            from src.tui.applications import ApplicationsList
            app_list = self.app.query_one(ApplicationsList, default=None)
            if app_list:
                app_list.load_applications()

            # Refresh dashboard if visible
            from src.tui.dashboard import Dashboard
            dashboard = self.app.query_one(Dashboard, default=None)
            if dashboard:
                dashboard.refresh_data()

        except Exception as e:
            self.app.sub_title = f"Error creating application: {str(e)}"
