from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship

from src.db.database import Base

# Association table for contacts and applications
contact_applications = Table(
    "contact_applications",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("contact_id", ForeignKey("contacts.id"), nullable=False),
    Column("application_id", ForeignKey("applications.id"), nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow),
)


class Company(Base):
    """Company model."""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    industry = Column(String(255))
    website = Column(String(255))
    type = Column(String(50))  # DIRECT_EMPLOYER, STAFFING_AGENCY, etc
    size = Column(String(50))  # S, M, L, XL etc
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    applications = relationship("Application", back_populates="company")
    contacts = relationship("Contact", back_populates="company")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "industry": self.industry,
            "website": self.website,
            "type": self.type,
            "size": self.size,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Application(Base):
    """Application model."""

    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    job_title = Column(String(255), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"))
    position = Column(String(255))
    description = Column(Text)
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    location = Column(String(255))
    remote = Column(String(50))  # REMOTE, HYBRID, ONSITE
    application_method = Column(String(50))  # WEBSITE, EMAIL, REFERRAL, etc
    job_url = Column(String(255))
    status = Column(String(50))  # APPLIED, INTERVIEWING, REJECTED, OFFER, etc
    status_details = Column(Text)
    applied_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="applications")
    change_records = relationship("ChangeRecord", back_populates="application")
    contacts = relationship("Contact", secondary=contact_applications, back_populates="applications")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "job_title": self.job_title,
            "company_id": self.company_id,
            "position": self.position,
            "description": self.description,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "location": self.location,
            "remote": self.remote,
            "application_method": self.application_method,
            "job_url": self.job_url,
            "status": self.status,
            "status_details": self.status_details,
            "applied_date": self.applied_date.isoformat() if self.applied_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Contact(Base):
    """Contact model."""

    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    title = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    company_id = Column(Integer, ForeignKey("companies.id"))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="contacts")
    applications = relationship("Application", secondary=contact_applications, back_populates="contacts")
    interactions = relationship("Interaction", back_populates="contact")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "email": self.email,
            "phone": self.phone,
            "company_id": self.company_id,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Interaction(Base):
    """Interaction model for tracking communication with contacts."""

    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id"))
    interaction_type = Column(String(50))  # EMAIL, CALL, MEETING, etc
    date = Column(DateTime, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contact = relationship("Contact", back_populates="interactions")
    application = relationship("Application")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "contact_id": self.contact_id,
            "application_id": self.application_id,
            "interaction_type": self.interaction_type,
            "date": self.date.isoformat() if self.date else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ChangeRecord(Base):
    """Change record for tracking application status changes."""

    __tablename__ = "change_records"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    change_type = Column(String(50))  # STATUS_CHANGE, NOTE_ADDED, CONTACT_ADDED, etc
    old_value = Column(String(255))
    new_value = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    application = relationship("Application", back_populates="change_records")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "application_id": self.application_id,
            "change_type": self.change_type,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CompanyRelationship(Base):
    """Company relationship model."""

    __tablename__ = "company_relationships"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    related_company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    relationship_type = Column(String(50))  # PARENT, SUBSIDIARY, PARTNER, etc
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "related_company_id": self.related_company_id,
            "relationship_type": self.relationship_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
