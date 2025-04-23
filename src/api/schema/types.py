"""GraphQL type definitions."""

from enum import Enum
import strawberry
from typing import List, Optional
from datetime import datetime


# Enums
@strawberry.enum
class ApplicationStatus(str, Enum):
    SAVED = "SAVED"
    APPLIED = "APPLIED"
    PHONE_SCREEN = "PHONE_SCREEN"
    INTERVIEW = "INTERVIEW"
    TECHNICAL_INTERVIEW = "TECHNICAL_INTERVIEW"
    OFFER = "OFFER"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


@strawberry.enum
class InteractionType(str, Enum):
    NOTE = "NOTE"
    EMAIL = "EMAIL"
    PHONE_CALL = "PHONE_CALL"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    FOLLOW_UP = "FOLLOW_UP"


@strawberry.enum
class DocumentType(str, Enum):
    RESUME = "RESUME"
    COVER_LETTER = "COVER_LETTER"
    PORTFOLIO = "PORTFOLIO"
    OFFER_LETTER = "OFFER_LETTER"
    OTHER = "OTHER"


# Output Types
@strawberry.type
class Company:
    id: strawberry.ID
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    logo: Optional[str] = None
    notes: Optional[str] = None


@strawberry.type
class Contact:
    id: strawberry.ID
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[Company] = None
    notes: Optional[str] = None


@strawberry.type
class Document:
    id: strawberry.ID
    name: str
    type: DocumentType
    url: Optional[str] = None
    content: Optional[str] = None
    created_at: datetime


@strawberry.type
class Interaction:
    id: strawberry.ID
    application_id: strawberry.ID
    type: InteractionType
    date: datetime
    notes: Optional[str] = None


@strawberry.type
class Application:
    id: strawberry.ID
    job_title: str
    company: Optional[Company] = None
    position: str
    location: Optional[str] = None
    salary: Optional[str] = None
    status: ApplicationStatus
    applied_date: datetime
    link: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


@strawberry.type
class Reminder:
    id: strawberry.ID
    title: str
    description: Optional[str] = None
    date: datetime
    completed: bool
    application_id: Optional[strawberry.ID] = None


@strawberry.type
class StatusCount:
    status: ApplicationStatus
    count: int


@strawberry.type
class DashboardStats:
    total_applications: int
    applications_by_status: List[StatusCount]
    recent_applications: Optional[List[Application]] = None
    upcoming_reminders: Optional[List[Reminder]] = None