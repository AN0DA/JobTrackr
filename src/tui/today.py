"""Today view showing upcoming tasks and recent activity."""
import logging

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Grid
from textual.widgets import Static, DataTable, Label
from datetime import datetime, timedelta

from src.services.application_service import ApplicationService
from src.services.reminder_service import ReminderService

logger = logging.getLogger(__name__)

class TodayView(Static):
    """Today view with upcoming tasks and recent activity."""

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Today", id="today-title")

            # Date display
            yield Label(datetime.now().strftime("%A, %B %d, %Y"), id="today-date")

            # Upcoming reminders
            with Vertical(id="upcoming-section"):
                yield Static("Upcoming Reminders", classes="section-title")
                yield DataTable(id="reminders-table")

            # Recent applications
            with Vertical(id="recent-section"):
                yield Static("Recent Applications", classes="section-title")
                yield DataTable(id="recent-table")

            # Status summary
            with Grid(id="status-summary-grid"):
                yield Static("Applications by Status", classes="section-title", id="status-summary-title")
                yield DataTable(id="status-table")

            # Upcoming deadlines
            with Vertical(id="deadlines-section"):
                yield Static("Action Items", classes="section-title")
                yield DataTable(id="deadlines-table")

    def on_mount(self) -> None:
        """Set up tables and load data."""
        # Configure reminders table
        reminders = self.query_one("#reminders-table", DataTable)
        reminders.add_columns("Due", "Title", "Application", "Actions")
        reminders.cursor_type = "row"

        # Configure recent applications table
        recent = self.query_one("#recent-table", DataTable)
        recent.add_columns("Applied", "Job Title", "Company", "Status")
        recent.cursor_type = "row"

        # Configure status table
        status = self.query_one("#status-table", DataTable)
        status.add_columns("Status", "Count", "Last Updated")

        # Configure deadlines table
        deadlines = self.query_one("#deadlines-table", DataTable)
        deadlines.add_columns("Type", "Details", "Due Date", "Priority")

        # Load data
        self.load_today_data()

    def load_today_data(self) -> None:
        """Load data for the today view."""
        try:
            # Load reminders
            reminder_service = ReminderService()
            upcoming_reminders = reminder_service.get_reminders(completed=False)

            reminders_table = self.query_one("#reminders-table", DataTable)
            reminders_table.clear()

            for reminder in sorted(upcoming_reminders, key=lambda x: datetime.fromisoformat(x["date"])):
                due_date = datetime.fromisoformat(reminder["date"])
                due_str = "Today!" if due_date.date() == datetime.now().date() else due_date.strftime("%Y-%m-%d")

                app_service = ApplicationService()
                app_info = ""
                if reminder["application_id"]:
                    app = app_service.get_application(reminder["application_id"])
                    if app:
                        app_info = f"{app['job_title']} at {app.get('company', {}).get('name', '')}"

                reminders_table.add_row(
                    due_str,
                    reminder["title"],
                    app_info,
                    "Mark Complete"  # This would be a button in a more advanced implementation
                )

            # Load recent applications
            app_service = ApplicationService()
            recent_apps = app_service.get_applications(limit=10)

            recent_table = self.query_one("#recent-table", DataTable)
            recent_table.clear()

            for app in recent_apps:
                applied_date = datetime.fromisoformat(app["applied_date"])
                days_ago = (datetime.now().date() - applied_date.date()).days

                if days_ago == 0:
                    date_str = "Today"
                elif days_ago == 1:
                    date_str = "Yesterday"
                else:
                    date_str = f"{days_ago} days ago"

                recent_table.add_row(
                    date_str,
                    app["job_title"],
                    app.get("company", {}).get("name", ""),
                    app["status"]
                )

            # Load status summary
            stats = app_service.get_dashboard_stats()

            status_table = self.query_one("#status-table", DataTable)
            status_table.clear()

            for status_count in stats["applications_by_status"]:
                status_table.add_row(
                    status_count["status"],
                    str(status_count["count"]),
                    "N/A"  # Would show last updated date in full implementation
                )

            # Create action items
            deadlines_table = self.query_one("#deadlines-table", DataTable)
            deadlines_table.clear()

            # Add action items based on status
            self._add_action_items(deadlines_table, app_service, stats)

            self.app.sub_title = "Today view refreshed"

        except Exception as e:
            self.app.sub_title = f"Error loading today view: {str(e)}"

    def _add_action_items(self, table, service, stats):
        """Add action items to the deadlines table."""
        # Check for applications that need follow-up
        try:
            # Find applications in APPLIED status older than 2 weeks
            apps = service.get_applications(status="APPLIED")
            two_weeks_ago = datetime.now() - timedelta(days=14)

            for app in apps:
                applied_date = datetime.fromisoformat(app["applied_date"])
                if applied_date < two_weeks_ago:
                    table.add_row(
                        "Follow-up",
                        f"{app['job_title']} at {app.get('company', {}).get('name', '')}",
                        applied_date.strftime("%Y-%m-%d"),
                        "High"
                    )

            # Add recommendation to apply to more jobs if few active applications
            active_apps = sum(count for status, count in ((status_count["status"], status_count["count"])
                                                          for status_count in stats["applications_by_status"])
                              if status not in ["REJECTED", "WITHDRAWN", "ACCEPTED"])

            if active_apps < 5:
                table.add_row(
                    "Apply More",
                    f"Only {active_apps} active applications",
                    "Today",
                    "High"
                )

            # Add reminder to prepare for upcoming interviews
            interview_apps = service.get_applications(status="INTERVIEW") + service.get_applications(
                status="PHONE_SCREEN")

            for app in interview_apps[:3]:  # Limit to top 3
                table.add_row(
                    "Prepare",
                    f"Interview prep for {app['job_title']} at {app.get('company', {}).get('name', '')}",
                    "Soon",
                    "High"
                )

        except Exception as e:
            logger.error(f"Error creating action items: {e}")