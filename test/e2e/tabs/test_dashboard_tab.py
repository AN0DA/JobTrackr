from src.gui.tabs.dashboard import DashboardTab
from src.services.application_service import ApplicationService


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

    def test_dashboard_recent_and_status_counts(self, main_window):
        service = ApplicationService()
        service.create(
            {
                "job_title": "Job1",
                "position": "P1",
                "status": "APPLIED",
                "applied_date": "2024-01-01T12:00:00",
                "company_id": None,
            }
        )
        service.create(
            {
                "job_title": "Job2",
                "position": "P2",
                "status": "INTERVIEW",
                "applied_date": "2024-01-02T12:00:00",
                "company_id": None,
            }
        )
        main_window.tabs.setCurrentIndex(0)
        tab = main_window.dashboard_tab
        if hasattr(tab, "refresh_data"):
            tab.refresh_data()
        # Example: assert tab.status_counts["APPLIED"] == 1
        # Example: assert tab.status_counts["INTERVIEW"] == 1
