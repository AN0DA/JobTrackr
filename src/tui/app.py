"""Job Tracker TUI - Main application."""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane
from textual.binding import Binding
from textual.css.query import NoMatches
import os

from src.tui.dashboard import Dashboard
from src.tui.applications import ApplicationsList
from src.db.database import init_db

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane
from textual.binding import Binding

from src.tui.dashboard import Dashboard
from src.tui.applications import ApplicationsList
from src.tui.analytics import Analytics
from src.tui.today import TodayView
from src.db.database import init_db


class JobTrackerApp(App):
    """Main Job Tracker application."""

    CSS_PATH = "app.css"
    BINDINGS = [
        Binding("d", "switch_tab('dashboard')", "Dashboard"),
        Binding("a", "switch_tab('applications')", "Applications"),
        Binding("t", "switch_tab('today')", "Today"),
        Binding("s", "switch_tab('analytics')", "Stats"),
        Binding("n", "new_application", "New Application"),
        Binding("f", "search", "Find"),
        Binding("e", "export", "Export"),
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("f1", "help", "Help"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield Header(show_clock=True)

        with TabbedContent(initial="dashboard"):
            with TabPane("Dashboard", id="dashboard"):
                yield Dashboard()
            with TabPane("Today", id="today"):
                yield TodayView()
            with TabPane("Applications", id="applications"):
                yield ApplicationsList()
            with TabPane("Analytics", id="analytics"):
                yield Analytics()

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the database when app starts."""
        self.sub_title = "Initializing database..."
        init_db()
        self.sub_title = "Ready"

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to the specified tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = tab_id

    def action_refresh(self) -> None:
        """Refresh the current screen's data."""
        active_tab_id = self.query_one(TabbedContent).active

        if active_tab_id == "dashboard":
            self.query_one(Dashboard).refresh_data()
        elif active_tab_id == "applications":
            self.query_one(ApplicationsList).load_applications()
        elif active_tab_id == "today":
            self.query_one(TodayView).load_today_data()
        elif active_tab_id == "analytics":
            self.query_one(Analytics).load_analytics()

        self.sub_title = f"Refreshed {active_tab_id} data"

    def action_new_application(self) -> None:
        """Open the quick application creation dialog."""
        from src.tui.quick_add import QuickAddDialog
        self.push_screen(QuickAddDialog())

    def action_search(self) -> None:
        """Open the search dialog."""
        from src.tui.search import SearchDialog
        self.push_screen(SearchDialog())

    def action_export(self) -> None:
        """Open the export dialog."""
        from src.tui.export import ExportDialog
        self.push_screen(ExportDialog())

def main():
    """Run the application."""
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)

    # Run the app
    app = JobTrackerApp()
    app.run()


if __name__ == "__main__":
    main()