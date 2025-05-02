from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.config import FONT_SIZES, UI_COLORS
from src.gui.dialogs.application_form import ApplicationForm
from src.services.application_service import ApplicationService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class StatsCard(QWidget):
    """Widget displaying a statistic with title and value."""

    def __init__(self, title, value="0", icon=None, color=UI_COLORS["primary"], parent=None):
        super().__init__(parent)

        # Set up styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }}
            QLabel[class="title"] {{
                color: #6B7280;
                font-size: {FONT_SIZES["md"]}px;
            }}
            QLabel[class="value"] {{
                color: {color};
                font-size: {FONT_SIZES["3xl"]}px;
                font-weight: bold;
            }}
        """)

        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)

        # Header with icon and title
        header_layout = QHBoxLayout()

        # Title label
        self.title_label = QLabel(title)
        self.title_label.setProperty("class", "title")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        # Add icon if provided
        if icon:
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(24, 24))
            header_layout.addWidget(icon_label)

        # Value label with larger font
        self.value_label = QLabel(value)
        self.value_label.setProperty("class", "value")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Add widgets to layout
        self.layout.addLayout(header_layout)
        self.layout.addWidget(self.value_label)
        self.layout.addStretch()

        # Set fixed size
        self.setMinimumHeight(120)
        self.setMaximumHeight(120)

    def update_value(self, value):
        """Update the displayed value."""
        self.value_label.setText(str(value))


class ApplicationList(QTableWidget):
    """Table widget showing a list of applications."""

    def __init__(self, parent=None):
        super().__init__(0, 4, parent)  # 0 rows, 4 columns

        # Set up the table
        self.setHorizontalHeaderLabels(["Job Title", "Company", "Status", "Applied Date"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

    def update_applications(self, applications):
        """Update the displayed applications."""
        self.setRowCount(0)  # Clear current rows

        if not applications:
            self.insertRow(0)
            self.setItem(0, 0, QTableWidgetItem("No applications found"))
            return

        for i, app in enumerate(applications):
            self.insertRow(i)

            # Add items to the row
            self.setItem(i, 0, QTableWidgetItem(app["job_title"]))

            company_name = app.get("company", {}).get("name", "")
            self.setItem(i, 1, QTableWidgetItem(company_name))

            status_item = QTableWidgetItem(app["status"])
            self.setItem(i, 2, status_item)

            self.setItem(i, 3, QTableWidgetItem(app["applied_date"].split("T")[0]))


class DashboardTab(QWidget):
    """Dashboard tab showing overview and recent activities."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.main_window = parent
        self._init_ui()
        self.refresh_data()

    def _init_ui(self) -> None:
        """Initialize the dashboard UI."""
        main_layout = QVBoxLayout(self)

        # Header section
        header_layout = QVBoxLayout()
        title_label = QLabel("Your Job Search Dashboard")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Quick actions
        actions_layout = QHBoxLayout()
        self.new_app_btn = QPushButton("➕ New Application")
        self.new_app_btn.clicked.connect(self.on_new_application)
        actions_layout.addStretch()
        actions_layout.addWidget(self.new_app_btn)
        actions_layout.addStretch()

        header_layout.addWidget(title_label)
        header_layout.addLayout(actions_layout)
        main_layout.addLayout(header_layout)

        # Stats section
        stats_layout = QVBoxLayout()
        stats_label = QLabel("Overview")
        stats_label.setFont(QFont("", 12, QFont.Weight.Bold))
        stats_layout.addWidget(stats_label)

        # Stats cards in a grid
        stats_grid = QGridLayout()
        self.total_apps_card = StatsCard("Total Applications")
        self.applied_apps_card = StatsCard("Applied")
        self.interview_apps_card = StatsCard("Interviews")
        self.offer_apps_card = StatsCard("Offers")

        stats_grid.addWidget(self.total_apps_card, 0, 0)
        stats_grid.addWidget(self.applied_apps_card, 0, 1)
        stats_grid.addWidget(self.interview_apps_card, 0, 2)
        stats_grid.addWidget(self.offer_apps_card, 0, 3)

        stats_layout.addLayout(stats_grid)
        main_layout.addLayout(stats_layout)

        # Content section - two columns
        content_layout = QHBoxLayout()

        # Left column - Recent applications
        left_column = QVBoxLayout()
        recent_apps_label = QLabel("Recent Applications")
        recent_apps_label.setFont(QFont("", 12, QFont.Weight.Bold))
        left_column.addWidget(recent_apps_label)

        self.recent_apps_list = ApplicationList()
        left_column.addWidget(self.recent_apps_list)

        self.view_all_apps_btn = QPushButton("View All Applications")
        self.view_all_apps_btn.clicked.connect(self.on_view_all_applications)
        left_column.addWidget(self.view_all_apps_btn)

        # Right column - Activity feed
        right_column = QVBoxLayout()
        activity_label = QLabel("Recent Activity")
        activity_label.setFont(QFont("", 12, QFont.Weight.Bold))
        right_column.addWidget(activity_label)

        self.activity_feed = QLabel("No recent activity")
        right_column.addWidget(self.activity_feed)
        right_column.addStretch()

        # Add columns to content layout
        content_layout.addLayout(left_column)
        content_layout.addLayout(right_column)
        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)

    def refresh_data(self) -> None:
        """Load and display dashboard data."""
        try:
            service = ApplicationService()
            stats = service.get_dashboard_stats()

            # Update stats cards
            self.total_apps_card.update_value(str(stats["total_applications"]))

            # Find status counts
            interview_count = 0
            for status_count in stats["applications_by_status"]:
                if status_count["status"] == "APPLIED":
                    self.applied_apps_card.update_value(str(status_count["count"]))
                elif status_count["status"] in ["INTERVIEW", "PHONE_SCREEN", "TECHNICAL_INTERVIEW"]:
                    interview_count += status_count["count"]
                elif status_count["status"] == "OFFER":
                    self.offer_apps_card.update_value(str(status_count["count"]))

            self.interview_apps_card.update_value(str(interview_count))

            # Update recent applications list
            self.recent_apps_list.update_applications(stats["recent_applications"])

            self.main_window.show_status_message("Dashboard updated")
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}", exc_info=True)
            self.main_window.show_status_message(f"Error: {str(e)}")

    @pyqtSlot()
    def on_new_application(self) -> None:
        """Open the new application form."""
        dialog = ApplicationForm(self)
        if dialog.exec():
            self.refresh_data()

    @pyqtSlot()
    def on_view_all_applications(self) -> None:
        """Switch to applications tab."""
        self.main_window.tabs.setCurrentIndex(1)  # Switch to Applications tab
