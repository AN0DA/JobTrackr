from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Button, Label, Input, TextArea, Select
from datetime import datetime, timedelta

from src.services.interaction_service import InteractionService
from src.db.models import InteractionType


class InteractionForm(ModalScreen):
    """Form for creating or editing an interaction."""

    def __init__(self, interaction_id: int = None, application_id: int = None):
        """Initialize the form."""
        super().__init__()
        self.interaction_id = interaction_id
        self.application_id = application_id

    def compose(self) -> ComposeResult:
        with Container(id="interaction-form"):
            yield Label(
                "Edit Interaction" if self.interaction_id else "New Interaction",
                id="form-title",
            )

            with Vertical(id="form-fields"):
                yield Label("Interaction Type:", classes="field-label")
                yield Select(
                    [(itype.value, itype.value) for itype in InteractionType],
                    id="interaction-type",
                )

                yield Label("Date:", classes="field-label")
                yield Input(
                    placeholder="YYYY-MM-DD",
                    id="interaction-date",
                    value=datetime.now().strftime("%Y-%m-%d"),
                )

                yield Label("Notes:", classes="field-label")
                yield TextArea(id="interaction-notes")

                yield Label("Quick Date:", classes="field-label")
                with Horizontal():
                    yield Button("Today", id="date-today")
                    yield Button("Yesterday", id="date-yesterday")
                    yield Button("-2 Days", id="date-two-days-ago")
                    yield Button("-1 Week", id="date-week-ago")

            with Horizontal(id="form-actions"):
                yield Button("Cancel", id="cancel-interaction")
                yield Button("Save", id="save-interaction", variant="success")

    def on_mount(self) -> None:
        """Load interaction data if editing."""
        if self.interaction_id:
            self.load_interaction()

    def load_interaction(self) -> None:
        """Load interaction data for editing."""
        try:
            service = InteractionService()
            interaction = service.get_interaction(self.interaction_id)
            if not interaction:
                self.app.sub_title = f"Interaction {self.interaction_id} not found"
                return

            self.query_one("#interaction-type", Select).value = interaction["type"]

            # Format the date
            date = datetime.fromisoformat(interaction["date"]).strftime("%Y-%m-%d")
            self.query_one("#interaction-date", Input).value = date

            if interaction.get("notes"):
                self.query_one("#interaction-notes", TextArea).text = interaction[
                    "notes"
                ]

            # Store the application ID if it exists
            self.application_id = interaction.get("application_id")

        except Exception as e:
            self.app.sub_title = f"Error loading interaction: {str(e)}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "cancel-interaction":
            self.app.pop_screen()

        elif button_id == "save-interaction":
            self.save_interaction()

        # Quick date buttons
        elif button_id.startswith("date-"):
            date = datetime.now()

            if button_id == "date-today":
                # Today, keep as is
                pass
            elif button_id == "date-yesterday":
                date -= timedelta(days=1)
            elif button_id == "date-two-days-ago":
                date -= timedelta(days=2)
            elif button_id == "date-week-ago":
                date -= timedelta(days=7)

            # Update the date input
            self.query_one("#interaction-date", Input).value = date.strftime("%Y-%m-%d")

    def save_interaction(self) -> None:
        """Save the interaction."""
        try:
            interaction_type = self.query_one("#interaction-type", Select).value
            date = self.query_one("#interaction-date", Input).value
            notes = self.query_one("#interaction-notes", TextArea).text

            # Validate required fields
            if not interaction_type:
                self.app.sub_title = "Interaction type is required"
                return

            if not date:
                self.app.sub_title = "Date is required"
                return

            if not self.application_id:
                self.app.sub_title = "Application ID is required"
                return

            # Prepare data
            interaction_data = {
                "type": interaction_type,
                "date": date,
                "notes": notes or None,
                "application_id": self.application_id,
            }

            # Save interaction
            service = InteractionService()

            if self.interaction_id:
                service.update_interaction(self.interaction_id, interaction_data)
                self.app.sub_title = "Interaction updated successfully"
            else:
                service.create_interaction(interaction_data)
                self.app.sub_title = "Interaction created successfully"

            # Close the form
            self.app.pop_screen()

            # Refresh application detail if visible
            from src.tui.application_detail import ApplicationDetail

            detail_screen = self.app.screen
            if isinstance(detail_screen, ApplicationDetail):
                detail_screen.load_timeline()
                detail_screen.load_interactions()

        except Exception as e:
            self.app.sub_title = f"Error saving interaction: {str(e)}"
