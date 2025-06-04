from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.db.settings import Settings

settings = Settings()
engine = create_engine(f"sqlite:///{settings.get('database_path')}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Session:
    """
    Get a new SQLAlchemy database session.

    Returns:
        Session: A SQLAlchemy session object for database operations.
    """
    session = SessionLocal()
    try:
        return session
    except Exception:
        session.rollback()
        raise


def change_database(db_path: str) -> None:
    """
    Change the database connection to use a different database file.

    This should be called after settings are updated with a new database path.

    Args:
        db_path (str): Path to the new database file.
    """
    global engine, SessionLocal

    engine = create_engine(f"sqlite:///{db_path}")

    # Update the sessionmaker to use the new engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # No need to call init_db() as Alembic will handle migrations
    # the next time the application starts
