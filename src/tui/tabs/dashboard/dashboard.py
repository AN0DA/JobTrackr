"""Dashboard screen for the Job Tracker TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.widgets import Button, Static, TabbedContent

from src.services.application_service import ApplicationService
from src.tui.widgets.application_list import ApplicationList
from src.tui.widgets.stats_card import StatsCard


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

            # Stats summary cards
            with Container(id="stats-section", classes="content-box"):
                yield Static("Overview", classes="section-heading")

                with Grid(id="stats-grid"):
                    yield StatsCard("Total Applications", "0", _id="total-apps")
                    yield StatsCard("Applied", "0", _id="applied-apps")
                    yield StatsCard("Interviews", "0", _id="interview-apps")
                    yield StatsCard("Offers", "0", _id="offer-apps")

            # Main content in two columns
            with Horizontal(id="dashboard-content"):
                # Left column - Recent applications and activity
                with Vertical(id="left-column"):
                    with Container(classes="content-box-full"):
                        yield Static("Recent Applications", classes="section-heading")
                        yield ApplicationList(title="", _id="recent-apps-list")
                        yield Button("View All Applications", id="view-all-apps")

                # Right column - Reminders and progress
                with Vertical(id="right-column"):
                    with Container(classes="content-box-full"):
                        yield Static("Recent Activity", classes="section-heading")
                        with Container(id="activity-feed"):
                            # Activity items will be added dynamically
                            pass

    def on_mount(self) -> None:
        """Load dashboard data when mounted."""

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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "new-app":
            from src.tui.tabs.applications.application_form import ApplicationForm

            self.app.push_screen(ApplicationForm())
        elif event.button.id == "view-all-apps":
            self.app.query_one(TabbedContent).active = "applications"
