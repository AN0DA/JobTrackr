#!/usr/bin/env python3

"""Database management for JobTrackr."""

import os
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from alembic import command
from alembic.config import Config

from src.db.models import Base
from src.db.settings import Settings
from src.utils.logging import get_logger

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
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    response = messagebox.askyesno(
        "Database Update",
        "Database schema updates are available. Do you want to update the database now?\n\n"
        "Choosing 'No' may cause the application to malfunction.",
        icon=messagebox.WARNING
    )
    
    root.destroy()
    return response


def run_migrations() -> bool:
    """Run database migrations.
    
    Returns:
        bool: True if migrations were successful, False otherwise.
    """
    try:
        # Get the path to alembic.ini
        alembic_ini_path = os.path.join(os.path.dirname(__file__), '..', '..', 'alembic.ini')
        
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
        # For now, we'll always prompt for updates
        # In the future, we could check the current migration version
        if show_migration_dialog():
            return run_migrations()
        
        logger.warning("User chose not to run migrations")
        return False
        
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False 