"""Form for creating/editing companies."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical
from textual.widgets import Input, Button, Label, TextArea

from src.tui.api_client import APIClient


class CompanyForm(Screen):
    """Form for creating a new company."""

    def compose(self) -> ComposeResult:
        """Compose the form layout."""
        with Container(id="company-form"):
            yield Label("New Company", id="form-title")

            with Vertical(id="form-fields"):
                yield Label("Company Name")
                yield Input(id="company-name")

                yield Label("Website")
                yield Input(id="website")

                yield Label("Industry")
                yield Input(id="industry")

                yield Label("Size")
                yield Input(id="size")

                yield Label("Notes")
                yield TextArea(id="notes")

            with Vertical(id="form-actions"):
                yield Button("Save", variant="primary", id="save-company")
                yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "save-company":
            self.save_company()

        elif button_id == "cancel":
            self.app.pop_screen()

    async def save_company(self) -> None:
        """Save the company data."""
        try:
            # Get values from form
            name = self.query_one("#company-name", Input).value
            website = self.query_one("#website", Input).value
            industry = self.query_one("#industry", Input).value
            size = self.query_one("#size", Input).value
            notes = self.query_one("#notes", TextArea).text

            # Validate required fields
            if not name:
                self.app.sub_title = "Company name is required"
                return

            # Prepare data
            company_data = {
                "name": name,
                "website": website or None,
                "industry": industry or None,
                "size": size or None,
                "notes": notes or None,
            }

            client = APIClient()
            result = await client.create_company(company_data)

            self.app.sub_title = "Company created successfully"

            # Return to the previous screen
            self.app.pop_screen()

            # Refresh the company dropdown in the application form if it's visible
            app_form = self.app.query_one(ApplicationForm, default=None)
            if app_form:
                await app_form.load_companies()

        except Exception as e:
            self.app.sub_title = f"Error saving company: {str(e)}"