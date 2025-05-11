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
DEFAULT_SETTINGS = {"database_path": str(DEFAULT_DB_PATH), "check_updates": True}

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
    CONTACT_REMOVED = "CONTACT_REMOVED"
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

# UI colors
UI_COLORS = {
    "primary": "#2C7BE5",  # Primary brand color
    "secondary": "#6B7280",  # Secondary text/elements
    "success": "#00B860",  # Success states
    "warning": "#F59E0B",  # Warning states
    "danger": "#E11D48",  # Error states
    "info": "#0EA5E9",  # Info states
    "light": "#F3F4F6",  # Light backgrounds
    "dark": "#1F2937",  # Dark text/elements
    "background": "#FFFFFF",  # Main background
    "card": "#F9FAFB",  # Card background
}

# Status colors for application states
STATUS_COLORS = {
    "SAVED": "#6B7280",  # Gray
    "APPLIED": "#0EA5E9",  # Blue
    "PHONE_SCREEN": "#F59E0B",  # Orange
    "INTERVIEW": "#F59E0B",  # Orange
    "TECHNICAL_INTERVIEW": "#F59E0B",  # Orange
    "OFFER": "#00B860",  # Green
    "ACCEPTED": "#059669",  # Darker Green
    "REJECTED": "#E11D48",  # Red
    "WITHDRAWN": "#6B7280",  # Gray
}

# Font sizes
FONT_SIZES = {
    "xs": 8,
    "sm": 10,
    "md": 12,
    "lg": 14,
    "xl": 16,
    "2xl": 20,
    "3xl": 24,
}

# Spacing constants
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "2xl": 32,
}
