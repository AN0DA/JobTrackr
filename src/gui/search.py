from PyQt6.QtCore import Qt
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

from src.gui.components.data_table import DataTable
from src.gui.dialogs.application_detail import ApplicationDetailDialog
from src.services.application_service import ApplicationService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SearchDialog(QDialog):
    """Dialog for searching applications."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.main_window = parent

        self.setWindowTitle("Search Applications")
        self.resize(600, 400)

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the search dialog UI."""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Search Applications")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Search form
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search term...")
        self.search_input.returnPressed.connect(self.perform_search)
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        # Results table
        self.results_table = DataTable(0, ["ID", "Job Title", "Company", "Position", "Status"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.doubleClicked.connect(self.on_row_double_clicked)
        layout.addWidget(self.results_table)

        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_button)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # Focus the search input
        self.search_input.setFocus()

    def perform_search(self) -> None:
        """Search for applications matching the search term."""
        search_term = self.search_input.text().strip()

        if not search_term:
            if self.main_window:
                self.main_window.show_status_message("Please enter a search term")
            return

        try:
            if self.main_window:
                self.main_window.show_status_message(f"Searching for '{search_term}'...")

            service = ApplicationService()
            results = service.search_applications(search_term)

            self.results_table.setRowCount(0)

            for i, app in enumerate(results):
                self.results_table.insertRow(i)
                self.results_table.setItem(i, 0, QTableWidgetItem(str(app["id"])))
                self.results_table.setItem(i, 1, QTableWidgetItem(app["job_title"]))

                company_name = app.get("company", {}).get("name", "")
                self.results_table.setItem(i, 2, QTableWidgetItem(company_name))

                self.results_table.setItem(i, 3, QTableWidgetItem(app["position"]))
                self.results_table.setItem(i, 4, QTableWidgetItem(app["status"]))

            count = len(results)
            if self.main_window:
                self.main_window.show_status_message(f"Found {count} result{'s' if count != 1 else ''}")

        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Search error: {str(e)}")

    def on_row_double_clicked(self, index) -> None:
        """Open the selected application."""
        app_id = int(self.results_table.item(index.row(), 0).text())

        # Close search dialog
        self.accept()

        # Open application detail
        dialog = ApplicationDetailDialog(self.main_window, app_id)
        dialog.exec()
