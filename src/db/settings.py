import json
import os
from pathlib import Path
from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)


class Settings:
    """
    Handle application settings including database configuration.

    This class manages reading, writing, and accessing application settings
    that are stored in a JSON file. It provides methods to get, set, and retrieve
    all settings, as well as to obtain the database path. Settings are persisted
    automatically on change.
    """

    def __init__(self, settings_file: str | None = None):
        """
        Initialize settings from the settings file.

        Args:
            settings_file: Optional path to settings file. If None, uses default location.
        """
        self._settings = {
            "database_path": str(Path.home() / ".jobtrackr" / "jobtrackr.db"),
            "log_level": "INFO",
            "theme": "system",
            "default_view": "dashboard",
            "save_window_state": True,
            "auto_backup": True,
            "backup_frequency_days": 7,
            "check_updates": True,
        }

        if settings_file is None:
            self._settings_dir = Path.home() / ".jobtrackr"
            self._settings_file = self._settings_dir / "settings.json"
        else:
            self._settings_file = Path(settings_file)
            self._settings_dir = self._settings_file.parent

        os.makedirs(self._settings_dir, exist_ok=True)

        self._load_settings()

    def _load_settings(self) -> None:
        """
        Load settings from file, creating default file if it doesn't exist.

        If the settings file does not exist, a default settings file is created.
        Updates the internal settings dictionary with values from the file.
        """
        try:
            if self._settings_file.exists():
                with open(self._settings_file) as f:
                    loaded_settings = json.load(f)
                    self._settings.update(loaded_settings)
                    logger.debug(f"Settings loaded from {self._settings_file}")
            else:
                self._save_settings()
                logger.info(f"Created default settings file at {self._settings_file}")
        except Exception as e:
            logger.error(f"Error loading settings: {e}", exc_info=True)

    def _save_settings(self) -> None:
        """
        Save current settings to file.

        Writes the current settings dictionary to the settings file in JSON format.
        """
        try:
            with open(self._settings_file, "w") as f:
                json.dump(self._settings, f, indent=2)
            logger.debug(f"Settings saved to {self._settings_file}")
        except Exception as e:
            logger.error(f"Error saving settings: {e}", exc_info=True)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value by key.

        Args:
            key: The setting key to retrieve.
            default: Value to return if key doesn't exist.

        Returns:
            The setting value or default if not found.
        """
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a setting value and save to file.

        Args:
            key: The setting key to set.
            value: The value to set.
        """
        self._settings[key] = value
        self._save_settings()

    def get_all(self) -> dict[str, Any]:
        """
        Get all settings as a dictionary.

        Returns:
            A copy of the settings dictionary.
        """
        return self._settings.copy()

    def get_database_path(self) -> str:
        """
        Get the database file path from settings.

        Ensures the directory for the database exists before returning the path.

        Returns:
            Path to the database file.
        """
        db_path = self.get("database_path")

        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)

        return db_path

    def database_exists(self) -> bool:
        """
        Check if the database file exists at the current database path.
        Returns:
            True if the database file exists, False otherwise.
        """
        db_path = self.get("database_path")
        return os.path.exists(db_path)
