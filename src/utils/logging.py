import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.config import LOG_BACKUP_COUNT, LOG_DIR, LOG_FORMAT, LOG_LEVEL, LOG_MAX_SIZE


def setup_logging(app_name: str = "jobtrackr") -> logging.Logger:
    """Set up application logging with console and file handlers.

    Args:
        app_name: Name of the application (used for logger name)

    Returns:
        The configured logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs(LOG_DIR, exist_ok=True)

    # Generate log filename with date
    today = datetime.now().strftime("%Y-%m-%d")
    log_filename = Path(LOG_DIR) / f"{app_name}_{today}.log"

    # Create root logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # Create formatters
    file_formatter = logging.Formatter(LOG_FORMAT)
    console_formatter = logging.Formatter("[%(levelname)s] %(message)s")

    # Create and configure file handler (with rotation)
    file_handler = RotatingFileHandler(
        log_filename, maxBytes=LOG_MAX_SIZE, backupCount=LOG_BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setLevel(getattr(logging, LOG_LEVEL))
    file_handler.setFormatter(file_formatter)

    # Create and configure console handler (less verbose)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Console gets INFO and above
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Log startup message
    logger.info(f"Logging initialized - writing to {log_filename}")

    return logger


# Create a default application logger
app_logger = setup_logging()


def get_logger(module_name: str) -> logging.Logger:
    """Get a logger for a specific module.

    Args:
        module_name: Usually __name__ from the calling module

    Returns:
        A logger instance with the module name
    """
    return logging.getLogger(f"jobtrackr.{module_name}")
