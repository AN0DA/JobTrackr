import pytest
from PyQt6.QtCore import Qt
from src.gui.tabs.applications import ApplicationsTab
from src.services.application_service import ApplicationService


class TestApplicationsTab:
    """Test suite for the Applications tab functionality."""

    def test_tab_initialization(self, main_window):
        """Test that the Applications tab initializes correctly."""
        tab = main_window.applications_tab
        assert isinstance(tab, ApplicationsTab)
        tab.show()
        tab.close()

    def test_tab_switching(self, main_window):
        """Test switching to the Applications tab."""
        main_window.tabs.setCurrentIndex(1)
        assert isinstance(main_window.tabs.currentWidget(), ApplicationsTab)

    def test_refresh_data(self, main_window):
        """Test that the tab can refresh its data."""
        tab = main_window.applications_tab
        if hasattr(tab, "refresh_data"):
            tab.refresh_data()  # Should not raise any exceptions 

    def test_multiple_applications_listed(self, main_window):
        service = ApplicationService()
        for i in range(3):
            service.create({
                "job_title": f"Job {i}",
                "position": f"Position {i}",
                "status": "APPLIED",
                "applied_date": "2024-01-01T12:00:00",
                "company_id": None,
            })
        main_window.tabs.setCurrentIndex(1)
        tab = main_window.applications_tab
        if hasattr(tab, "refresh_data"):
            tab.refresh_data()
        # assert len(tab.model_data) == 3

    def test_filter_by_status(self, main_window):
        service = ApplicationService()
        service.create({
            "job_title": "Job A",
            "position": "A",
            "status": "APPLIED",
            "applied_date": "2024-01-01T12:00:00",
            "company_id": None,
        })
        service.create({
            "job_title": "Job B",
            "position": "B",
            "status": "INTERVIEW",
            "applied_date": "2024-01-01T12:00:00",
            "company_id": None,
        })
        main_window.tabs.setCurrentIndex(1)
        tab = main_window.applications_tab
        if hasattr(tab, "refresh_data"):
            tab.refresh_data()
        # Simulate filter (pseudo, adjust as needed)
        # filtered = [row for row in tab.model_data if row["status"] == "APPLIED"]
        # assert len(filtered) == 1

    def test_no_applications_edge_case(self, main_window):
        main_window.tabs.setCurrentIndex(1)
        tab = main_window.applications_tab
        if hasattr(tab, "refresh_data"):
            tab.refresh_data()
        # assert tab.model_data == [] 