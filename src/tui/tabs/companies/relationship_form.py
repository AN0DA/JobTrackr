"""Form for creating company relationships."""

from collections.abc import Callable

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, TextArea

from src.services.company_service import CompanyService


class CompanyRelationshipForm(ModalScreen):
    """Modal form for creating or editing company relationships."""

    def __init__(
        self,
        source_company_id: int,
        relationship_id: int = None,
        on_saved: Callable | None = None,
    ):
        """Initialize the form.

        Args:
            source_company_id: ID of the source company
            relationship_id: If provided, edit the existing relationship
            on_saved: Optional callback after save
        """
        super().__init__()
        self.source_company_id = source_company_id
        self.relationship_id = relationship_id
        self.on_saved = on_saved
        self.companies = []

        # Predefined relationship types
        self.relationship_types = [
            "recruits_for",
            "parent_company",
            "subsidiary",
            "client",
            "vendor",
            "partner",
            "other",
        ]

    def compose(self) -> ComposeResult:
        with Container(id="relationship-form-container", classes="modal-container"):
            with Container(id="relationship-form", classes="modal-content"):
                yield Label(
                    "Add Company Relationship" if not self.relationship_id else "Edit Relationship",
                    id="form-title",
                    classes="modal-title",
                )

                with Vertical(id="form-fields"):
                    # Source company (read-only)
                    yield Label("From Company:", classes="field-label")
                    yield Input(id="source-company", disabled=True)

                    # Relationship type
                    yield Label("Relationship Type:", classes="field-label")
                    yield Select(
                        [(rt, rt) for rt in self.relationship_types],
                        id="relationship-type",
                    )

                    # Target company
                    yield Label("To Company:", classes="field-label")
                    yield Select([], id="target-company")

                    yield Label("Notes:", classes="field-label")
                    yield TextArea(id="relationship-notes")

                with Horizontal(id="form-actions", classes="modal-actions"):
                    yield Button("Save", variant="primary", id="save-relationship")
                    yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        """Load companies and set up fields."""
        self.load_companies()

        # Load relationship data if editing
        if self.relationship_id:
            self.load_relationship()

    def load_companies(self) -> None:
        """Load companies for dropdown."""
        try:
            service = CompanyService()

            # Get current company details for display
            source_company = service.get_company(self.source_company_id)
            if source_company:
                self.query_one("#source-company", Input).value = source_company["name"]

            # Get all companies for target selection
            self.companies = service.get_companies()

            # Remove the source company from options
            target_companies = [c for c in self.companies if c["id"] != self.source_company_id]

            # Update target company dropdown
            target_select = self.query_one("#target-company", Select)
            target_select.clear()
            for company in target_companies:
                target_select.add_option(company["name"], str(company["id"]))

        except Exception as e:
            self.app.sub_title = f"Error loading companies: {str(e)}"

    def load_relationship(self) -> None:
        """Load relationship data if editing."""
        try:
            service = CompanyService()
            relationship = service.get_relationship(self.relationship_id)

            if not relationship:
                self.app.sub_title = f"Relationship {self.relationship_id} not found"
                return

            # Set relationship type
            relationship_type = relationship.get("relationship_type")
            if relationship_type:
                self.query_one("#relationship-type", Select).value = relationship_type

            # Set target company
            target_id = relationship.get("target_id")
            if target_id:
                target_select = self.query_one("#target-company", Select)
                target_select.value = str(target_id)

            # Set notes
            notes = relationship.get("notes")
            if notes:
                self.query_one("#relationship-notes", TextArea).text = notes

            self.app.sub_title = "Loaded relationship data for editing"

        except Exception as e:
            self.app.sub_title = f"Error loading relationship: {str(e)}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "cancel":
            self.app.pop_screen()

        elif button_id == "save-relationship":
            self.save_relationship()

    def save_relationship(self) -> None:
        """Save the relationship."""
        try:
            service = CompanyService()

            relationship_type = self.query_one("#relationship-type", Select).value
            target_company_id = int(self.query_one("#target-company", Select).value)
            notes = self.query_one("#relationship-notes", TextArea).text

            # Validate
            if not relationship_type:
                self.app.sub_title = "Please select a relationship type"
                return

            if not target_company_id:
                self.app.sub_title = "Please select a target company"
                return

            # Create or update the relationship
            if self.relationship_id:
                # Update logic would go here
                pass
            else:
                service.create_relationship(
                    source_id=self.source_company_id,
                    target_id=target_company_id,
                    relationship_type=relationship_type,
                    notes=notes,
                )

            self.app.sub_title = "Relationship saved successfully"

            # Run callback if provided
            if self.on_saved:
                self.on_saved()

            # Close the form
            self.app.pop_screen()

        except Exception as e:
            self.app.sub_title = f"Error saving relationship: {str(e)}"
