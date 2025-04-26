"""Dashboard screen for the Job Tracker TUI."""

from textual.widgets import Static, Button
from textual.containers import Grid, Container, Vertical, Horizontal
from textual.app import ComposeResult

from src.tui.widgets.stats_card import StatsCard
from src.tui.widgets.application_list import ApplicationList
from src.services.application_service import ApplicationService


class Dashboard(Static):
    """Main dashboard view."""

    def compose(self) -> ComposeResult:
        """Compose the dashboard layout."""
        with Container(id="dashboard-container"):
            # Header with welcome and summary
            with Container(id="dashboard-header", classes="content-box"):
                yield Static("Your Job Search Dashboard", id="dashboard-title")

                with Horizontal(id="quick-actions"):
                    yield Button("➕ New Application", variant="primary", id="new-app")
                    yield Button("📅 Today's Tasks", id="view-today")
                    yield Button("📊 Analytics", id="view-analytics")

            # Stats summary cards
            with Container(id="stats-section", classes="content-box"):
                yield Static("Overview", classes="section-heading")

                with Grid(id="stats-grid"):
                    yield StatsCard("Active Applications", "0", id="active-apps")
                    yield StatsCard("This Week", "0", id="weekly-apps")
                    yield StatsCard("Interview Rate", "0%", id="interview-rate")
                    yield StatsCard("Response Rate", "0%", id="response-rate")

            # Main content in two columns
            with Horizontal(id="dashboard-content"):
                # Left column - Recent applications and activity
                with Vertical(id="left-column"):
                    with Container(classes="content-box"):
                        yield Static("Recent Applications", classes="section-heading")
                        yield ApplicationList(title="", id="recent-apps-list")
                        yield Button("View All Applications", id="view-all-apps")

                # Right column - Reminders and progress
                with Vertical(id="right-column"):
                    with Container(classes="content-box"):
                        yield Static("Recent Activity", classes="section-heading")
                        with Container(id="activity-feed"):
                            # Activity items will be added dynamically
                            pass

    def on_mount(self) -> None:
        """Load dashboard data when mounted."""
        self.refresh_data()

    def refresh_data(self) -> None:
        """Refresh dashboard data from database."""
        self.update_status("Fetching dashboard data...")

        try:
            service = ApplicationService()
            stats = service.get_dashboard_stats()

            # Update stats cards
            total_card = self.query_one("#total-apps", StatsCard)
            applied_card = self.query_one("#applied-apps", StatsCard)
            interview_card = self.query_one("#interview-apps", StatsCard)
            offer_card = self.query_one("#offer-apps", StatsCard)

            total_card.update_value(str(stats["total_applications"]))

            # Find status counts
            interview_count = 0
            for status_count in stats["applications_by_status"]:
                if status_count["status"] == "APPLIED":
                    applied_card.update_value(str(status_count["count"]))
                elif status_count["status"] in [
                    "INTERVIEW",
                    "PHONE_SCREEN",
                    "TECHNICAL_INTERVIEW",
                ]:
                    interview_count += status_count["count"]
                elif status_count["status"] == "OFFER":
                    offer_card.update_value(str(status_count["count"]))

            interview_card.update_value(str(interview_count))

            # Update recent applications list
            app_list = self.query_one(ApplicationList)
            app_list.update_applications(stats["recent_applications"])

            self.update_status("Dashboard updated")
        except Exception as e:
            self.update_status(f"Error: {str(e)}")

    def update_status(self, message: str) -> None:
        """Update status message in the footer."""
        self.app.sub_title = message
