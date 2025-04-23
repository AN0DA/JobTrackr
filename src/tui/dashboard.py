"""Dashboard screen for the Job Tracker TUI."""

from textual.widgets import Static
from textual.containers import Grid, Container
from textual.app import ComposeResult

from src.tui.widgets.stats_card import StatsCard
from src.tui.widgets.application_list import ApplicationList
from src.tui.widgets.reminder_list import ReminderList
from src.tui.api_client import APIClient


class Dashboard(Static):
    """Main dashboard view."""

    def compose(self) -> ComposeResult:
        """Compose the dashboard layout."""
        with Container():
            with Grid(id="stats-grid"):
                yield StatsCard("Total Applications", "0")
                yield StatsCard("Applied", "0")
                yield StatsCard("Interviews", "0")
                yield StatsCard("Offers", "0")

            with Grid(id="lists-grid"):
                yield ApplicationList(title="Recent Applications")
                yield ReminderList(title="Upcoming Reminders")

    async def on_mount(self) -> None:
        """Load dashboard data when mounted."""
        await self.refresh_data()

    async def refresh_data(self) -> None:
        """Refresh dashboard data from API."""
        self.update_status("Fetching dashboard data...")

        try:
            client = APIClient()
            stats = await client.get_dashboard_stats()

            # Update stats cards
            total_card = self.query_one("#total-apps", StatsCard)
            applied_card = self.query_one("#applied-apps", StatsCard)
            interview_card = self.query_one("#interview-apps", StatsCard)
            offer_card = self.query_one("#offer-apps", StatsCard)

            total_card.update_value(str(stats["totalApplications"]))

            # Find status counts
            for status_count in stats["applicationsByStatus"]:
                if status_count["status"] == "APPLIED":
                    applied_card.update_value(str(status_count["count"]))
                elif status_count["status"] in ["INTERVIEW", "PHONE_SCREEN", "TECHNICAL_INTERVIEW"]:
                    interview_card.update_value(str(status_count["count"]))
                elif status_count["status"] == "OFFER":
                    offer_card.update_value(str(status_count["count"]))

            # Update recent applications list
            app_list = self.query_one(ApplicationList)
            app_list.update_applications(stats["recentApplications"])

            # Update reminders list
            reminder_list = self.query_one(ReminderList)
            reminder_list.update_reminders(stats["upcomingReminders"])

            self.update_status("Dashboard updated")
        except Exception as e:
            self.update_status(f"Error: {str(e)}")

    def update_status(self, message: str) -> None:
        """Update status message in the footer."""
        self.app.sub_title = message
