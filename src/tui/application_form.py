"""Form for creating/editing job applications."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical
from textual.widgets import Input, Button, Label, TextArea, Select
from datetime import datetime

from src.tui.api_client import APIClient
from src.tui.company_form import CompanyForm


class ApplicationForm(Screen):
    """Form for creating or editing a job application."""

    def __init__(self, app_id: str = None, readonly: bool = False):
        """Initialize the form.

        Args:
            app_id: If provided, the form will edit the existing application
            readonly: If True, the form will be displayed in read-only mode
        """
        super().__init__()
        self.app_id = app_id
        self.readonly = readonly
        self.companies = []

    def compose(self) -> ComposeResult:
        """Compose the form layout."""
        with Container(id="app-form"):
            yield Label(
                "View Application" if self.readonly else
                "Edit Application" if self.app_id else
                "New Application",
                id="form-title"
            )

            with Vertical(id="form-fields"):
                yield Label("Job Title")
                yield Input(id="job-title", disabled=self.readonly)

                yield Label("Company")
                with Vertical(id="company-field"):
                    yield Select([], id="company-select", disabled=self.readonly)
                    if not self.readonly:
                        yield Button("+ New Company", id="new-company", variant="primary")

                yield Label("Position")
                yield Input(id="position", disabled=self.readonly)

                yield Label("Location")
                yield Input(id="location", disabled=self.readonly)

                yield Label("Salary")
                yield Input(id="salary", disabled=self.readonly)

                yield Label("Status")
                yield Select(
                    [(status, status) for status in [
                        "SAVED", "APPLIED", "PHONE_SCREEN", "INTERVIEW",
                        "TECHNICAL_INTERVIEW", "OFFER", "ACCEPTED", "REJECTED", "WITHDRAWN"
                    ]],
                    id="status",
                    disabled=self.readonly
                )

                yield Label("Applied Date")
                yield Input(id="applied-date", placeholder="YYYY-MM-DD", disabled=self.readonly)

                yield Label("Link")
                yield Input(id="link", disabled=self.readonly)

                yield Label("Description")
                yield TextArea(id="description", disabled=self.readonly)

                yield Label("Notes")
                yield TextArea(id="notes", disabled=self.readonly)

            with Vertical(id="form-actions"):
                if not self.readonly:
                    yield Button("Save", variant="primary", id="save-app")
                yield Button("Close", id="close-form")

    async def on_mount(self) -> None:
        """Load data when the form is mounted."""
        await self.load_companies()
        if self.app_id:
            await self.load_application()

    async def load_companies(self) -> None:
        """Load companies for the dropdown."""
        try:
            client = APIClient()
            self.companies = await client.get_companies()

            company_select = self.query_one("#company-select", Select)
            company_select.set_options([
                (company["name"], company["id"]) for company in self.companies
            ])
        except Exception as e:
            self.app.sub_title = f"Error loading companies: {str(e)}"

    async def load_application(self) -> None:
        """Load application data for editing."""
        try:
            client = APIClient()
            app_data = await client.get_application(self.app_id)

            # Populate the form fields
            self.query_one("#job-title", Input).value = app_data["jobTitle"]
            self.query_one("#position", Input).value = app_data["position"]

            if app_data.get("location"):
                self.query_one("#location", Input).value = app_data["location"]

            if app_data.get("salary"):
                self.query_one("#salary", Input).value = app_data["salary"]

            self.query_one("#status", Select).value = app_data["status"]

            # Format the date
            applied_date = datetime.fromisoformat(app_data["appliedDate"]).strftime("%Y-%m-%d")
            self.query_one("#applied-date", Input).value = applied_date

            if app_data.get("link"):
                self.query_one("#link", Input).value = app_data["link"]

            if app_data.get("description"):
                self.query_one("#description", TextArea).text = app_data["description"]

            if app_data.get("notes"):
                self.query_one("#notes", TextArea).text = app_data["notes"]

            # Set company if available
            if app_data.get("company"):
                self.query_one("#company-select", Select).value = app_data["company"]["id"]

        except Exception as e:
            self.app.sub_title = f"Error loading application: {str(e)}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "new-company":
            self.app.push_screen(CompanyForm())

        elif button_id == "save-app":
            self.save_application()

        elif button_id == "close-form":
            self.app.pop_screen()

    async def save_application(self) -> None:
        """Save the application data."""
        try:
            # Get values from form
            job_title = self.query_one("#job-title", Input).value
            company_id = self.query_one("#company-select", Select).value
            position = self.query_one("#position", Input).value
            location = self.query_one("#location", Input).value
            salary = self.query_one("#salary", Input).value
            status = self.query_one("#status", Select).value
            applied_date = self.query_one("#applied-date", Input).value
            link = self.query_one("#link", Input).value
            description = self.query_one("#description", TextArea).text
            notes = self.query_one("#notes", TextArea).text

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

            if not status:
                self.app.sub_title = "Status is required"
                return

            if not applied_date:
                self.app.sub_title = "Applied date is required"
                return

            # Prepare data
            app_data = {
                "jobTitle": job_title,
                "companyId": company_id,
                "position": position,
                "location": location or None,
                "salary": salary or None,
                "status": status,
                "appliedDate": applied_date,
                "link": link or None,
                "description": description or None,
                "notes": notes or None,
            }

            client = APIClient()

            if self.app_id:
                # Update existing application
                app_data["id"] = self.app_id
                result = await client.update_application(app_data)
                self.app.sub_title = "Application updated successfully"
            else:
                # Create new application
                result = await client.create_application(app_data)
                self.app.sub_title = "Application created successfully"

            # Return to the previous screen
            self.app.pop_screen()

            # Refresh the applications list if it's visible
            app_list = self.app.query_one(ApplicationsList, default=None)
            if app_list:
                await app_list.load_applications()

        except Exception as e:
            self.app.sub_title = f"Error saving application: {str(e)}"