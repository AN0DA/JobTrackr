from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.config import ApplicationStatus
from src.gui.components.data_table import DataTable
from src.gui.dialogs.application_detail import ApplicationDetailDialog
from src.gui.dialogs.application_form import ApplicationForm
from src.services.application_service import ApplicationService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ApplicationsTab(QWidget):
    """Tab for managing job applications."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.main_window = parent
        self.current_status = None
        self._init_ui()
        self.load_applications()

    def _init_ui(self) -> None:
        """Initialize the applications tab UI."""
        layout = QVBoxLayout(self)

        # Header section with filters
        header_layout = QHBoxLayout()

        # Status filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("All")
        for status in ApplicationStatus:
            self.status_filter.addItem(status.value)
        self.status_filter.currentTextChanged.connect(self.on_status_filter_changed)
        filter_layout.addWidget(self.status_filter)

        # Search box
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search applications...")
        self.search_input.returnPressed.connect(self.on_search)
        self.search_button = QPushButton("🔍")
        self.search_button.clicked.connect(self.on_search)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)

        # New application button
        self.new_app_button = QPushButton("New Application")
        self.new_app_button.clicked.connect(self.on_new_application)

        # Add all components to header
        header_layout.addLayout(filter_layout)
        header_layout.addLayout(search_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.new_app_button)

        layout.addLayout(header_layout)

        # Table for applications
        self.table = DataTable(
            0, ["ID", "Job Title", "Company", "Position", "Status", "Applied Date"]
        )  # 0 rows, 6 columns
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemDoubleClicked.connect(self.on_row_double_clicked)
        layout.addWidget(self.table)

        # Action buttons
        actions_layout = QHBoxLayout()
        self.view_button = QPushButton("View")
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        self.view_button.clicked.connect(self.on_view_application)
        self.edit_button.clicked.connect(self.on_edit_application)
        self.delete_button.clicked.connect(self.on_delete_application)

        # Initially disable buttons until selection
        self.view_button.setEnabled(False)
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)

        actions_layout.addStretch()
        actions_layout.addWidget(self.view_button)
        actions_layout.addWidget(self.edit_button)
        actions_layout.addWidget(self.delete_button)
        layout.addLayout(actions_layout)

        self.setLayout(layout)

        # Connect selection signal
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

    def load_applications(self, status=None) -> None:
        """Load applications with optional status filter."""
        try:
            self.main_window.show_status_message("Loading applications...")
            self.current_status = status

            service = ApplicationService()

            if status and status != "All":
                applications = service.get_applications(status=status)
            else:
                applications = service.get_applications()

            # Clear and update table
            self.table.setRowCount(0)

            if not applications:
                self.main_window.show_status_message("No applications found")
                return

            for i, app in enumerate(applications):
                self.table.insertRow(i)

                # Add items to the row
                self.table.setItem(i, 0, QTableWidgetItem(str(app["id"])))
                self.table.setItem(i, 1, QTableWidgetItem(app["job_title"]))

                company_name = app.get("company", {}).get("name", "")
                self.table.setItem(i, 2, QTableWidgetItem(company_name))

                self.table.setItem(i, 3, QTableWidgetItem(app["position"]))

                status_item = QTableWidgetItem(app["status"])
                self.table.setItem(i, 4, status_item)

                # Format date
                date_str = app["applied_date"].split("T")[0]
                self.table.setItem(i, 5, QTableWidgetItem(date_str))

            count = len(applications)
            self.main_window.show_status_message(f"Loaded {count} application{'s' if count != 1 else ''}")

        except Exception as e:
            logger.error(f"Error loading applications: {e}", exc_info=True)
            self.main_window.show_status_message(f"Error: {str(e)}")

    def search_applications(self, search_term) -> None:
        """Search applications by keyword."""
        try:
            if not search_term:
                self.load_applications(self.current_status)
                return

            self.main_window.show_status_message(f"Searching for '{search_term}'...")

            service = ApplicationService()
            applications = service.search_applications(search_term)

            # Apply status filter if active
            if self.current_status and self.current_status != "All":
                applications = [app for app in applications if app["status"] == self.current_status]

            # Update table
            self.table.setRowCount(0)

            if not applications:
                self.main_window.show_status_message(f"No results found for '{search_term}'")
                return

            for i, app in enumerate(applications):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(str(app["id"])))
                self.table.setItem(i, 1, QTableWidgetItem(app["job_title"]))

                company_name = app.get("company", {}).get("name", "")
                self.table.setItem(i, 2, QTableWidgetItem(company_name))

                self.table.setItem(i, 3, QTableWidgetItem(app["position"]))
                self.table.setItem(i, 4, QTableWidgetItem(app["status"]))

                date_str = app["applied_date"].split("T")[0]
                self.table.setItem(i, 5, QTableWidgetItem(date_str))

            count = len(applications)
            self.main_window.show_status_message(
                f"Found {count} application{'s' if count != 1 else ''} matching '{search_term}'"
            )

        except Exception as e:
            logger.error(f"Error searching applications: {e}", exc_info=True)
            self.main_window.show_status_message(f"Search error: {str(e)}")

    def get_selected_application_id(self) -> int | None:
        """Get the ID of the selected application."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        id_item = self.table.item(row, 0)
        if id_item:
            return int(id_item.text())
        return None

    def refresh_data(self) -> None:
        """Refresh the applications data."""
        self.load_applications(self.current_status)

    @pyqtSlot()
    def on_selection_changed(self) -> None:
        """Enable or disable buttons based on selection."""
        has_selection = bool(self.table.selectedItems())
        self.view_button.setEnabled(has_selection)
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    @pyqtSlot(str)
    def on_status_filter_changed(self, status) -> None:
        """Handle status filter changes."""
        if status == "All":
            self.load_applications(None)
        else:
            self.load_applications(status)

    @pyqtSlot()
    def on_search(self) -> None:
        """Handle search button click."""
        search_term = self.search_input.text().strip()
        self.search_applications(search_term)

    @pyqtSlot()
    def on_new_application(self) -> None:
        """Open dialog to create a new application."""
        dialog = ApplicationForm(self)
        if dialog.exec():
            self.refresh_data()

    @pyqtSlot()
    def on_view_application(self) -> None:
        """Open the application detail view."""
        app_id = self.get_selected_application_id()
        if app_id:
            dialog = ApplicationDetailDialog(self, app_id)
            dialog.exec()
            self.refresh_data()

    @pyqtSlot()
    def on_edit_application(self) -> None:
        """Open dialog to edit the selected application."""
        app_id = self.get_selected_application_id()
        if app_id:
            dialog = ApplicationForm(self, app_id)
            if dialog.exec():
                self.refresh_data()

    @pyqtSlot()
    def on_delete_application(self) -> None:
        """Delete the selected application."""
        app_id = self.get_selected_application_id()
        if not app_id:
            return

        # Get application details for confirmation message
        row = self.table.selectedItems()[0].row()
        job_title = self.table.item(row, 1).text()
        company = self.table.item(row, 2).text()

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete this application?\n\nTitle: {job_title}\nCompany: {company}\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                service = ApplicationService()
                success = service.delete(app_id)

                if success:
                    self.main_window.show_status_message(f"Application {app_id} deleted successfully")
                    self.refresh_data()
                else:
                    self.main_window.show_status_message(f"Failed to delete application {app_id}")
            except Exception as e:
                logger.error(f"Error deleting application: {e}", exc_info=True)
                self.main_window.show_status_message(f"Error: {str(e)}")

    @pyqtSlot(QTableWidgetItem)
    def on_row_double_clicked(self, item) -> None:
        """Handle row double click to open application details."""
        row = item.row()
        app_id = int(self.table.item(row, 0).text())
        dialog = ApplicationDetailDialog(self, app_id)
        dialog.exec()
        self.refresh_data()
