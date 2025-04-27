from collections.abc import Callable

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class ConfirmationModal(ModalScreen):
    """Reusable confirmation dialog."""

    def __init__(
        self,
        title: str,
        message: str,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        on_confirm: Callable | None = None,
        on_cancel: Callable | None = None,
        dangerous: bool = False,
    ):
        """Initialize the confirmation dialog.

        Args:
            title: The title of the dialog
            message: The message to display
            confirm_text: Text for the confirm button
            cancel_text: Text for the cancel button
            on_confirm: Callback to run when confirmed
            on_cancel: Callback to run when canceled
            dangerous: Whether this is a dangerous action (changes button styling)
        """
        super().__init__()
        self.title_text = title
        self.message = message
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.dangerous = dangerous

    def compose(self) -> ComposeResult:
        """Compose the dialog layout."""
        with Container(id="confirmation-modal"):
            yield Static(self.title_text, id="modal-title")
            yield Label(self.message, id="modal-message")

            with Horizontal(id="modal-buttons"):
                yield Button(self.cancel_text, id="cancel-button", variant="primary")

                # Use different styling for dangerous actions
                if self.dangerous:
                    yield Button(self.confirm_text, id="confirm-button", variant="error")
                else:
                    yield Button(self.confirm_text, id="confirm-button", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "cancel-button":
            if self.on_cancel:
                self.on_cancel()
            self.app.pop_screen()

        elif button_id == "confirm-button":
            if self.on_confirm:
                self.on_confirm()
            self.app.pop_screen()
