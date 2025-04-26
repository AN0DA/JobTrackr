import os
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "database_path": "~/jobtracker_data/jobtracker.db",
    "export_directory": "~/jobtracker_data/exports",
    "check_updates": True,
    "save_window_size": True,
}


class Settings:
    """Class to handle application settings."""

    def __init__(self):
        # Define settings file location in user's home directory
        self.home_dir = os.path.expanduser("~")
        self.config_dir = os.path.join(self.home_dir, ".jobtracker")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self._config = {}

        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)

        # Load settings (or create default)
        self.load()

    def load(self) -> None:
        """Load settings from config file or create default if not exists."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    self._config = json.load(f)

                # Check for missing keys and apply defaults
                for key, default_value in DEFAULT_CONFIG.items():
                    if key not in self._config:
                        self._config[key] = default_value
            else:
                # Create default config
                self._config = DEFAULT_CONFIG.copy()
                self.save()

            # Expand paths with ~ to user's home directory
            for key in ["database_path", "export_directory"]:
                if self._config[key].startswith("~"):
                    self._config[key] = os.path.expanduser(self._config[key])

        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            self._config = DEFAULT_CONFIG.copy()

    def save(self) -> None:
        """Save settings to config file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        self._config[key] = value
        self.save()

    def get_database_path(self) -> str:
        """Get the database path, ensuring directory exists."""
        db_path = self.get("database_path")
        db_dir = os.path.dirname(db_path)

        # Ensure database directory exists
        os.makedirs(db_dir, exist_ok=True)

        return db_path

    def get_export_directory(self) -> str:
        """Get the export directory, ensuring it exists."""
        export_dir = self.get("export_directory")

        # Ensure export directory exists
        os.makedirs(export_dir, exist_ok=True)

        return export_dir

    def database_exists(self) -> bool:
        """Check if the database file exists."""
        return os.path.exists(self.get_database_path())
