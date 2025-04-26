import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from src.db.settings import Settings

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)

# Create base model class
Base = declarative_base()

# Global variables
engine = None
SessionLocal = None
settings = Settings()


def init_db(db_path=None):
    """Initialize the database, creating tables if they don't exist."""
    global engine, SessionLocal

    try:
        # Use specified path or get from settings
        if db_path is None:
            db_path = settings.get_database_path()

        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)

        # Create database engine
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

        # Create session factory
        session_factory = sessionmaker(bind=engine)
        SessionLocal = scoped_session(session_factory)

        # Create tables if they don't exist
        Base.metadata.create_all(engine)
        logger.info(f"Database initialized successfully at {db_path}")
        return True

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False


def get_session():
    """Get a database session."""
    if SessionLocal is None:
        init_db()

    session = SessionLocal()
    try:
        return session
    except:
        session.close()
        raise


def change_database(new_path):
    """Change the database location."""
    global engine, SessionLocal

    # Close existing connections
    if SessionLocal:
        SessionLocal.remove()

    if engine:
        engine.dispose()

    # Update settings
    settings.set("database_path", new_path)

    # Reinitialize with new path
    return init_db(new_path)
