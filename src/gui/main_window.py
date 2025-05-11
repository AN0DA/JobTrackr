from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QMenuBar, QMessageBox, QStatusBar, QTabWidget

from src import __version__
from src.db.settings import Settings
from src.gui.dialogs.settings import SettingsDialog  # Fixed import path
from src.gui.search import SearchDialog
from src.gui.tabs.applications import ApplicationsTab
from src.gui.tabs.companies import CompaniesTab
from src.gui.tabs.contacts import ContactsTab
from src.gui.tabs.dashboard import DashboardTab
from src.utils.logging import get_logger

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window with tabs for different sections."""

    def __init__(self) -> None:
        super().__init__()

        # Configuration
        self.settings = Settings()
        self.setWindowTitle("JobTrackr")
        self.resize(1024, 768)

        # Set up status bar
        self.setStatusBar(QStatusBar())  # Create status bar using built-in method
        self.statusBar().showMessage("Ready")  # Use statusBar() method to access it

        # Initialize UI components
        self._init_ui()

        logger.info("Main window initialized")

    def _init_ui(self) -> None:
        """Initialize the user interface components."""
        # Create menu bar
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)

        # File menu
        file_menu = self.menu_bar.addMenu("File")
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)

        # Help menu
        help_menu = self.menu_bar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # Create tab widget
        self.tabs = QTabWidget()

        # Create each tab
        self.dashboard_tab = DashboardTab(self)
        self.applications_tab = ApplicationsTab(self)
        self.companies_tab = CompaniesTab(self)
        self.contacts_tab = ContactsTab(self)

        # Add tabs to widget
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.applications_tab, "Applications")
        self.tabs.addTab(self.companies_tab, "Companies")
        self.tabs.addTab(self.contacts_tab, "Contacts")

        # Connect tab changed signal
        self.tabs.currentChanged.connect(self.on_tab_changed)

        # Set central widget
        self.setCentralWidget(self.tabs)

        # Set up keyboard shortcuts
        self._setup_shortcuts()

    def _setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts for common actions."""
        # These would typically be implemented using QAction and QShortcut
        pass

    def on_tab_changed(self, index) -> None:
        """Handle tab changes - refresh data in the selected tab."""
        current_tab = self.tabs.widget(index)
        if hasattr(current_tab, "refresh_data"):
            current_tab.refresh_data()

    def show_settings(self) -> None:
        """Show the settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec()

    def show_search(self) -> None:
        """Show the search dialog."""
        dialog = SearchDialog(self)
        dialog.exec()

    def show_about(self) -> None:
        """Show the about dialog."""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.about(self, "About JobTrackr", f"JobTrackr v{__version__}\n\nA job application tracking tool.")

    def show_status_message(self, message, timeout=5000) -> None:
        """Display a message in the status bar."""
        self.statusBar().showMessage(message, timeout)  # Use statusBar() method instead of status_bar attribute

    def show_error_message(self, title, message) -> None:
        """Display an error message dialog."""
        QMessageBox.critical(self, title, message)

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        logger.info("Application shutting down")
        # Any cleanup needed before closing
        event.accept()
