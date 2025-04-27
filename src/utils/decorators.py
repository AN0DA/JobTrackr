import functools
import traceback

from src.db.database import get_session
from src.utils.logging import get_logger

logger = get_logger(__name__)


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
            logger.error(f"Database error in {func.__name__}: {e}", exc_info=True)
            raise
        finally:
            session.close()

    return wrapper


def error_handler(func):
    """Decorator to handle and log errors in UI operations."""

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            # Get a more detailed traceback
            tb = traceback.format_exc()

            # Log the error
            logger.error(f"Error in {func.__name__}: {e}\n{tb}")

            # Set application status
            if hasattr(self, "update_status"):
                self.update_status(f"Error: {str(e)}")
            elif hasattr(self, "app") and hasattr(self.app, "sub_title"):
                self.app.sub_title = f"Error: {str(e)}"

            # Re-raise if needed (can be commented out to prevent crashes)
            # raise

    return wrapper
