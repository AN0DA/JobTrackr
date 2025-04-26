"""Context menu for applications."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Vertical
from textual.widgets import Button, Label


class ApplicationContextMenu(ModalScreen):
    """Context menu for application actions."""

    def __init__(self, application_id, application_title, status):
        super().__init__()
        self.application_id = application_id
        self.application_title = application_title
        self.status = status

    def compose(self) -> ComposeResult:
        with Container(id="context-menu"):
            yield Label(f"{self.application_title}", id="menu-title")

            with Vertical(id="menu-actions"):
                # Status transitions based on current status
                if self.status == "SAVED":
                    yield Button(
                        "➤ Mark as APPLIED", variant="primary", id="change-to-applied"
                    )

                elif self.status == "APPLIED":
                    yield Button(
                        "➤ Got PHONE SCREEN", variant="primary", id="change-to-phone"
                    )
                    yield Button(
                        "➤ Got INTERVIEW", variant="primary", id="change-to-interview"
                    )
                    yield Button(
                        "➤ Mark as REJECTED", variant="error", id="change-to-rejected"
                    )

                elif self.status in [
                    "PHONE_SCREEN",
                    "INTERVIEW",
                    "TECHNICAL_INTERVIEW",
                ]:
                    yield Button(
                        "➤ Next Interview Stage",
                        variant="primary",
                        id="change-to-next-interview",
                    )
                    yield Button(
                        "➤ Got an OFFER", variant="success", id="change-to-offer"
                    )
                    yield Button(
                        "➤ Mark as REJECTED", variant="error", id="change-to-rejected"
                    )

                elif self.status == "OFFER":
                    yield Button(
                        "➤ Mark as ACCEPTED", variant="success", id="change-to-accepted"
                    )
                    yield Button(
                        "➤ Mark as REJECTED", variant="error", id="change-to-rejected"
                    )
                    yield Button(
                        "➤ Mark as WITHDRAWN",
                        variant="warning",
                        id="change-to-withdrawn",
                    )

                # Common actions for all statuses
                yield Button("Change Status...", id="change-status")
                yield Label("─" * 30, classes="menu-divider")
                yield Button("View Details", id="view-details")
                yield Button("View Detailed Timeline", id="view-details-timeline")
                yield Button("Edit Application", id="edit-application")
                yield Label("─" * 30, classes="menu-divider")
                yield Button(
                    "Delete Application", variant="error", id="delete-application"
                )
                yield Label("─" * 30, classes="menu-divider")
                yield Button("Close Menu", id="close-menu")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        # Close the menu
        if button_id == "close-menu":
            self.app.pop_screen()
            return

        # Status transitions
        if button_id.startswith("change-to-"):
            # Remove the menu first
            self.app.pop_screen()

            # Get the new status from the button ID
            new_status = None
            if button_id == "change-to-applied":
                new_status = "APPLIED"
            elif button_id == "change-to-phone":
                new_status = "PHONE_SCREEN"
            elif button_id == "change-to-interview":
                new_status = "INTERVIEW"
            elif button_id == "change-to-next-interview":
                if self.status == "PHONE_SCREEN":
                    new_status = "INTERVIEW"
                elif self.status == "INTERVIEW":
                    new_status = "TECHNICAL_INTERVIEW"
            elif button_id == "change-to-offer":
                new_status = "OFFER"
            elif button_id == "change-to-accepted":
                new_status = "ACCEPTED"
            elif button_id == "change-to-rejected":
                new_status = "REJECTED"
            elif button_id == "change-to-withdrawn":
                new_status = "WITHDRAWN"

            # If a specific status was selected, update directly
            if new_status:
                from src.services.application_service import ApplicationService

                service = ApplicationService()
                try:
                    service.update_application(
                        self.application_id, {"status": new_status}
                    )
                    self.app.sub_title = f"Status updated to {new_status}"

                    # Refresh applications list if visible
                    from src.tui.tabs.applications.applications import ApplicationsList

                    app_list = self.app.query_one(ApplicationsList)
                    if app_list:
                        app_list.load_applications()
                except Exception as e:
                    self.app.sub_title = f"Error updating status: {str(e)}"
                return

        # Other actions
        self.app.pop_screen()

        if button_id == "change-status":
            from src.tui.tabs.applications.status_transition import (
                StatusTransitionDialog,
            )

            self.app.push_screen(
                StatusTransitionDialog(self.application_id, self.status)
            )

        elif button_id == "view-details":
            from src.tui.tabs.applications.application_form import ApplicationForm

            self.app.push_screen(
                ApplicationForm(app_id=self.application_id, readonly=True)
            )

        elif button_id == "edit-application":
            from src.tui.tabs.applications.application_form import ApplicationForm

            self.app.push_screen(ApplicationForm(app_id=self.application_id))

        elif button_id == "delete-application":
            from src.tui.tabs.applications.applications import DeleteConfirmationModal

            self.app.push_screen(DeleteConfirmationModal(self.application_id))

        elif button_id == "view-details-timeline":
            from src.tui.tabs.applications.application_detail import ApplicationDetail

            self.app.pop_screen()  # Close menu
            self.app.push_screen(ApplicationDetail(int(self.application_id)))
