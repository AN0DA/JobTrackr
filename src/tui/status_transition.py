"""Dialog for transitioning application status."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Button, Label, Select, TextArea

from datetime import datetime, timedelta
from src.services.application_service import ApplicationService
from src.db.models import ApplicationStatus


class StatusTransitionDialog(ModalScreen):
    """Modal dialog for changing application status."""

    def __init__(self, application_id, current_status):
        super().__init__()
        self.application_id = application_id
        self.current_status = current_status

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

                yield Label("Create Reminder:", classes="field-label")
                with Horizontal(id="reminder-container"):
                    yield Button(
                        "+ Tomorrow", id="reminder-tomorrow", variant="primary"
                    )
                    yield Button(
                        "+ 3 Days", id="reminder-three-days", variant="primary"
                    )
                    yield Button("+ 1 Week", id="reminder-week", variant="primary")
                    yield Button(
                        "+ 2 Weeks", id="reminder-two-weeks", variant="primary"
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

        elif button_id.startswith("reminder-"):
            # Set a reminder date
            reminder_date = datetime.now()

            if button_id == "reminder-tomorrow":
                reminder_date += timedelta(days=1)
            elif button_id == "reminder-three-days":
                reminder_date += timedelta(days=3)
            elif button_id == "reminder-week":
                reminder_date += timedelta(days=7)
            elif button_id == "reminder-two-weeks":
                reminder_date += timedelta(days=14)

            # Highlight the button to show it was selected
            for btn in self.query(Button):
                if btn.id.startswith("reminder-"):
                    btn.variant = "primary"
            event.button.variant = "success"

            # Store the reminder date for later use
            self.reminder_date = reminder_date

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
            service.update_application(self.application_id, {"status": new_status})

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

            # Add reminder if one was selected
            if hasattr(self, "reminder_date"):
                from src.services.reminder_service import ReminderService

                reminder_service = ReminderService()

                # Create different reminder messages based on status
                if new_status == "APPLIED":
                    title = "Follow up on application"
                elif new_status == "INTERVIEW" or new_status == "PHONE_SCREEN":
                    title = "Prepare for interview"
                elif new_status == "OFFER":
                    title = "Review offer details"
                else:
                    title = f"Follow up ({new_status})"

                reminder_service.create_reminder(
                    {
                        "title": title,
                        "description": f"Follow up on application (previous status: {new_status})",
                        "date": self.reminder_date.isoformat(),
                        "completed": False,
                        "application_id": self.application_id,
                    }
                )

            self.app.sub_title = f"Status updated to {new_status}"
            self.app.pop_screen()

            # Refresh applications list if visible
            from src.tui.applications import ApplicationsList

            app_list = self.app.query_one(ApplicationsList)
            if app_list:
                app_list.load_applications()

        except Exception as e:
            self.app.sub_title = f"Error updating status: {str(e)}"
