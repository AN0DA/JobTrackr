from collections.abc import Callable
from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Select, TextArea

from src.config import ApplicationStatus
from src.services.application_service import ApplicationService


class StatusTransitionDialog(ModalScreen):
    """Modal dialog for changing application status."""

    def __init__(self, application_id: int, current_status: str, on_updated: Callable | None = None):
        """Initialize status transition dialog.

        Args:
            application_id: ID of the application to modify
            current_status: Current status of the application
            on_updated: Callback function to run when status is updated
        """
        super().__init__()
        self.application_id = application_id
        self.current_status = current_status
        self.on_updated = on_updated

    def compose(self) -> ComposeResult:
        with Container(id="transition-dialog"):
            yield Label(
                f"Change Status for Application #{self.application_id}",
                id="dialog-title",
            )

            with Vertical(id="transition-form"):
                yield Label("Current Status:", classes="field-label")
                yield Label(self.current_status, id="current-status")

                yield Label("New Status:", classes="field-label")
                yield Select(
                    [(status.value, status.value) for status in ApplicationStatus],
                    id="new-status",
                    value=self.current_status,
                )

                yield Label("Add Note:", classes="field-label")
                yield TextArea(
                    id="status-note",
                    tooltip="Optional note about this status change",
                )

            with Horizontal(id="dialog-buttons"):
                yield Button("Cancel", id="cancel-transition")
                yield Button("Save", id="save-transition", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "cancel-transition":
            self.app.pop_screen()
            return

        elif button_id == "save-transition":
            self.save_status_change()

    def save_status_change(self) -> None:
        """Save the status change."""
        try:
            new_status = self.query_one("#new-status", Select).value
            note = self.query_one("#status-note", TextArea).text

            if new_status == self.current_status:
                self.app.sub_title = "Status unchanged"
                self.app.pop_screen()
                return

            # Update application status
            service = ApplicationService()
            service.update(self.application_id, {"status": new_status})

            # Create interaction record for the status change
            if note:
                service.add_interaction(
                    {
                        "application_id": self.application_id,
                        "type": "NOTE",
                        "notes": f"Status changed from {self.current_status} to {new_status}. Note: {note}",
                        "date": datetime.now().isoformat(),
                    }
                )

            self.app.sub_title = f"Status updated to {new_status}"

            # Call the on_updated callback if provided
            if self.on_updated:
                self.on_updated()

            self.app.pop_screen()

        except Exception as e:
            self.app.sub_title = f"Error updating status: {str(e)}"
