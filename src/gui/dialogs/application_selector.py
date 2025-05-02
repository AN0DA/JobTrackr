from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from src.gui.components.data_table import DataTable
from src.services.application_service import ApplicationService


class ApplicationSelectorDialog(QDialog):
    """Dialog for selecting an application to associate with a contact."""

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

        # Instructions
        layout.addWidget(QLabel("Select an application to associate with this contact:"))

        # Applications table
        self.table = DataTable(0, ["ID", "Job Title", "Company", "Status"])  # 0 rows, 4 columns
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.doubleClicked.connect(self.on_select)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        self.select_btn = QPushButton("Select")
        self.select_btn.clicked.connect(self.on_select)
        self.select_btn.setEnabled(False)

        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.select_btn)

        layout.addLayout(btn_layout)

        # Connect selection signal
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

    def load_applications(self):
        """Load applications into the table."""
        try:
            service = ApplicationService()
            applications = service.get_applications(limit=100)

            for i, app in enumerate(applications):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(str(app["id"])))
                self.table.setItem(i, 1, QTableWidgetItem(app["job_title"]))

                company_name = app.get("company", {}).get("name", "")
                self.table.setItem(i, 2, QTableWidgetItem(company_name))

                self.table.setItem(i, 3, QTableWidgetItem(app["status"]))
        except Exception as e:
            if self.main_window:
                self.main_window.show_status_message(f"Error loading applications: {str(e)}")

    def on_selection_changed(self):
        """Handle table selection changes."""
        self.select_btn.setEnabled(bool(self.table.selectedItems()))

    def on_select(self):
        """Handle application selection."""
        selected_items = self.table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            self.selected_application_id = int(self.table.item(row, 0).text())
            self.accept()
