"""Application configuration and constants."""

import enum
import os
from pathlib import Path

# Application metadata
APP_NAME = "JobTrackr"
APP_VERSION = "0.1.0"

# File paths
HOME_DIR = Path.home()
CONFIG_DIR = HOME_DIR / ".jobtrackr"
DEFAULT_DATA_DIR = HOME_DIR / "jobtrackr_data"
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "jobtrackr.db"
DEFAULT_EXPORT_DIR = DEFAULT_DATA_DIR / "exports"

# Application settings defaults
DEFAULT_SETTINGS = {
    "database_path": str(DEFAULT_DB_PATH),
    "export_directory": str(DEFAULT_EXPORT_DIR),
    "check_updates": True,
    "save_window_size": True,
}

# Ensure required directories exist
CONFIG_DIR.mkdir(exist_ok=True)
DEFAULT_DATA_DIR.mkdir(exist_ok=True)


# Logging Configuration
LOG_DIR = CONFIG_DIR / "logs"
LOG_LEVEL = os.environ.get("JOBTRACKR_LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
LOG_MAX_SIZE = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT = 5


# Application state enum types
class ApplicationStatus(enum.Enum):
    SAVED = "SAVED"
    APPLIED = "APPLIED"
    PHONE_SCREEN = "PHONE_SCREEN"
    INTERVIEW = "INTERVIEW"
    TECHNICAL_INTERVIEW = "TECHNICAL_INTERVIEW"
    OFFER = "OFFER"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


class InteractionType(enum.Enum):
    NOTE = "NOTE"
    LINKEDIN = "LINKEDIN"
    EMAIL = "EMAIL"
    PHONE_CALL = "PHONE_CALL"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    FOLLOW_UP = "FOLLOW_UP"


class CompanyType(enum.Enum):
    DIRECT_EMPLOYER = "DIRECT_EMPLOYER"  # Company that directly employs people
    RECRUITER = "RECRUITER"  # Recruitment agency
    STAFFING = "STAFFING"  # Staffing/contracting company
    CLIENT = "CLIENT"  # Client company (for contractors)
    OTHER = "OTHER"  # Other type


class ChangeType(enum.Enum):
    STATUS_CHANGE = "STATUS_CHANGE"
    INTERACTION_ADDED = "INTERACTION_ADDED"
    CONTACT_ADDED = "CONTACT_ADDED"
    APPLICATION_UPDATED = "APPLICATION_UPDATED"
    NOTE_ADDED = "NOTE_ADDED"
    DOCUMENT_ADDED = "DOCUMENT_ADDED"


# Relationship types for companies
COMPANY_RELATIONSHIP_TYPES = [
    "recruits_for",
    "parent_company",
    "subsidiary",
    "client",
    "vendor",
    "partner",
    "other",
]
