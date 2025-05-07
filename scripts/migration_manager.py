"""Migration manager for database schema updates."""
import os
import sys
import tkinter as tk
from tkinter import messagebox
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from alembic import command
import sqlalchemy as sa

# Get the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.db.settings import Settings
from src.db.models import Base


def get_alembic_config():
    """Get the alembic configuration."""
    alembic_cfg_path = os.path.join(project_root, "alembic.ini")
    
    if not os.path.exists(alembic_cfg_path):
        print(f"Error: alembic.ini not found at {alembic_cfg_path}")
        sys.exit(1)
    
    alembic_cfg = Config(alembic_cfg_path)
    
    # Make sure we're using the correct script location
    script_location = os.path.join(project_root, "alembic")
    alembic_cfg.set_main_option("script_location", script_location)
    
    return alembic_cfg


def get_database_url():
    """Get the database URL from settings."""
    settings = Settings()
    db_path = settings.get("database_path")
    return f"sqlite:///{db_path}"


def check_migrations_needed():
    """Check if there are any pending migrations that need to be applied.
    
    Returns:
        bool: True if migrations are needed, False otherwise.
    """
    alembic_cfg = get_alembic_config()
    script = ScriptDirectory.from_config(alembic_cfg)
    
    # Get the current head revision in the alembic scripts
    head_revision = script.get_current_head()
    
    # Connect to the database
    engine = sa.create_engine(get_database_url())
    
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        # Get the current revision in the database
        current_revision = context.get_current_revision()
    
    # If the current revision is not the head revision, migrations are needed
    return current_revision != head_revision


def run_migrations():
    """Apply all pending database migrations."""
    alembic_cfg = get_alembic_config()
    command.upgrade(alembic_cfg, "head")
    print("Migrations successfully applied.")


def create_revision(message):
    """Create a new migration revision.
    
    Args:
        message (str): Migration message/description.
    """
    alembic_cfg = get_alembic_config()
    command.revision(alembic_cfg, message=message, autogenerate=True)
    print(f"Created new migration revision with message: {message}")


def show_migration_dialog():
    """Show a dialog asking the user if they want to run migrations.
    
    Returns:
        bool: True if the user chooses to run migrations, False otherwise.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    response = messagebox.askyesno(
        "Database Migration",
        "Database schema updates are available. Do you want to update the database now?\n\n"
        "Choosing 'No' may cause the application to malfunction.",
        icon=messagebox.WARNING
    )
    
    root.destroy()
    return response


def check_and_run_migrations(force=False):
    """Check if migrations are needed and run them if necessary.
    
    Args:
        force (bool): If True, run migrations without prompting.
        
    Returns:
        bool: True if the application should continue, False if it should exit.
    """
    if check_migrations_needed():
        if force:
            run_migrations()
            return True
        
        # Show dialog and get user response
        run_approved = show_migration_dialog()
        
        if run_approved:
            run_migrations()
            return True
        else:
            return False  # User chose not to run migrations, exit app
    
    # No migrations needed
    return True


if __name__ == "__main__":
    # For testing purposes
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        needs_migration = check_migrations_needed()
        print(f"Migrations needed: {needs_migration}")
    elif len(sys.argv) > 2 and sys.argv[1] == "--revision":
        create_revision(sys.argv[2])
    else:
        continue_app = check_and_run_migrations()
        print(f"Continue application: {continue_app}")