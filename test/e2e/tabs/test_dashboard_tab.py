import pytest
from PyQt6.QtCore import Qt
from src.gui.tabs.dashboard import DashboardTab


class TestDashboardTab:
    """Test suite for the Dashboard tab functionality."""

    def test_tab_initialization(self, main_window):
        """Test that the Dashboard tab initializes correctly."""
        tab = main_window.dashboard_tab
        assert isinstance(tab, DashboardTab)
        assert tab.isVisible()

    def test_tab_switching(self, main_window):
        """Test switching to the Dashboard tab."""
        main_window.tabs.setCurrentIndex(0)
        assert isinstance(main_window.tabs.currentWidget(), DashboardTab)

    def test_refresh_data(self, main_window):
        """Test that the tab can refresh its data."""
        tab = main_window.dashboard_tab
        if hasattr(tab, "refresh_data"):
            tab.refresh_data()  # Should not raise any exceptions 