import functools
import traceback
from collections.abc import Callable
from typing import Any, TypeVar, cast

from src.db.database import get_session
from src.utils.logging import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def db_operation(func: Callable[..., F]) -> Callable[..., F]:
    """Decorator to handle database session management for service methods.

    This decorator creates a database session, passes it to the decorated function,
    and handles commit/rollback as appropriate.

    Args:
        func: The function to decorate.

    Returns:
        The decorated function.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        session = get_session()
        try:
            result = func(*args, **kwargs, session=session)
            session.commit()
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            session.rollback()
            raise
        finally:
            session.close()

    return wrapper


def error_handler(func: F) -> F:
    """Decorator to handle and log errors in UI operations."""

    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
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

    return cast(F, wrapper)
