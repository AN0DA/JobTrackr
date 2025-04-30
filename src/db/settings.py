import json
import os
from typing import Any

from src.config import CONFIG_DIR, DEFAULT_SETTINGS
from src.utils.logging import get_logger

# Set up module logger
logger = get_logger(__name__)


class Settings:
    """Class to handle application settings."""

    def __init__(self) -> None:
        # Define settings file location from central config
        self.config_dir = CONFIG_DIR
        self.config_file = self.config_dir / "config.json"
        self._config: dict[str, Any] = {}  # Add proper type annotation

        # Load settings (or create default)
        self.load()

    def load(self) -> None:
        """Load settings from config file or create default if not exists."""
        try:
            if self.config_file.exists():
                logger.debug(f"Loading settings from {self.config_file}")
                with open(self.config_file) as f:
                    self._config = json.load(f)

                # Check for missing keys and apply defaults
                for key, default_value in DEFAULT_SETTINGS.items():
                    if key not in self._config:
                        logger.debug(f"Adding missing setting: {key} = {default_value}")
                        self._config[key] = default_value
            else:
                # Create default config
                logger.info(f"No settings file found, creating defaults at {self.config_file}")
                self._config = DEFAULT_SETTINGS.copy()
                self.save()

            # Expand paths with ~ to user's home directory
            for key in ["database_path", "export_directory"]:
                if isinstance(self._config[key], str) and self._config[key].startswith("~"):
                    self._config[key] = os.path.expanduser(self._config[key])
                    logger.debug(f"Expanded path for {key}: {self._config[key]}")

        except Exception as e:
            logger.error(f"Error loading settings: {e}", exc_info=True)
            self._config = DEFAULT_SETTINGS.copy()
            logger.info("Using default settings due to error")

    def save(self) -> None:
        """Save settings to config file."""
        try:
            logger.debug(f"Saving settings to {self.config_file}")
            with open(self.config_file, "w") as f:
                json.dump(self._config, f, indent=2)
            logger.debug("Settings saved successfully")
        except Exception as e:
            logger.error(f"Error saving settings: {e}", exc_info=True)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        value = self._config.get(key, default)
        logger.debug(f"Retrieved setting {key} = {value}")
        return value

    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        logger.info(f"Setting {key} = {value}")
        self._config[key] = value
        self.save()

    def get_database_path(self) -> str:
        """Get the database path, ensuring directory exists."""
        db_path = self.get("database_path")
        db_dir = os.path.dirname(db_path)

        # Ensure database directory exists
        os.makedirs(db_dir, exist_ok=True)
        logger.debug(f"Ensured database directory exists: {db_dir}")

        return db_path

    def get_export_directory(self) -> str:
        """Get the export directory, ensuring it exists."""
        export_dir = self.get("export_directory")

        # Ensure export directory exists
        os.makedirs(export_dir, exist_ok=True)
        logger.debug(f"Ensured export directory exists: {export_dir}")

        return export_dir

    def database_exists(self) -> bool:
        """Check if the database file exists."""
        exists = os.path.exists(self.get_database_path())
        logger.debug(f"Database exists check: {exists}")
        return exists
