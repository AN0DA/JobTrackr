"""Database connection and session management."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.db.settings import Settings

# Create engine once at module level
settings = Settings()
engine = create_engine(f"sqlite:///{settings.get('database_path')}")

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Generator[Session]:
    """Provide a transactional scope around a series of operations.

    Yields:
        Session: SQLAlchemy session
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def change_database(db_path: str) -> None:
    """Change the database connection to use a different database file.

    This should be called after settings are updated with a new database path.

    Args:
        db_path (str): Path to the new database file.
    """
    global engine, SessionLocal

    # Create a new engine with the updated path
    engine = create_engine(f"sqlite:///{db_path}")

    # Update the sessionmaker to use the new engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # No need to call init_db() as Alembic will handle migrations
    # the next time the application starts


# The init_db function is no longer needed as migrations are now handled by Alembic
# Migration-related functions are now in scripts/migration_manager.py
