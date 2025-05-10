#!/usr/bin/env python3

"""Database management for JobTrackr."""

import os
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from src.db.settings import Settings
from src.utils.logging import get_logger

from PyQt6.QtWidgets import QApplication, QMessageBox

logger = get_logger(__name__)


def ensure_db_directory(db_path: str) -> None:
    """Ensure the database directory exists."""
    db_dir = os.path.dirname(db_path)
    if db_dir:
        Path(db_dir).mkdir(parents=True, exist_ok=True)


def show_migration_dialog() -> bool:
    """Show a dialog asking the user if they want to run migrations.

    Returns:
        bool: True if the user chooses to run migrations, False otherwise.
    """
    # Ensure a QApplication exists
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        created_app = True
    else:
        created_app = False

    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Warning)
    msg_box.setWindowTitle("Database Update")
    msg_box.setText(
        "Database schema updates are available. Do you want to update the database now?\n\n"
        "Choosing 'No' may cause the application to malfunction."
    )
    msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
    result = msg_box.exec()

    if created_app:
        app.quit()

    return result == QMessageBox.StandardButton.Yes


def run_migrations() -> bool:
    """Run database migrations.

    Returns:
        bool: True if migrations were successful, False otherwise.
    """
    try:
        # Get the path to alembic.ini
        alembic_ini_path = os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini")

        # Create Alembic configuration
        alembic_cfg = Config(alembic_ini_path)

        # Run migrations
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        return False


def check_and_run_migrations() -> bool:
    """Check if migrations are needed and run them if necessary.

    Returns:
        bool: True if the application should continue, False if it should exit.
    """
    try:
        # Get database path from settings
        settings = Settings()
        db_path = settings.get("database_path")

        # Ensure database directory exists
        ensure_db_directory(db_path)

        # Create database engine
        engine = create_engine(f"sqlite:///{db_path}")

        # Check if database exists and has tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if not tables:
            # Database is empty, run migrations to create schema
            logger.info("Database is empty. Running initial migration...")
            return run_migrations()

        # Database exists, check if it needs updates
        # Get the path to alembic.ini
        alembic_ini_path = os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini")

        # Create Alembic configuration
        alembic_cfg = Config(alembic_ini_path)

        # Get current database revision
        with engine.connect() as conn:
            try:
                current_rev = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            except Exception:
                # If alembic_version table doesn't exist, we need to run migrations
                current_rev = None

        # Get latest revision from migrations
        script = ScriptDirectory.from_config(alembic_cfg)
        head_revision = script.get_current_head()

        # Only show dialog if migrations are needed
        if current_rev != head_revision:
            if show_migration_dialog():
                return run_migrations()
            logger.warning("User chose not to run migrations")
            return False

        return True

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False
