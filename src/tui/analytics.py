"""Analytics screen for job application insights."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, Grid
from textual.widgets import Static, DataTable
from datetime import datetime, timedelta

from src.services.analytics_service import AnalyticsService
from src.tui.widgets.stats_card import StatsCard
from src.tui.widgets.plot_chart import PlotChart
from src.tui.widgets.time_series_chart import TimeSeriesChart


class Analytics(Static):
    """Analytics dashboard for job applications."""

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Job Search Analytics", id="analytics-title")

            with Grid(id="analytics-stats"):
                yield StatsCard("Response Rate", "0%", id="response-rate")
                yield StatsCard("Interview Rate", "0%", id="interview-rate")
                yield StatsCard("Time to Interview", "0 days", id="time-to-interview")
                yield StatsCard("Applications per Week", "0", id="apps-per-week")

            with Horizontal(id="charts-container"):
                # Status breakdown chart
                with Vertical(id="status-chart-container"):
                    yield Static("Applications by Status", classes="chart-title")
                    yield PlotChart(title="Status Distribution", id="status-chart", color="cyan")

                # Timeline chart
                with Vertical(id="timeline-chart-container"):
                    yield Static("Applications Over Time", classes="chart-title")
                    yield TimeSeriesChart(title="Weekly Applications", id="timeline-chart", color="green")

            with Vertical(id="top-companies"):
                yield Static("Most Applied Companies", classes="section-title")
                yield DataTable(id="companies-table")

            with Vertical(id="recent-activity"):
                yield Static("Recent Activity", classes="section-title")
                yield DataTable(id="activity-table")

    def on_mount(self) -> None:
        """Set up the tables and load data when mounted."""
        # Set up tables
        companies_table = self.query_one("#companies-table", DataTable)
        companies_table.add_columns("Company", "Applications", "Responses", "Interviews")

        activity_table = self.query_one("#activity-table", DataTable)
        activity_table.add_columns("Date", "Type", "Company", "Details")

        # Load data
        self.load_analytics()

    def load_analytics(self) -> None:
        """Load analytics data."""
        try:
            service = AnalyticsService()
            data = service.get_analytics()

            # Update stats cards
            self.query_one("#response-rate", StatsCard).update_value(f"{data['response_rate']}%")
            self.query_one("#interview-rate", StatsCard).update_value(f"{data['interview_rate']}%")
            self.query_one("#time-to-interview", StatsCard).update_value(f"{data['avg_days_to_interview']} days")
            self.query_one("#apps-per-week", StatsCard).update_value(f"{data['apps_per_week']}")

            # Update status chart
            status_chart = self.query_one("#status-chart", PlotChart)
            status_dict = {status: count for status, count in data["status_counts"]}
            status_chart.data = status_dict

            # Update timeline chart
            timeline_chart = self.query_one("#timeline-chart", TimeSeriesChart)
            timeline_chart.data = data["weekly_applications"]

            # Update company table
            companies_table = self.query_one("#companies-table", DataTable)
            companies_table.clear()
            for company in data["top_companies"]:
                companies_table.add_row(
                    company["name"],
                    str(company["applications"]),
                    str(company["responses"]),
                    str(company["interviews"])
                )

            # Update activity table
            activity_table = self.query_one("#activity-table", DataTable)
            activity_table.clear()
            for activity in data["recent_activity"]:
                activity_table.add_row(
                    activity["date"],
                    activity["type"],
                    activity["company"],
                    activity["details"]
                )

            self.app.sub_title = "Analytics loaded successfully"

        except Exception as e:
            self.app.sub_title = f"Error loading analytics: {str(e)}"