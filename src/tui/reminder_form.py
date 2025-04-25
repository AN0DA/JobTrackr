"""Form for creating reminders."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Button, Label, Input, TextArea
from datetime import datetime, timedelta

from src.services.reminder_service import ReminderService


class ReminderForm(ModalScreen):
    """Form for creating a reminder."""

    def __init__(self, reminder_id: int = None, application_id: int = None):
        super().__init__()
        self.reminder_id = reminder_id
        self.application_id = application_id

    def compose(self) -> ComposeResult:
        with Container(id="reminder-form-dialog"):
            yield Label(
                "Edit Reminder" if self.reminder_id else "New Reminder",
                id="dialog-title",
            )

            with Vertical(id="reminder-form"):
                yield Label("Title:", classes="field-label")
                yield Input(id="reminder-title")

                yield Label("Description:", classes="field-label")
                yield TextArea(id="reminder-description")

                yield Label("Date:", classes="field-label")
                yield Input(
                    placeholder="YYYY-MM-DD",
                    id="reminder-date",
                    value=datetime.now().strftime("%Y-%m-%d"),
                )

                yield Label("Quick Date:", classes="field-label")
                with Horizontal():
                    yield Button("Today", id="date-today")
                    yield Button("Tomorrow", id="date-tomorrow")
                    yield Button("+3 Days", id="date-three-days")
                    yield Button("+1 Week", id="date-week")

            with Horizontal(id="dialog-buttons"):
                yield Button("Cancel", id="cancel-reminder")
                yield Button("Save", id="save-reminder", variant="success")

    def on_mount(self) -> None:
        """Load reminder data if editing."""
        if self.reminder_id:
            self.load_reminder()

    def load_reminder(self) -> None:
        """Load reminder data for editing."""
        try:
            service = ReminderService()
            reminder = service.get_reminder(self.reminder_id)
            if not reminder:
                self.app.sub_title = f"Reminder {self.reminder_id} not found"
                return

            self.query_one("#reminder-title", Input).value = reminder["title"]

            if reminder.get("description"):
                self.query_one("#reminder-description", TextArea).text = reminder[
                    "description"
                ]

            # Format the date
            date = datetime.fromisoformat(reminder["date"]).strftime("%Y-%m-%d")
            self.query_one("#reminder-date", Input).value = date

            # Store the application ID if it exists
            self.application_id = reminder.get("application_id")

        except Exception as e:
            self.app.sub_title = f"Error loading reminder: {str(e)}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "cancel-reminder":
            self.app.pop_screen()

        elif button_id == "save-reminder":
            self.save_reminder()

        # Quick date buttons
        elif button_id.startswith("date-"):
            date = datetime.now()

            if button_id == "date-today":
                # Today, keep as is
                pass
            elif button_id == "date-tomorrow":
                date += timedelta(days=1)
            elif button_id == "date-three-days":
                date += timedelta(days=3)
            elif button_id == "date-week":
                date += timedelta(days=7)

            # Update the date input
            self.query_one("#reminder-date", Input).value = date.strftime("%Y-%m-%d")

    def save_reminder(self) -> None:
        """Save the reminder."""
        try:
            title = self.query_one("#reminder-title", Input).value
            description = self.query_one("#reminder-description", TextArea).text
            date = self.query_one("#reminder-date", Input).value

            # Validate required fields
            if not title:
                self.app.sub_title = "Title is required"
                return

            if not date:
                self.app.sub_title = "Date is required"
                return

            # Prepare data
            reminder_data = {
                "title": title,
                "description": description or None,
                "date": date,
                "completed": False,
                "application_id": self.application_id,
            }

            # Save reminder
            service = ReminderService()

            if self.reminder_id:
                service.update_reminder(self.reminder_id, reminder_data)
                self.app.sub_title = "Reminder updated successfully"
            else:
                service.create_reminder(reminder_data)
                self.app.sub_title = "Reminder created successfully"

            # Close the form
            self.app.pop_screen()

            # Refresh dashboard if visible
            from src.tui.dashboard import Dashboard

            dashboard = self.app.query_one(Dashboard)
            if dashboard:
                dashboard.refresh_data()

        except Exception as e:
            self.app.sub_title = f"Error saving reminder: {str(e)}"
