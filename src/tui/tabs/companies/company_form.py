"""Form for creating/editing companies."""

from collections.abc import Callable

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select, TextArea

from src.db.models import CompanyType
from src.services.company_service import CompanyService


class CompanyForm(Screen):
    """Form for creating a new company."""

    def __init__(
        self,
        company_id: str = None,
        readonly: bool = False,
        on_saved: Callable | None = None,
    ):
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
        with Container(id="app-form"):
            yield Label(
                "New Company" if not self.company_id else "Edit Company",
                id="form-title",
            )

            with Container(id="contact-fields", classes="form-page"):
                with Vertical(id="contact-fields"):
                    yield Label("Company Name *", classes="field-label")
                    yield Input(id="company-name", disabled=self.readonly)

                    yield Label("Website", classes="field-label")
                    yield Input(id="website", disabled=self.readonly)

                    # Additional information
                    yield Label("Company Type", classes="field-label")
                    yield Select(
                        [(ct.value, ct.value) for ct in CompanyType],
                        id="company-type",
                        disabled=self.readonly,
                        value=CompanyType.DIRECT_EMPLOYER.value,
                    )

                    yield Label("Industry", classes="field-label")
                    yield Input(id="industry", disabled=self.readonly)

                    yield Label("Size", classes="field-label")
                    yield Input(
                        id="size",
                        placeholder="e.g. 1-50, 51-200, 201-500, etc.",
                        disabled=self.readonly,
                    )

                    yield Label("Notes", classes="field-label")
                    yield TextArea(id="notes", disabled=self.readonly)

            with Horizontal(id="form-actions"):
                if not self.readonly:
                    yield Button("Save", variant="primary", id="save-company")
                yield Button("Close", id="close-form")

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

            if company_data.get("company_type"):
                self.query_one("#company-type", Select).value = company_data["company_type"]

            if company_data.get("notes"):
                self.query_one("#notes", TextArea).text = company_data["notes"]

        except Exception as e:
            self.app.sub_title = f"Error loading company: {str(e)}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "save-company":
            self.save_company()

        elif button_id == "close-form":
            self.app.pop_screen()

    def save_company(self) -> None:
        """Save the company data."""
        try:
            # Get values from form
            name = self.query_one("#company-name", Input).value
            website = self.query_one("#website", Input).value
            industry = self.query_one("#industry", Input).value
            size = self.query_one("#size", Input).value
            company_type = self.query_one("#company-type", Select).value
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
                "company_type": company_type,
                "notes": notes or None,
            }

            service = CompanyService()

            if self.company_id:
                # Update existing company
                service.update_company(int(self.company_id), company_data)
                self.app.sub_title = "Company updated successfully"
            else:
                # Create new company
                service.create_company(company_data)
                self.app.sub_title = "Company created successfully"

            # Call the on_saved callback if provided
            if self.on_saved:
                self.on_saved()

            # Return to the previous screen
            self.app.pop_screen()

        except Exception as e:
            self.app.sub_title = f"Error saving company: {str(e)}"
