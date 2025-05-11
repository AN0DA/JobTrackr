import pytest
from PyQt6.QtCore import Qt
from src.gui.tabs.applications import ApplicationsTab


class TestApplicationsTab:
    """Test suite for the Applications tab functionality."""

    def test_tab_initialization(self, main_window):
        """Test that the Applications tab initializes correctly."""
        tab = main_window.applications_tab
        assert isinstance(tab, ApplicationsTab)
        assert tab.isVisible()

    def test_tab_switching(self, main_window):
        """Test switching to the Applications tab."""
        main_window.tabs.setCurrentIndex(1)
        assert isinstance(main_window.tabs.currentWidget(), ApplicationsTab)

    def test_refresh_data(self, main_window):
        """Test that the tab can refresh its data."""
        tab = main_window.applications_tab
        if hasattr(tab, "refresh_data"):
            tab.refresh_data()  # Should not raise any exceptions 