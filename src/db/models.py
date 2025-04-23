import json

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from src.db.database import Base


# Enums for application statuses and types
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
    EMAIL = "EMAIL"
    PHONE_CALL = "PHONE_CALL"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    FOLLOW_UP = "FOLLOW_UP"


class DocumentType(enum.Enum):
    RESUME = "RESUME"
    COVER_LETTER = "COVER_LETTER"
    PORTFOLIO = "PORTFOLIO"
    OFFER_LETTER = "OFFER_LETTER"
    OTHER = "OTHER"


# Association tables for many-to-many relationships
application_contact = Table(
    'application_contact',
    Base.metadata,
    Column('application_id', ForeignKey('applications.id'), primary_key=True),
    Column('contact_id', ForeignKey('contacts.id'), primary_key=True)
)

application_document = Table(
    'application_document',
    Base.metadata,
    Column('application_id', ForeignKey('applications.id'), primary_key=True),
    Column('document_id', ForeignKey('documents.id'), primary_key=True)
)

interaction_contact = Table(
    'interaction_contact',
    Base.metadata,
    Column('interaction_id', ForeignKey('interactions.id'), primary_key=True),
    Column('contact_id', ForeignKey('contacts.id'), primary_key=True)
)

interaction_document = Table(
    'interaction_document',
    Base.metadata,
    Column('interaction_id', ForeignKey('interactions.id'), primary_key=True),
    Column('document_id', ForeignKey('documents.id'), primary_key=True)
)


# Data models
class Company(Base):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    website = Column(String)
    industry = Column(String, index=True)
    size = Column(String)
    logo = Column(String)
    notes = Column(Text)

    # Relationships
    applications = relationship("Application", back_populates="company")
    contacts = relationship("Contact", back_populates="company")

    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}')>"


class Application(Base):
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True)
    job_title = Column(String, nullable=False, index=True)
    position = Column(String, nullable=False, index=True)
    location = Column(String)
    salary = Column(String)
    status = Column(String, nullable=False, index=True)
    applied_date = Column(DateTime, nullable=False, index=True)
    link = Column(String)
    description = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    _tags = Column(String, name='tags')  # Store tags as JSON string

    @property
    def tags(self):
        """Get tags as a list."""
        if self._tags:
            return json.loads(self._tags)
        return []

    @tags.setter
    def tags(self, value):
        """Set tags from a list."""
        if value:
            self._tags = json.dumps(value)
        else:
            self._tags = None

    # Foreign keys
    company_id = Column(Integer, ForeignKey('companies.id'))

    # Relationships
    company = relationship("Company", back_populates="applications")
    contacts = relationship("Contact", secondary=application_contact, back_populates="applications")
    interactions = relationship("Interaction", back_populates="application", cascade="all, delete-orphan")
    documents = relationship("Document", secondary=application_document, back_populates="applications")
    reminders = relationship("Reminder", back_populates="application", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Application(id={self.id}, job_title='{self.job_title}', company_id={self.company_id})>"


class Contact(Base):
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    title = Column(String)
    email = Column(String, index=True)
    phone = Column(String)
    notes = Column(Text)

    # Foreign keys
    company_id = Column(Integer, ForeignKey('companies.id'))

    # Relationships
    company = relationship("Company", back_populates="contacts")
    applications = relationship("Application", secondary=application_contact, back_populates="contacts")
    interactions = relationship("Interaction", secondary=interaction_contact, back_populates="contacts")

    def __repr__(self):
        return f"<Contact(id={self.id}, name='{self.name}')>"


class Interaction(Base):
    __tablename__ = 'interactions'

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    notes = Column(Text)

    # Foreign keys
    application_id = Column(Integer, ForeignKey('applications.id'))

    # Relationships
    application = relationship("Application", back_populates="interactions")
    contacts = relationship("Contact", secondary=interaction_contact, back_populates="interactions")
    documents = relationship("Document", secondary=interaction_document, back_populates="interactions")

    def __repr__(self):
        return f"<Interaction(id={self.id}, type='{self.type}')>"


class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False, index=True)
    url = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    applications = relationship("Application", secondary=application_document, back_populates="documents")
    interactions = relationship("Interaction", secondary=interaction_document, back_populates="documents")

    def __repr__(self):
        return f"<Document(id={self.id}, name='{self.name}', type='{self.type}')>"


class Reminder(Base):
    __tablename__ = 'reminders'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    date = Column(DateTime, nullable=False, index=True)
    completed = Column(Boolean, default=False, index=True)

    # Foreign keys
    application_id = Column(Integer, ForeignKey('applications.id'))

    # Relationships
    application = relationship("Application", back_populates="reminders")

    def __repr__(self):
        return f"<Reminder(id={self.id}, title='{self.title}')>"
