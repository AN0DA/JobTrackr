"""Contacts management screen for the Job Tracker TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Input, Label, Select, Static

from src.services.company_service import CompanyService
from src.services.contact_service import ContactService
from src.tui.tabs.contacts.contact_detail import ContactDetailScreen
from src.tui.tabs.contacts.contact_form import ContactForm


class ContactsList(Static):
    """Contacts listing and management screen."""

    BINDINGS = [
        ("a", "add_contact", "Add Contact"),
        ("d", "delete_contact", "Delete"),
        ("e", "edit_contact", "Edit"),
        ("v", "view_contact", "View"),
        ("r", "refresh_contacts", "Refresh"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.sort_column = "Name"
        self.sort_ascending = True
        self.companies = []
        self.company_filter = None

    def compose(self) -> ComposeResult:
        """Compose the contacts screen layout."""
        with Container(classes="list-view-container"):
            # Header section
            with Container(classes="list-header"):
                yield Static("Contacts", classes="list-title")

                # Filter bar
                with Horizontal(classes="filter-bar"):
                    with Vertical(classes="filter-section"):
                        yield Static("Company:", classes="filter-label")
                        yield Select(id="company-filter", options=[], classes="filter-dropdown")

                    # Search section
                    with Horizontal(classes="search-section"):
                        yield Input(
                            placeholder="Search contacts...",
                            id="contact-search",
                            classes="search-box",
                        )
                        yield Button("🔍", id="search-button")

                    # Quick action buttons
                    with Horizontal(classes="action-section"):
                        yield Button("New Contact", variant="primary", id="new-contact")

            # Table section
            with Container(classes="table-container"):
                yield DataTable(id="contacts-table")

            # Footer section
            with Horizontal(classes="list-footer"):
                with Horizontal(classes="action-buttons"):
                    yield Button("View", id="view-contact", disabled=True)
                    yield Button("Edit", id="edit-contact", disabled=True)
                    yield Button("Delete", id="delete-contact", variant="error", disabled=True)

    def on_mount(self) -> None:
        """Set up the screen when mounted."""
        table = self.query_one("#contacts-table", DataTable)
        table.add_columns(
            "ID",
            "Name",
            "Title",
            "Company",
            "Email",
            "Phone",
        )
        table.cursor_type = "row"
        table.can_focus = True

        # Enable sorting
        table.sort_column_click = True

        # Load companies for filtering first, before trying to load contacts
        self.load_companies()

    def load_companies(self) -> None:
        """Load companies for filtering."""
        try:
            service = CompanyService()
            self.companies = service.get_companies()

            company_select = self.query_one("#company-filter", Select)
            company_select.clear()

            # Add "All" option first
            company_select.add_option("All Companies", "All")

            # Add companies
            for company in self.companies:
                company_select.add_option(company["name"], str(company["id"]))

            # Set default value after options are added
            company_select.value = "All"

            # Now load contacts after company filter is set up
            self.load_contacts()

        except Exception as e:
            self.update_status(f"Error loading companies: {str(e)}")

    def load_contacts(self, company_id: str = None) -> None:
        """Load contacts from the database."""
        self.update_status("Loading contacts...")

        try:
            service = ContactService()

            # Convert company_id to int if not None or "All"
            filter_company_id = None
            if company_id and company_id != "All":
                filter_company_id = int(company_id)

            contacts = service.get_contacts(company_id=filter_company_id)

            table = self.query_one("#contacts-table", DataTable)
            table.clear()

            # Convert to list for sorting
            contacts_list = list(contacts)

            # Apply current sort settings
            self._sort_contacts(contacts_list)

            for contact in contacts_list:
                table.add_row(
                    str(contact["id"]),
                    contact["name"],
                    contact.get("title", ""),
                    contact.get("company", {}).get("name", ""),
                    contact.get("email", ""),
                    contact.get("phone", ""),
                )

            self.update_status(f"Loaded {len(contacts)} contacts")
        except Exception as e:
            self.update_status(f"Error loading contacts: {str(e)}")

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle company filter changes."""
        if event.select.id == "company-filter":
            company_id = event.value
            self.company_filter = company_id
            self.load_contacts(company_id)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission."""
        if event.input.id == "contact-search":
            self.search_contacts(event.input.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        table = self.query_one("#contacts-table", DataTable)

        if button_id == "new-contact":
            self.app.push_screen(ContactForm(on_saved=self.load_contacts))

        elif button_id == "view-contact" and table.cursor_row is not None:
            contact_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(ContactDetailScreen(int(contact_id)))

        elif button_id == "edit-contact" and table.cursor_row is not None:
            contact_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(ContactForm(contact_id=contact_id, on_saved=self.load_contacts))

        elif button_id == "delete-contact" and table.cursor_row is not None:
            contact_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(DeleteConfirmationModal(contact_id, self.load_contacts))

        elif button_id == "search-button":
            search_term = self.query_one("#contact-search", Input).value
            self.search_contacts(search_term)

    def search_contacts(self, search_term: str) -> None:
        """Search contacts by name, email, or company."""
        if not search_term:
            self.load_contacts(self.company_filter)
            return

        self.update_status(f"Searching for '{search_term}'...")

        try:
            service = ContactService()
            results = service.search_contacts(search_term)

            # Apply company filter if active
            if self.company_filter and self.company_filter != "All":
                filter_id = int(self.company_filter)
                results = [c for c in results if c.get("company", {}).get("id") == filter_id]

            table = self.query_one("#contacts-table", DataTable)
            table.clear()

            for contact in results:
                table.add_row(
                    str(contact["id"]),
                    contact["name"],
                    contact.get("title", ""),
                    contact.get("company", {}).get("name", ""),
                    contact.get("email", ""),
                    contact.get("phone", ""),
                )

            self.update_status(f"Found {len(results)} contacts matching '{search_term}'")

        except Exception as e:
            self.update_status(f"Search error: {str(e)}")

    def update_status(self, message: str) -> None:
        """Update status message in the footer."""
        self.app.sub_title = message

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Enable buttons when a row is highlighted."""
        view_btn = self.query_one("#view-contact", Button)
        edit_btn = self.query_one("#edit-contact", Button)
        delete_btn = self.query_one("#delete-contact", Button)

        view_btn.disabled = False
        edit_btn.disabled = False
        delete_btn.disabled = False

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Open the contact detail view when a row is selected."""
        table = self.query_one("#contacts-table", DataTable)
        contact_id = table.get_row(event.row_key)[0]
        self.app.push_screen(ContactDetailScreen(int(contact_id)))

    def _sort_contacts(self, contacts):
        """Sort contacts based on current sort settings."""
        # Define sort keys for each column
        sort_keys = {
            "ID": lambda c: int(c["id"]),
            "Name": lambda c: c["name"].lower(),
            "Title": lambda c: (c.get("title") or "").lower(),
            "Company": lambda c: c.get("company", {}).get("name", "").lower(),
            "Email": lambda c: (c.get("email") or "").lower(),
            "Phone": lambda c: (c.get("phone") or "").lower(),
        }

        # Get sort key function
        sort_key = sort_keys.get(self.sort_column, lambda c: c["name"].lower())

        # Sort contacts
        contacts.sort(key=sort_key, reverse=not self.sort_ascending)

    def action_add_contact(self) -> None:
        """Open the contact creation form."""
        self.app.push_screen(ContactForm(on_saved=self.load_contacts))

    def action_delete_contact(self) -> None:
        """Delete the selected contact."""
        table = self.query_one("#contacts-table", DataTable)
        if table.cursor_row is not None:
            contact_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(DeleteConfirmationModal(contact_id, self.load_contacts))

    def action_edit_contact(self) -> None:
        """Edit the selected contact."""
        table = self.query_one("#contacts-table", DataTable)
        if table.cursor_row is not None:
            contact_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(ContactForm(contact_id=contact_id, on_saved=self.load_contacts))

    def action_view_contact(self) -> None:
        """View the selected contact."""
        table = self.query_one("#contacts-table", DataTable)
        if table.cursor_row is not None:
            contact_id = table.get_row_at(table.cursor_row)[0]
            self.app.push_screen(ContactDetailScreen(int(contact_id)))

    def action_refresh_contacts(self) -> None:
        """Refresh the contacts list."""
        self.load_contacts(self.company_filter)


class DeleteConfirmationModal(ModalScreen):
    """Confirmation dialog for deleting contacts."""

    def __init__(self, contact_id: str, on_delete=None):
        super().__init__()
        self.contact_id = contact_id
        self.on_delete = on_delete

    def compose(self) -> ComposeResult:
        yield Container(
            Label(f"Are you sure you want to delete contact #{self.contact_id}?"),
            Label(
                "This will permanently remove the contact from the database.",
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
            self.delete_contact()

    def delete_contact(self) -> None:
        try:
            service = ContactService()
            success = service.delete_contact(int(self.contact_id))

            if success:
                self.app.sub_title = f"Successfully deleted contact #{self.contact_id}"
            else:
                self.app.sub_title = f"Contact #{self.contact_id} not found"

            self.app.pop_screen()

            # Run callback after deletion
            if self.on_delete:
                self.on_delete()

        except Exception as e:
            self.app.sub_title = f"Error deleting contact: {str(e)}"
            self.app.pop_screen()
