import os

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.db.database import change_database
from src.db.settings import Settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SettingsDialog(QDialog):
    """Dialog for application settings."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.main_window = parent
        self.settings = Settings()

        self.setWindowTitle("Settings")
        self.resize(500, 400)

        self._init_ui()
        self._load_settings()

    def _init_ui(self) -> None:
        """Initialize the settings dialog UI."""
        layout = QVBoxLayout(self)

        # Database settings
        db_group = QGroupBox("Database Settings")
        db_layout = QFormLayout()

        self.db_path_input = QLineEdit()
        db_path_layout = QHBoxLayout()
        db_path_layout.addWidget(self.db_path_input)
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.on_browse_db)
        db_path_layout.addWidget(self.browse_button)
        db_layout.addRow("Database Path:", db_path_layout)

        self.db_status = QLabel()
        db_layout.addRow("Current Status:", self.db_status)

        self.apply_db_button = QPushButton("Apply Database Changes")
        self.apply_db_button.clicked.connect(self.on_apply_db_changes)
        db_layout.addRow("", self.apply_db_button)

        db_group.setLayout(db_layout)
        layout.addWidget(db_group)

        # General settings
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout()

        self.updates_checkbox = QCheckBox()
        general_layout.addRow("Check for updates:", self.updates_checkbox)

        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        # Logging settings
        log_group = QGroupBox("Logging Settings")
        log_layout = QFormLayout()

        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_layout.addRow("Log Level:", self.log_level)

        self.log_dir = QLabel()
        log_layout.addRow("Log Directory:", self.log_dir)

        self.view_logs_button = QPushButton("View Logs")
        self.view_logs_button.clicked.connect(self.on_view_logs)
        log_layout.addRow("", self.view_logs_button)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # Button row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.on_save_settings)
        btn_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_button)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _load_settings(self) -> None:
        """Load current settings values."""
        # Database path
        db_path = self.settings.get("database_path")
        self.db_path_input.setText(db_path)

        # Database status
        if self.settings.database_exists():
            self.db_status.setText("Database file exists")
            self.db_status.setStyleSheet("color: green")
        else:
            self.db_status.setText("Database file does not exist")
            self.db_status.setStyleSheet("color: red")

        # General settings
        self.updates_checkbox.setChecked(self.settings.get("check_updates", True))

        # Log settings
        from src.config import LOG_DIR, LOG_LEVEL

        index = self.log_level.findText(LOG_LEVEL)
        if index >= 0:
            self.log_level.setCurrentIndex(index)

        self.log_dir.setText(str(LOG_DIR))

    def on_browse_db(self) -> None:
        """Browse for database file."""
        current_path = self.db_path_input.text()
        initial_dir = os.path.dirname(os.path.expanduser(current_path))

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Database Location", initial_dir, "Database Files (*.db);;All Files (*)"
        )

        if file_path:
            self.db_path_input.setText(file_path)

    def on_apply_db_changes(self) -> None:
        """Apply database path changes."""
        new_db_path = self.db_path_input.text()

        # Expand user path if needed
        if new_db_path.startswith("~"):
            new_db_path = os.path.expanduser(new_db_path)

        try:
            # Check if directory exists or can be created
            db_dir = os.path.dirname(new_db_path)
            os.makedirs(db_dir, exist_ok=True)

            # Change database path
            if change_database(new_db_path):
                if self.main_window:
                    self.main_window.show_status_message(f"Database changed to {new_db_path}")

                # Update status
                if os.path.exists(new_db_path):
                    self.db_status.setText("Database file exists")
                    self.db_status.setStyleSheet("color: green")
                else:
                    self.db_status.setText("New database created")
                    self.db_status.setStyleSheet("color: green")
            else:
                if self.main_window:
                    self.main_window.show_status_message("Failed to change database")
                self.db_status.setText("Error changing database")
                self.db_status.setStyleSheet("color: red")

        except Exception as e:
            logger.error(f"Error changing database: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error: {str(e)}")
            self.db_status.setText(f"Error: {str(e)}")
            self.db_status.setStyleSheet("color: red")

    def on_view_logs(self) -> None:
        """Open log directory."""
        import webbrowser

        from src.config import LOG_DIR

        log_dir = str(LOG_DIR)
        if os.path.exists(log_dir):
            webbrowser.open(f"file://{log_dir}")
            if self.main_window:
                self.main_window.show_status_message(f"Opening log directory: {log_dir}")
        else:
            if self.main_window:
                self.main_window.show_status_message("Log directory does not exist yet")
            QMessageBox.information(self, "Logs", "Log directory does not exist yet.")

    def on_save_settings(self) -> None:
        """Save all settings."""
        try:
            # Get values
            db_path = self.db_path_input.text()
            check_updates = self.updates_checkbox.isChecked()

            # Save settings
            self.settings.set("database_path", db_path)
            self.settings.set("check_updates", check_updates)

            if self.main_window:
                self.main_window.show_status_message("Settings saved")

            self.accept()

        except Exception as e:
            logger.error(f"Error saving settings: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_status_message(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error saving settings: {str(e)}")
