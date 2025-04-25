import functools
import logging
from src.db.database import get_session

logger = logging.getLogger(__name__)


def db_operation(func):
    """Decorator for database operations with consistent error handling."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session = get_session()
        try:
            result = func(*args, **kwargs, session=session)
            return result
        except Exception as e:
            session.rollback()
            logger.error(f"Database error in {func.__name__}: {e}")
            raise
        finally:
            session.close()

    return wrapper
