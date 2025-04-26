"""Job Tracker TUI - Main application."""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane
from textual.binding import Binding
import os

from src.db.settings import Settings
from src.tui.tabs.companies.companies import CompaniesList
from src.tui.tabs.contacts.contacts import ContactsList
from src.tui.tabs.dashboard.dashboard import Dashboard
from src.tui.tabs.applications.applications import ApplicationsList
from src.db.database import init_db


class JobTrackerApp(App):
    """Main Job Tracker application."""

    CSS_PATH = "app.css"
    BINDINGS = [
        # Clear and simple keyboard shortcuts
        Binding("d", "switch_tab('dashboard')", "Dashboard"),
        Binding("a", "switch_tab('applications')", "Applications"),
        Binding("c", "switch_tab('companies')", "Companies"),
        Binding("t", "switch_tab('contacts')", "Contacts"),
        # Action shortcuts
        Binding("n", "new_application", "New"),
        Binding("f", "search", "Find"),
        Binding("r", "refresh", "Refresh"),
        # System shortcuts
        Binding("ctrl+s", "show_settings", "Settings"),
        Binding("q", "quit", "Quit"),
        Binding("f1", "help", "Help"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield Header(show_clock=True)

        with TabbedContent(initial="dashboard"):
            with TabPane("Dashboard", id="dashboard"):
                yield Dashboard()
            with TabPane("Applications", id="applications"):
                yield ApplicationsList()
            with TabPane("Companies", id="companies"):
                yield CompaniesList()
            with TabPane("Contacts", id="contacts"):
                yield ContactsList()

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the database when app starts."""
        settings = Settings()

        # Check if this is first run or if database exists
        if not settings.database_exists():
            # Show first run screen
            from src.tui.tabs.settings.first_run import FirstRunScreen

            self.push_screen(FirstRunScreen())
        else:
            # Initialize with existing database
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

        self.sub_title = f"Refreshed {active_tab_id} data"

    def action_new_application(self) -> None:
        """Open the application creation form."""
        from src.tui.tabs.applications.application_form import ApplicationForm

        self.push_screen(ApplicationForm())

    def action_search(self) -> None:
        """Open the search dialog."""
        from src.tui.search import SearchDialog

        self.push_screen(SearchDialog())

    def action_show_settings(self) -> None:
        """Open settings screen."""
        from src.tui.tabs.settings.settings import SettingsScreen

        self.push_screen(SettingsScreen())


def main():
    """Run the application."""
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Run the app
    app = JobTrackerApp()
    app.run()


if __name__ == "__main__":
    main()
