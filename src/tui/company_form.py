"""Form for creating/editing companies."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical
from textual.widgets import Input, Button, Label, TextArea
from typing import Callable, Optional

from src.services.company_service import CompanyService


class CompanyForm(Screen):
    """Form for creating a new company."""

    def __init__(self, company_id: str = None, readonly: bool = False, on_saved: Optional[Callable] = None):
        """Initialize the form.

        Args:
            company_id: If provided, edit the existing company
            readonly: If True, display in read-only mode
            on_saved: Callback function to run after saving
        """
        super().__init__()
        self.company_id = company_id
        self.readonly = readonly
        self.on_saved = on_saved

    def compose(self) -> ComposeResult:
        """Compose the form layout."""
        with Container(id="company-form"):
            yield Label(
                "View Company" if self.readonly else
                "Edit Company" if self.company_id else
                "New Company",
                id="form-title"
            )

            with Vertical(id="form-fields"):
                yield Label("Company Name")
                yield Input(id="company-name", disabled=self.readonly)

                yield Label("Website")
                yield Input(id="website", disabled=self.readonly)

                yield Label("Industry")
                yield Input(id="industry", disabled=self.readonly)

                yield Label("Size")
                yield Input(id="size", disabled=self.readonly)

                yield Label("Notes")
                yield TextArea(id="notes", disabled=self.readonly)

            with Vertical(id="form-actions"):
                if not self.readonly:
                    yield Button("Save", variant="primary", id="save-company")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        """Load data when mounted."""
        if self.company_id:
            self.load_company()

    def load_company(self) -> None:
        """Load company data for editing."""
        try:
            service = CompanyService()
            company_data = service.get_company(int(self.company_id))

            if not company_data:
                self.app.sub_title = f"Company {self.company_id} not found"
                return

            # Populate form fields
            self.query_one("#company-name", Input).value = company_data["name"]

            if company_data.get("website"):
                self.query_one("#website", Input).value = company_data["website"]

            if company_data.get("industry"):
                self.query_one("#industry", Input).value = company_data["industry"]

            if company_data.get("size"):
                self.query_one("#size", Input).value = company_data["size"]

            if company_data.get("notes"):
                self.query_one("#notes", TextArea).text = company_data["notes"]

        except Exception as e:
            self.app.sub_title = f"Error loading company: {str(e)}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "save-company":
            self.save_company()

        elif button_id == "cancel":
            self.app.pop_screen()

    def save_company(self) -> None:
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

            service = CompanyService()

            if self.company_id:
                # Update existing company
                result = service.update_company(int(self.company_id), company_data)
                self.app.sub_title = "Company updated successfully"
            else:
                # Create new company
                result = service.create_company(company_data)
                self.app.sub_title = "Company created successfully"

            # Call the on_saved callback if provided
            if self.on_saved:
                self.on_saved()

            # Return to the previous screen
            self.app.pop_screen()

        except Exception as e:
            self.app.sub_title = f"Error saving company: {str(e)}"