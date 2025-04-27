from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Header, Label, Static

from src.services.contact_service import ContactService


class ContactDetailScreen(Screen):
    """Screen for viewing details about a contact."""

    def __init__(self, contact_id: int):
        super().__init__()
        self.contact_id = contact_id
        self.contact_data = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="contact-detail"):
            with Horizontal(id="contact-header"):
                with Vertical(id="contact-identity"):
                    yield Static("", id="contact-name", classes="contact-title")
                    yield Static("", id="contact-title", classes="contact-subtitle")

                with Vertical(id="header-actions"):
                    yield Button("Edit Contact", id="edit-contact")

            # Contact information grid
            with Grid(id="contact-info-grid", classes="info-grid"):
                yield Label("Company:", classes="field-label")
                yield Static("", id="contact-company", classes="field-value")

                yield Label("Email:", classes="field-label")
                yield Static("", id="contact-email", classes="field-value")

                yield Label("Phone:", classes="field-label")
                yield Static("", id="contact-phone", classes="field-value")

            yield Label("Notes:", classes="section-label")
            with Container(id="notes-container", classes="notes-box"):
                yield Static("", id="contact-notes")

            # Related applications
            yield Label("Associated Applications", classes="section-label")
            yield DataTable(id="contact-details-applications-table")

            # Related interactions
            yield Label("Recent Interactions", classes="section-label")
            yield DataTable(id="contact-details-interactions-table")

            with Horizontal(id="contact-detail-actions"):
                yield Button("Back", id="back-button", variant="default")
                yield Button("Add to Application", id="add-to-application", variant="primary")

    def on_mount(self) -> None:
        """Load contact data when the screen is mounted."""
        # Set up tables
        applications_table = self.query_one("#contact-details-applications-table", DataTable)
        applications_table.add_columns("ID", "Job Title", "Position", "Status", "Applied Date")
        applications_table.cursor_type = "row"

        interactions_table = self.query_one("#contact-details-interactions-table", DataTable)
        interactions_table.add_columns("Date", "Type", "Application", "Details")
        interactions_table.cursor_type = "row"

        # Load contact data
        self.load_contact_data()

    def load_contact_data(self) -> None:
        """Load all contact data and populate the UI."""
        try:
            # Load contact details
            service = ContactService()
            self.contact_data = service.get_contact(self.contact_id)

            if not self.contact_data:
                self.app.sub_title = f"Contact {self.contact_id} not found"
                return

            # Update header
            self.query_one("#contact-name", Static).update(self.contact_data.get("name", "Unknown"))

            # Make sure title is a string
            title = self.contact_data.get("title", "")
            if title is None:
                title = "No title"
            self.query_one("#contact-title", Static).update(title)

            # Update fields - ensure we always use strings for display
            company = self.contact_data.get("company", {})
            company_name = company.get("name", "") if company else ""
            if not company_name:
                company_name = "Not associated with a company"
            self.query_one("#contact-company", Static).update(company_name)

            email = self.contact_data.get("email", "")
            if email is None or email == "":
                email = "No email provided"
            self.query_one("#contact-email", Static).update(email)

            phone = self.contact_data.get("phone", "")
            if phone is None or phone == "":
                phone = "No phone provided"
            self.query_one("#contact-phone", Static).update(phone)

            # Update notes
            notes = self.contact_data.get("notes", "")
            if notes is None or notes == "":
                notes = "No notes available."
            self.query_one("#contact-notes", Static).update(notes)

            # Load applications (placeholder - would need to implement in service)
            self.load_applications()

            # Load interactions (placeholder - would need to implement in service)
            self.load_interactions()

            self.app.sub_title = f"Viewing contact: {self.contact_data.get('name', 'Unknown')}"

        except Exception as e:
            self.app.sub_title = f"Error loading contact data: {str(e)}"

    def load_applications(self) -> None:
        """Load applications associated with this contact."""
        table = self.query_one("#contact-details-applications-table", DataTable)
        table.clear()

        if not self.contact_data or not self.contact_data.get("applications"):
            table.add_row("No applications found", "", "", "", "")
            return

        applications = self.contact_data.get("applications", [])

        if not applications:
            table.add_row("No applications found", "", "", "", "")
            return

        for app in applications:
            table.add_row(
                str(app["id"]),
                app["job_title"],
                app["position"],
                app["status"],
                app.get("applied_date", ""),
            )

    def load_interactions(self) -> None:
        """Load interactions associated with this contact."""
        table = self.query_one("#contact-details-interactions-table", DataTable)
        table.clear()

        # This would require an actual method in the service to get interactions by contact
        # For now, display placeholder
        table.add_row("No interactions found", "", "", "")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "back-button":
            self.app.pop_screen()

        elif button_id == "edit-contact":
            from src.tui.tabs.contacts.contact_form import ContactForm

            def refresh_after_edit() -> None:
                self.load_contact_data()

            self.app.push_screen(ContactForm(contact_id=str(self.contact_id), on_saved=refresh_after_edit))

        elif button_id == "add-to-application":
            # This would open a dialog to add the contact to an application
            # Not implemented in this example
            self.app.sub_title = "This feature is not yet implemented"
