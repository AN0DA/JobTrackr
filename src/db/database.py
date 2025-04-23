import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create database directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Create database engine
engine = create_engine('sqlite:///data/jobtracker.db', connect_args={'check_same_thread': False})

# Create session factory
session_factory = sessionmaker(bind=engine)
SessionLocal = scoped_session(session_factory)

# Create base model class
Base = declarative_base()


def init_db():
    """Initialize the database, creating tables if they don't exist."""
    try:
        Base.metadata.create_all(engine)
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False


def get_session():
    """Get a database session."""
    session = SessionLocal()
    try:
        return session
    except:
        session.close()
        raise
