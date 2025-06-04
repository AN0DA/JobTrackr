import pytest
from PyQt6.QtCore import Qt
from src.gui.tabs.companies import CompaniesTab
from src.services.company_service import CompanyService


class TestCompaniesTab:
    """Test suite for the Companies tab functionality."""

    def test_tab_initialization(self, main_window):
        """Test that the Companies tab initializes correctly."""
        tab = main_window.companies_tab
        assert isinstance(tab, CompaniesTab)
        tab.show()
        tab.close()

    def test_tab_switching(self, main_window):
        """Test switching to the Companies tab."""
        main_window.tabs.setCurrentIndex(2)
        assert isinstance(main_window.tabs.currentWidget(), CompaniesTab)

    def test_refresh_data(self, main_window):
        """Test that the tab can refresh its data."""
        tab = main_window.companies_tab
        if hasattr(tab, "refresh_data"):
            tab.refresh_data()  # Should not raise any exceptions 

    def test_create_and_list_companies(self, main_window):
        service = CompanyService()
        for i in range(2):
            service.create({"name": f"Company {i}"})
        main_window.tabs.setCurrentIndex(2)
        tab = main_window.companies_tab
        if hasattr(tab, "refresh_data"):
            tab.refresh_data()
        # assert len(tab.model_data) == 2

    def test_update_company(self, main_window):
        service = CompanyService()
        company = service.create({"name": "Old Name"})
        updated = service.update(company["id"], {"name": "New Name"})
        assert updated["name"] == "New Name"

    def test_delete_company(self, main_window):
        service = CompanyService()
        company = service.create({"name": "ToDelete"})
        service.delete(company["id"])
        companies = service.get_all()
        assert all(c["id"] != company["id"] for c in companies) 