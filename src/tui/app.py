import os

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, TabbedContent, TabPane

from src.db.database import init_db
from src.db.settings import Settings
from src.tui.tabs.applications.applications import ApplicationsList
from src.tui.tabs.companies.companies import CompaniesList
from src.tui.tabs.contacts.contacts import ContactsList
from src.tui.tabs.dashboard.dashboard import Dashboard
from src.utils.logging import get_logger

# Set up module-level logger
logger = get_logger(__name__)


class JobTrackr(App):
    """Main Job Tracker application."""

    CSS_PATH = "app.tcss"
    BINDINGS = [
        # Clear and simple keyboard shortcuts
        Binding("d", "switch_tab('dashboard')", "Dashboard"),
        Binding("a", "switch_tab('applications')", "Applications"),
        Binding("c", "switch_tab('companies')", "Companies"),
        Binding("t", "switch_tab('contacts')", "Contacts"),
        # Action shortcuts
        Binding("n", "new_application", "New"),
        Binding("f", "search", "Find"),
        # System shortcuts
        Binding("ctrl+s", "show_settings", "Settings"),
        Binding("ctrl+q", "quit", "Quit"),
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
        logger.info("Application starting")

        # Check if this is first run or if database exists
        if not settings.database_exists():
            # Show first run screen
            logger.info("First run detected - showing setup screen")
            from src.tui.tabs.settings.first_run import FirstRunScreen

            self.push_screen(FirstRunScreen())
        else:
            # Initialize with existing database
            db_path = settings.get_database_path()
            logger.info(f"Initializing database at {db_path}")
            self.sub_title = "Initializing database..."

            try:
                init_db()
                self.sub_title = "Ready"
                logger.info("Database initialization successful")
            except Exception as e:
                error_msg = f"Database initialization failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                self.sub_title = error_msg

    # ... rest of the class unchanged ...

    def on_exception(self, exception: Exception) -> None:
        """Handle uncaught exceptions in the application."""
        logger.exception(f"Uncaught exception: {exception}")
        self.sub_title = f"ERROR: {str(exception)}"


def app() -> None:
    """Run the application."""
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)

        # Log application start
        logger.info("Starting JobTrackr application")

        # Run the app
        app = JobTrackr()
        app.run()

    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        # Re-raise to show the error to the user
        raise
