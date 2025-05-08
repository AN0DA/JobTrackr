import pytest
from PyQt6.QtCore import Qt
from src.gui.tabs.contacts import ContactsTab


class TestContactsTab:
    """Test suite for the Contacts tab functionality."""

    def test_tab_initialization(self, main_window):
        """Test that the Contacts tab initializes correctly."""
        tab = main_window.contacts_tab
        assert isinstance(tab, ContactsTab)
        assert tab.isVisible()

    def test_tab_switching(self, main_window):
        """Test switching to the Contacts tab."""
        main_window.tabs.setCurrentIndex(3)
        assert isinstance(main_window.tabs.currentWidget(), ContactsTab)

    def test_refresh_data(self, main_window):
        """Test that the tab can refresh its data."""
        tab = main_window.contacts_tab
        if hasattr(tab, "refresh_data"):
            tab.refresh_data()  # Should not raise any exceptions 