from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from src.config import ApplicationStatus
from src.services.application_service import ApplicationService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class StatusTransitionDialog(QDialog):
    """Dialog for changing application status."""

    def __init__(self, parent=None, application_id=None, current_status=None):
        super().__init__(parent)
        self.main_window = parent.main_window if parent else None
        self.application_id = application_id
        self.current_status = current_status

        self.setWindowTitle("Change Application Status")
        self.resize(400, 300)

        self._init_ui()

    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)

        # Dialog title
        title_label = QLabel(f"Change Status for Application #{self.application_id}")
        title_font = QLabel().font()
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Form layout for status selection
        form_layout = QFormLayout()

        # Current status (read-only)
        current_status_label = QLabel(self.current_status)
        form_layout.addRow("Current Status:", current_status_label)

        # New status dropdown
        self.new_status_select = QComboBox()
        for status in ApplicationStatus:
            self.new_status_select.addItem(status.value)
            if status.value == self.current_status:
                self.new_status_select.setCurrentText(status.value)

        form_layout.addRow("New Status:", self.new_status_select)

        # Notes field
        form_layout.addRow("Add Note:", QLabel())
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Optional note about this status change")
        form_layout.addWidget(self.notes_input)

        layout.addLayout(form_layout)

        # Button row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.save_status_change)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    @pyqtSlot()
    def save_status_change(self):
        """Save the status change."""
        try:
            new_status = self.new_status_select.currentText()
            note = self.notes_input.toPlainText().strip()

            if new_status == self.current_status:
                if self.main_window:
                    self.main_window.show_status_message("Status unchanged")
                self.accept()
                return

            # Update application status
            service = ApplicationService()
            service.update(self.application_id, {"status": new_status})

            # Create interaction record for the status change
            if note:
                service.add_interaction(
                    {
                        "application_id": self.application_id,
                        "type": "NOTE",
                        "notes": f"Status changed from {self.current_status} to {new_status}. Note: {note}",
                        "date": datetime.now().isoformat(),
                    }
                )

            if self.main_window:
                self.main_window.show_status_message(f"Status updated to {new_status}")

            self.accept()

        except Exception as e:
            logger.error(f"Error updating status: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error updating status: {str(e)}")
