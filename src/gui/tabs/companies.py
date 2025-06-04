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

from src.config import CompanyType
from src.gui.components.data_table import DataTable
from src.gui.dialogs.company_detail import CompanyDetailDialog
from src.gui.dialogs.company_form import CompanyForm
from src.services.company_service import CompanyService
from src.utils.logging import get_logger
from src.db.database import get_session

logger = get_logger(__name__)


class CompaniesTab(QWidget):
    """
    Tab for managing companies.

    Provides UI and logic for listing, searching, filtering, viewing, editing, and deleting companies.
    """

    def __init__(self, parent=None) -> None:
        """
        Initialize the companies tab.

        Args:
            parent: Parent widget (main window).
        """
        super().__init__(parent)
        self.main_window = parent
        self.company_type_filter = None
        self._init_ui()
        self.load_companies()

    def _init_ui(self) -> None:
        """
        Initialize the companies tab UI components and layout.
        """
        layout = QVBoxLayout(self)

        # Header section with filters
        header_layout = QHBoxLayout()

        # Type filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("All")
        for company_type in CompanyType:
            self.type_filter.addItem(company_type.value)
        self.type_filter.currentTextChanged.connect(self.on_type_filter_changed)
        filter_layout.addWidget(self.type_filter)

        # Search box
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search companies...")
        self.search_input.returnPressed.connect(self.on_search)
        self.search_button = QPushButton("🔍")
        self.search_button.clicked.connect(self.on_search)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)

        # New company button
        self.new_company_button = QPushButton("New Company")
        self.new_company_button.clicked.connect(self.on_new_company)

        # Add all components to header
        header_layout.addLayout(filter_layout)
        header_layout.addLayout(search_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.new_company_button)

        layout.addLayout(header_layout)

        # Table for companies
        self.table = DataTable(0, ["ID", "Name", "Industry", "Type", "Website", "Size"])  # 0 rows, 6 columns
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemDoubleClicked.connect(self.on_row_double_clicked)
        layout.addWidget(self.table)

        # Action buttons
        actions_layout = QHBoxLayout()
        self.view_button = QPushButton("View")
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        self.view_button.clicked.connect(self.on_view_company)
        self.edit_button.clicked.connect(self.on_edit_company)
        self.delete_button.clicked.connect(self.on_delete_company)

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

    def load_companies(self, company_type=None) -> None:
        """
        Load companies, optionally filtered by type.

        Args:
            company_type: Type to filter companies by, or None for all.
        """
        try:
            self.main_window.show_status_message("Loading companies...")
            self.company_type_filter = company_type

            service = CompanyService()
            session = get_session()
            try:
                companies = service.get_all()
            finally:
                session.close()

            # Apply type filter if specified
            if company_type and company_type != "All":
                companies = [c for c in companies if c.get("type") == company_type]

            # Clear and update table
            self.table.setRowCount(0)

            if not companies:
                self.main_window.show_status_message("No companies found")
                return

            for i, company in enumerate(companies):
                self.table.insertRow(i)

                # Add items to the row
                self.table.setItem(i, 0, QTableWidgetItem(str(company["id"])))
                self.table.setItem(i, 1, QTableWidgetItem(company["name"]))

                industry = company.get("industry", "")
                self.table.setItem(i, 2, QTableWidgetItem(industry or ""))

                company_type_val = company.get("type", "")
                self.table.setItem(i, 3, QTableWidgetItem(company_type_val or ""))

                website = company.get("website", "")
                self.table.setItem(i, 4, QTableWidgetItem(website or ""))

                size = company.get("size", "")
                self.table.setItem(i, 5, QTableWidgetItem(size or ""))

            count = len(companies)
            self.main_window.show_status_message(f"Loaded {count} compan{'ies' if count != 1 else 'y'}")

        except Exception as e:
            logger.error(f"Error loading companies: {e}", exc_info=True)
            self.main_window.show_status_message(f"Error loading companies: {str(e)}")

    def search_companies(self, search_term) -> None:
        """
        Search companies by name or industry, and update the table.

        Args:
            search_term: The search string to filter companies.
        """
        try:
            if not search_term:
                self.load_companies(self.company_type_filter)
                return

            self.main_window.show_status_message(f"Searching for '{search_term}'...")

            service = CompanyService()
            all_companies = service.get_all()

            # Simple case-insensitive search
            search_term = search_term.lower()
            filtered_companies = [
                c
                for c in all_companies
                if search_term in c["name"].lower()
                or (c.get("industry") and search_term in c.get("industry", "").lower())
                or (c.get("notes") and search_term in c.get("notes", "").lower())
            ]

            # Apply type filter if active
            if self.company_type_filter and self.company_type_filter != "All":
                filtered_companies = [c for c in filtered_companies if c.get("type") == self.company_type_filter]

            # Update table
            self.table.setRowCount(0)

            if not filtered_companies:
                self.main_window.show_status_message(f"No companies found matching '{search_term}'")
                return

            for i, company in enumerate(filtered_companies):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(str(company["id"])))
                self.table.setItem(i, 1, QTableWidgetItem(company["name"]))
                self.table.setItem(i, 2, QTableWidgetItem(company.get("industry") or ""))
                self.table.setItem(i, 3, QTableWidgetItem(company.get("type") or ""))
                self.table.setItem(i, 4, QTableWidgetItem(company.get("website") or ""))
                self.table.setItem(i, 5, QTableWidgetItem(company.get("size") or ""))

            count = len(filtered_companies)
            self.main_window.show_status_message(
                f"Found {count} compan{'ies' if count != 1 else 'y'} matching '{search_term}'"
            )

        except Exception as e:
            logger.error(f"Error searching companies: {e}", exc_info=True)
            self.main_window.show_status_message(f"Search error: {str(e)}")

    def get_selected_company_id(self) -> int | None:
        """
        Get the ID of the currently selected company.

        Returns:
            The selected company's ID, or None if no selection.
        """
        selected_items = self.table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        id_item = self.table.item(row, 0)
        if id_item:
            return int(id_item.text())
        return None

    def refresh_data(self) -> None:
        """
        Refresh the companies data in the table.
        """
        self.load_companies(self.company_type_filter)

    @pyqtSlot()
    def on_selection_changed(self) -> None:
        """
        Enable or disable action buttons based on table selection.
        """
        has_selection = bool(self.table.selectedItems())
        self.view_button.setEnabled(has_selection)
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    @pyqtSlot(str)
    def on_type_filter_changed(self, company_type) -> None:
        """
        Handle changes to the type filter dropdown.

        Args:
            company_type: The selected company type from the filter.
        """
        if company_type == "All":
            self.load_companies(None)
        else:
            self.load_companies(company_type)

    @pyqtSlot()
    def on_search(self) -> None:
        """
        Handle search button click or return key in search box.
        """
        search_term = self.search_input.text().strip()
        self.search_companies(search_term)

    @pyqtSlot()
    def on_new_company(self) -> None:
        """
        Open dialog to create a new company and refresh the table on success.
        """
        dialog = CompanyForm(self)
        if dialog.exec():
            self.refresh_data()

    @pyqtSlot()
    def on_view_company(self) -> None:
        """
        Open dialog to view the selected company's details.
        """
        company_id = self.get_selected_company_id()
        if company_id:
            dialog = CompanyDetailDialog(self, company_id)
            dialog.exec()
            self.refresh_data()

    @pyqtSlot()
    def on_edit_company(self) -> None:
        """
        Open dialog to edit the selected company and refresh the table on success.
        """
        company_id = self.get_selected_company_id()
        if company_id:
            dialog = CompanyForm(self, company_id)
            if dialog.exec():
                self.refresh_data()

    @pyqtSlot()
    def on_delete_company(self) -> None:
        """
        Delete the selected company and refresh the table on success.
        """
        company_id = self.get_selected_company_id()
        if not company_id:
            return

        # Get company name for confirmation message
        row = self.table.selectedItems()[0].row()
        company_name = self.table.item(row, 1).text()

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete company '{company_name}'?\n\nThis will remove all relationships with this company. This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                service = CompanyService()
                success = service.delete(company_id)

                if success:
                    self.main_window.show_status_message(f"Company '{company_name}' deleted successfully")
                    self.refresh_data()
                else:
                    self.main_window.show_status_message(f"Failed to delete company {company_id}")
            except Exception as e:
                logger.error(f"Error deleting company: {e}", exc_info=True)
                self.main_window.show_status_message(f"Error: {str(e)}")

    @pyqtSlot(QTableWidgetItem)
    def on_row_double_clicked(self, item) -> None:
        """
        Open dialog to view the company's details when a row is double clicked.
        """
        row = item.row()
        company_id = int(self.table.item(row, 0).text())
        dialog = CompanyDetailDialog(self, company_id)
        dialog.exec()
        self.refresh_data()
