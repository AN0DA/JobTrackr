#!/usr/bin/env python3

"""Main entry point for the JobTrackr application."""

import sys

from PyQt6.QtWidgets import QApplication

from src.db.manager import check_and_run_migrations
from src.gui.main_window import MainWindow
from src.utils.logging import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Run the GUI application."""
    try:
        # Check and run migrations if needed
        if not check_and_run_migrations():
            logger.error("Database migration failed or was rejected. Exiting...")
            sys.exit(1)

        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("JobTrackr")
        app.setStyle("Fusion")  # Consistent look across platforms

        # Create and show the main window
        window = MainWindow()
        window.show()

        # Run the application
        sys.exit(app.exec())

    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
