from collections.abc import Callable

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select, TextArea

from src.services.company_service import CompanyService
from src.services.contact_service import ContactService


class ContactForm(Screen):
    """Form for creating or editing a contact."""

    def __init__(
        self,
        contact_id: str = None,
        readonly: bool = False,
        on_saved: Callable | None = None,
    ):
        """Initialize the form.

        Args:
            contact_id: If provided, edit the existing contact
            readonly: If True, display in read-only mode
            on_saved: Callback function to run after saving
        """
        super().__init__()
        self.contact_id = contact_id
        self.readonly = readonly
        self.on_saved = on_saved
        self.companies = []

    def compose(self) -> ComposeResult:
        """Compose the form layout."""
        with Container(id="app-form"):
            yield Label(
                "New Contact" if not self.contact_id else "Edit Contact",
                id="form-title",
            )

            with Container(id="contact-fields", classes="form-page"):
                with Vertical(id="contact-fields"):
                    yield Label("Name *", classes="field-label")
                    yield Input(id="contact-name", disabled=self.readonly)

                    yield Label("Title", classes="field-label")
                    yield Input(id="contact-title", disabled=self.readonly)

                    yield Label("Company", classes="field-label")
                    with Horizontal(id="company-field"):
                        yield Select([], id="company-select", disabled=self.readonly)
                        if not self.readonly:
                            yield Button("+ New", id="new-company", variant="primary")

                    # Contact information
                    yield Label("Email", classes="field-label")
                    yield Input(
                        id="contact-email",
                        placeholder="email@example.com",
                        disabled=self.readonly,
                    )

                    yield Label("Phone", classes="field-label")
                    yield Input(
                        id="contact-phone",
                        placeholder="(123) 456-7890",
                        disabled=self.readonly,
                    )

                    yield Label("Notes", classes="field-label")
                    yield TextArea(id="contact-notes", disabled=self.readonly)

            with Horizontal(id="form-actions"):
                if not self.readonly:
                    yield Button("Save", variant="primary", id="save-contact")
                yield Button("Close", id="close-form")

    def on_mount(self) -> None:
        """Load data when mounted."""
        self.load_companies()

        if self.contact_id:
            self.load_contact()

    def load_companies(self) -> None:
        """Load companies for the dropdown."""
        try:
            service = CompanyService()
            self.companies = service.get_companies()

            company_values = [(company["name"], str(company["id"])) for company in self.companies]
            company_values.append(("No Company", ""))

            company_select = self.query_one("#company-select", Select)
            company_select.set_options(company_values)

        except Exception as e:
            self.app.sub_title = f"Error loading companies: {str(e)}"

    def load_contact(self) -> None:
        """Load contact data for editing."""
        try:
            service = ContactService()
            contact_data = service.get_contact(int(self.contact_id))

            if not contact_data:
                self.app.sub_title = f"Contact {self.contact_id} not found"
                return

            # Populate form fields
            self.query_one("#contact-name", Input).value = contact_data["name"]

            if contact_data.get("title"):
                self.query_one("#contact-title", Input).value = contact_data["title"]

            if contact_data.get("email"):
                self.query_one("#contact-email", Input).value = contact_data["email"]

            if contact_data.get("phone"):
                self.query_one("#contact-phone", Input).value = contact_data["phone"]

            if contact_data.get("notes"):
                self.query_one("#contact-notes", TextArea).text = contact_data["notes"]

            # Set company if available
            company_select = self.query_one("#company-select", Select)
            if contact_data.get("company") and contact_data["company"].get("id"):
                # Convert company ID to string to match options format
                company_id_str = str(contact_data["company"]["id"])

                # Check if this value exists in the options
                valid_options = [option[1] for option in company_select.options]
                if company_id_str in valid_options:
                    company_select.value = company_id_str
                else:
                    # If company ID is not in options, just leave as default
                    self.app.sub_title = f"Warning: Company ID {company_id_str} not found in options"

        except Exception as e:
            self.app.sub_title = f"Error loading contact: {str(e)}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "save-contact":
            self.save_contact()

        elif button_id == "close-form":
            self.app.pop_screen()

        elif button_id == "new-company":
            from src.tui.tabs.companies.company_form import CompanyForm

            def refresh_companies() -> None:
                self.load_companies()

            self.app.push_screen(CompanyForm(on_saved=refresh_companies))

    def save_contact(self) -> None:
        """Save the contact data."""
        try:
            # Get values from form
            name = self.query_one("#contact-name", Input).value
            title = self.query_one("#contact-title", Input).value
            company_id = self.query_one("#company-select", Select).value or None
            email = self.query_one("#contact-email", Input).value
            phone = self.query_one("#contact-phone", Input).value
            notes = self.query_one("#contact-notes", TextArea).text

            # Validate required fields
            if not name:
                self.app.sub_title = "Contact name is required"
                return

            # Prepare data
            contact_data = {
                "name": name,
                "title": title or None,
                "company_id": int(company_id) if company_id else None,
                "email": email or None,
                "phone": phone or None,
                "notes": notes or None,
            }

            service = ContactService()

            if self.contact_id:
                # Update existing contact
                service.update_contact(int(self.contact_id), contact_data)
                self.app.sub_title = "Contact updated successfully"
            else:
                # Create new contact
                service.create_contact(contact_data)
                self.app.sub_title = "Contact created successfully"

            # Call the on_saved callback if provided
            if self.on_saved:
                self.on_saved()

            # Return to the previous screen
            self.app.pop_screen()

        except Exception as e:
            self.app.sub_title = f"Error saving contact: {str(e)}"
