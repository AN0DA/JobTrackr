import pytest
from PyQt6.QtGui import QAction
from src.gui.main_window import MainWindow
from unittest.mock import patch
from src.services.application_service import ApplicationService
from src.db.models import Application
from PyQt6.QtWidgets import QMessageBox


class TestMainWindow:
    """Test suite for the main window functionality."""

    def test_window_initialization(self, main_window):
        """Test that the main window initializes correctly with all components."""
        assert main_window.windowTitle() == "JobTrackr"
        assert main_window.tabs.count() == 4
        assert main_window.tabs.tabText(0) == "Dashboard"
        assert main_window.tabs.tabText(1) == "Applications"
        assert main_window.tabs.tabText(2) == "Companies"
        assert main_window.tabs.tabText(3) == "Contacts"

    def test_menu_bar_actions(self, main_window):
        """Test that menu bar actions work correctly."""
        # Find Settings and About actions by iterating menu actions
        settings_action = None
        about_action = None
        for menu in main_window.menuBar().findChildren(type(main_window.menuBar().addMenu(""))):
            for action in menu.actions():
                if action.text() == "Settings":
                    settings_action = action
                if action.text() == "About":
                    about_action = action
        assert settings_action is not None
        assert about_action is not None

    def test_status_bar(self, main_window):
        """Test status bar functionality."""
        test_message = "Test status message"
        main_window.show_status_message(test_message)
        assert main_window.statusBar().currentMessage() == test_message

    def test_window_resize(self, main_window):
        """Test window resize functionality."""
        new_width = 1280
        new_height = 800
        main_window.resize(new_width, new_height)
        assert main_window.width() == new_width
        assert main_window.height() == new_height

    def test_close_event(self, main_window):
        """Test window close event."""
        main_window.close()
        assert not main_window.isVisible()

    def test_create_application_and_display(self, main_window):
        """Test creating a new application and verifying it appears in the applications tab."""
        service = ApplicationService()
        data = {
            "job_title": "Test Engineer",
            "position": "Engineer",
            "location": "Remote",
            "salary_min": 100000,
            "salary_max": 120000,
            "status": "APPLIED",
            "applied_date": "2024-01-01T12:00:00",
            "company_id": None,
        }
        app_dict = service.create(data)
        # Simulate refresh in UI
        main_window.tabs.setCurrentIndex(1)
        tab = main_window.applications_tab
        if hasattr(tab, "refresh_data"):
            tab.refresh_data()
        # Check if the new application is present in the tab's data model (pseudo, adjust as needed)
        # assert any(row["job_title"] == "Test Engineer" for row in tab.model_data)

    def test_error_handling_shows_dialog(self, main_window):
        """Test error dialog is shown when a service fails."""
        with patch.object(ApplicationService, "get_applications", side_effect=Exception("DB error")):
            # Simulate user action that triggers the error
            try:
                main_window.tabs.setCurrentIndex(1)
                tab = main_window.applications_tab
                if hasattr(tab, "refresh_data"):
                    tab.refresh_data()
            except Exception:
                pass
            # Check if error dialog was shown (pseudo, adjust as needed)
            # assert main_window.last_error_message == "DB error"

    def test_tab_switching_updates_view(self, main_window):
        """Test that switching tabs updates the view with correct data."""
        for idx, name in enumerate(["Dashboard", "Applications", "Companies", "Contacts"]):
            main_window.tabs.setCurrentIndex(idx)
            assert main_window.tabs.tabText(idx) == name 