from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from src.services.application_service import ApplicationService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ApplicationSelectorDialog(QDialog):
    """Dialog for selecting an application to associate with a contact or other entity."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent.main_window if parent else None
        self.selected_application_id = None

        self.setWindowTitle("Select Application")
        self.resize(600, 400)

        self._init_ui()
        self.load_applications()

    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter job title, company name, etc.")
        self.search_input.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Applications table
        layout.addWidget(QLabel("Select an application:"))
        self.applications_table = QTableWidget(0, 5)
        self.applications_table.setHorizontalHeaderLabels(["ID", "Job Title", "Company", "Status", "Applied Date"])
        self.applications_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.applications_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.applications_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.applications_table.doubleClicked.connect(self.on_table_double_clicked)
        layout.addWidget(self.applications_table)

        # Bottom buttons
        button_layout = QHBoxLayout()
        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.on_select)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_applications(self, search_term=None):
        """Load applications with optional search filtering."""
        try:
            self.applications_table.setRowCount(0)

            # Get applications from service
            service = ApplicationService()
            applications = service.search(search_term) if search_term else service.get_all()

            if not applications:
                self.applications_table.insertRow(0)
                self.applications_table.setItem(0, 0, QTableWidgetItem("No applications found"))
                self.applications_table.setItem(0, 1, QTableWidgetItem(""))
                self.applications_table.setItem(0, 2, QTableWidgetItem(""))
                self.applications_table.setItem(0, 3, QTableWidgetItem(""))
                self.applications_table.setItem(0, 4, QTableWidgetItem(""))
                return

            # Populate table
            for i, app in enumerate(applications):
                self.applications_table.insertRow(i)

                # Store the application ID for later retrieval
                id_item = QTableWidgetItem(str(app.get("id", "")))
                id_item.setData(Qt.ItemDataRole.UserRole, app.get("id"))
                self.applications_table.setItem(i, 0, id_item)

                self.applications_table.setItem(i, 1, QTableWidgetItem(app.get("job_title", "")))

                # Get company name if available
                company_name = ""
                if app.get("company"):
                    company_name = app["company"].get("name", "")
                self.applications_table.setItem(i, 2, QTableWidgetItem(company_name))

                self.applications_table.setItem(i, 3, QTableWidgetItem(app.get("status", "")))

                # Format date
                date_str = ""
                if app.get("applied_date"):
                    date_str = app["applied_date"].split("T")[0]
                self.applications_table.setItem(i, 4, QTableWidgetItem(date_str))

        except Exception as e:
            logger.error(f"Error loading applications: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error loading applications: {str(e)}")

    @pyqtSlot(str)
    def on_search(self, text):
        """Handle search input changes."""
        if not text:
            self.load_applications()
        else:
            self.load_applications(text)

    @pyqtSlot()
    def on_select(self):
        """Handle select button click."""
        selected_rows = self.applications_table.selectedItems()
        if not selected_rows:
            if self.main_window:
                self.main_window.show_status_message("No application selected")
            return

        # Get the application ID from the first column
        app_id_item = self.applications_table.item(selected_rows[0].row(), 0)
        if not app_id_item or app_id_item.text() == "No applications found":
            return

        self.selected_application_id = app_id_item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    @pyqtSlot()
    def on_table_double_clicked(self, index):
        """Handle double-click on table row."""
        if self.applications_table.item(index.row(), 0).text() == "No applications found":
            return

        app_id_item = self.applications_table.item(index.row(), 0)
        self.selected_application_id = app_id_item.data(Qt.ItemDataRole.UserRole)
        self.accept()
