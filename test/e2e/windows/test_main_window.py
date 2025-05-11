import pytest
from PyQt6.QtGui import QAction
from src.gui.main_window import MainWindow


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
        # Test Settings menu
        settings_action = main_window.menu_bar.findChild(QAction, "Settings")
        assert settings_action is not None
        
        # Test About menu
        about_action = main_window.menu_bar.findChild(QAction, "About")
        assert about_action is not None

    def test_status_bar(self, main_window):
        """Test status bar functionality."""
        test_message = "Test status message"
        main_window.show_status_message(test_message)
        assert main_window.statusBar().currentMessage() == test_message

    def test_error_dialog(self, main_window):
        """Test error message dialog."""
        title = "Test Error"
        message = "This is a test error message"
        main_window.show_error_message(title, message)

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