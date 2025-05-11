from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget


class DataTable(QTableWidget):
    """Standardized table widget for consistent data display."""

    row_double_clicked = pyqtSignal(int)  # Emits row id when double-clicked

    def __init__(self, rows, columns, parent=None):
        """Initialize the table with standard configuration.

        Args:
            columns: List of column names
            parent: Parent widget
        """
        super().__init__(rows, len(columns), parent)

        # Set column headers
        self.setHorizontalHeaderLabels(columns)

        # Configure header and selection behavior
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # Style
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E5E7EB;
                gridline-color: #E5E7EB;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #F3F4F6;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #D1D5DB;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #EFF6FF;
                color: #1F2937;
            }
        """)

        # Connect double-click signal
        self.cellDoubleClicked.connect(self._on_cell_double_clicked)

    def _on_cell_double_clicked(self, row, column):
        """Handle cell double click."""
        id_item = self.item(row, 0)
        if id_item:
            self.row_double_clicked.emit(int(id_item.text()))
