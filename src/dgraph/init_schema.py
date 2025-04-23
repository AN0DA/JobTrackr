"""Initialize Dgraph schema."""

import sys
import logging

# Add parent directory to path so we can import from api
sys.path.append('')

from src.api.db.schema import initialize_schema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for schema initialization."""
    logger.info("Starting schema initialization...")

    # Initialize schema
    if initialize_schema():
        logger.info("Schema initialization completed successfully.")
        return 0
    else:
        logger.error("Schema initialization failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
