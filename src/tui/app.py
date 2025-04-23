"""Job Tracker TUI - Main application."""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane
from textual.binding import Binding

from src.tui.dashboard import Dashboard
from src.tui.applications import ApplicationsList


class JobTrackerApp(App):
    """Main Job Tracker application."""

    CSS_PATH = "app.css"
    BINDINGS = [
        Binding("d", "switch_tab('dashboard')", "Dashboard"),
        Binding("a", "switch_tab('applications')", "Applications"),
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

        yield Footer()

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to the specified tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = tab_id


def main():
    """Run the application."""
    app = JobTrackerApp()
    app.run()


if __name__ == "__main__":
    main()