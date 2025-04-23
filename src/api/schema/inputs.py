"""GraphQL input types."""

import strawberry
from typing import List, Optional
from datetime import datetime

from src.api.schema.types import ApplicationStatus, InteractionType, DocumentType


@strawberry.input
class ApplicationInput:
    job_title: str
    company_id: strawberry.ID
    position: str
    location: Optional[str] = None
    salary: Optional[str] = None
    status: ApplicationStatus
    applied_date: datetime
    link: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


@strawberry.input
class CompanyInput:
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    logo: Optional[str] = None
    notes: Optional[str] = None


@strawberry.input
class ContactInput:
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company_id: Optional[strawberry.ID] = None
    application_id: Optional[strawberry.ID] = None
    notes: Optional[str] = None


@strawberry.input
class InteractionInput:
    application_id: strawberry.ID
    type: InteractionType
    date: datetime
    notes: Optional[str] = None
    contact_ids: Optional[List[strawberry.ID]] = None
    document_ids: Optional[List[strawberry.ID]] = None


@strawberry.input
class DocumentInput:
    name: str
    type: DocumentType
    url: Optional[str] = None
    content: Optional[str] = None
    application_ids: Optional[List[strawberry.ID]] = None


@strawberry.input
class ReminderInput:
    title: str
    description: Optional[str] = None
    date: datetime
    completed: bool = False
    application_id: Optional[strawberry.ID] = None