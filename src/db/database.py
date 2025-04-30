import os
from typing import TypeVar

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

from src.db.settings import Settings
from src.utils.logging import get_logger

# Set up module logger
logger = get_logger(__name__)

# Create base model class with proper type definition
Base = declarative_base()
# Define a type variable for BaseModel classes
ModelType = TypeVar("ModelType", bound=Base)

# Global variables
engine = None
SessionLocal: scoped_session | None = None
settings = Settings()


def init_db(db_path: str | None = None) -> bool:
    """Initialize the database, creating tables if they don't exist."""
    global engine, SessionLocal

    try:
        # Use specified path or get from settings
        if db_path is None:
            db_path = settings.get_database_path()

        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)

        # Log database location
        logger.info(f"Initializing database at {db_path}")

        # Create database engine
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

        # Create session factory
        session_factory = sessionmaker(bind=engine)
        SessionLocal = scoped_session(session_factory)

        # Create tables if they don't exist
        Base.metadata.create_all(engine)
        logger.info("Database tables created/verified successfully")
        return True

    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        return False


def get_session() -> scoped_session:
    """Get a database session."""
    global SessionLocal

    if SessionLocal is None:
        logger.debug("No active session, initializing database")
        init_db()

    if SessionLocal is None:  # Check again after init_db
        raise RuntimeError("Failed to initialize database session")

    logger.debug("Database session created")
    return SessionLocal


def change_database(new_path: str) -> bool:
    """Change the database location."""
    global engine, SessionLocal

    logger.info(f"Changing database to {new_path}")

    # Close existing connections
    if SessionLocal:
        logger.debug("Closing existing session")
        SessionLocal.remove()

    if engine:
        logger.debug("Disposing engine")
        engine.dispose()

    # Update settings
    settings.set("database_path", new_path)

    # Reinitialize with new path
    result = init_db(new_path)

    if result:
        logger.info(f"Database changed successfully to {new_path}")
    else:
        logger.error(f"Failed to change database to {new_path}")

    return result
