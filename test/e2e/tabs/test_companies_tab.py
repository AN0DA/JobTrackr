import pytest
from PyQt6.QtCore import Qt
from src.gui.tabs.companies import CompaniesTab


class TestCompaniesTab:
    """Test suite for the Companies tab functionality."""

    def test_tab_initialization(self, main_window):
        """Test that the Companies tab initializes correctly."""
        tab = main_window.companies_tab
        assert isinstance(tab, CompaniesTab)
        assert tab.isVisible()

    def test_tab_switching(self, main_window):
        """Test switching to the Companies tab."""
        main_window.tabs.setCurrentIndex(2)
        assert isinstance(main_window.tabs.currentWidget(), CompaniesTab)

    def test_refresh_data(self, main_window):
        """Test that the tab can refresh its data."""
        tab = main_window.companies_tab
        if hasattr(tab, "refresh_data"):
            tab.refresh_data()  # Should not raise any exceptions 