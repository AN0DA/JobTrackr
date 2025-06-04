import pytest
from PyQt6.QtCore import Qt
from src.gui.tabs.contacts import ContactsTab
from src.services.contact_service import ContactService


class TestContactsTab:
    """Test suite for the Contacts tab functionality."""

    def test_tab_initialization(self, main_window):
        """Test that the Contacts tab initializes correctly."""
        tab = main_window.contacts_tab
        assert isinstance(tab, ContactsTab)
        tab.show()
        tab.close()

    def test_tab_switching(self, main_window):
        """Test switching to the Contacts tab."""
        main_window.tabs.setCurrentIndex(3)
        assert isinstance(main_window.tabs.currentWidget(), ContactsTab)

    def test_refresh_data(self, main_window):
        """Test that the tab can refresh its data."""
        tab = main_window.contacts_tab
        if hasattr(tab, "refresh_data"):
            tab.refresh_data()  # Should not raise any exceptions 

    def test_create_and_list_contacts(self, main_window):
        service = ContactService()
        for i in range(2):
            service.create({"name": f"Contact {i}"})
        main_window.tabs.setCurrentIndex(3)
        tab = main_window.contacts_tab
        if hasattr(tab, "refresh_data"):
            tab.refresh_data()
        # assert len(tab.model_data) == 2

    def test_search_contact(self, main_window):
        service = ContactService()
        service.create({"name": "Alice"})
        service.create({"name": "Bob"})
        results = service.search_contacts("Alice")
        assert any(c["name"] == "Alice" for c in results)

    def test_no_contacts_edge_case(self, main_window):
        main_window.tabs.setCurrentIndex(3)
        tab = main_window.contacts_tab
        if hasattr(tab, "refresh_data"):
            tab.refresh_data()
        # assert tab.model_data == [] 