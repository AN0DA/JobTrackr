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
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# Association table for contacts and applications
contact_applications = Table(
    "contact_applications",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("contact_id", ForeignKey("contacts.id", name="fk_contact_applications_contact_id_contacts"), nullable=False),
    Column(
        "application_id",
        ForeignKey("applications.id", name="fk_contact_applications_application_id_applications"),
        nullable=False,
    ),
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
    outgoing_relationships = relationship(
        "CompanyRelationship", foreign_keys="CompanyRelationship.source_company_id", back_populates="source_company"
    )
    incoming_relationships = relationship(
        "CompanyRelationship", foreign_keys="CompanyRelationship.related_company_id", back_populates="related_company"
    )

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
    position = Column(String(255), nullable=False)
    location = Column(String(255))
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    status = Column(String(50), nullable=False)
    applied_date = Column(DateTime, nullable=False)
    link = Column(String(255))
    description = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Foreign keys
    company_id = Column(Integer, ForeignKey("companies.id"))
    company = relationship("Company", back_populates="applications")
    interactions = relationship("Interaction", back_populates="application", cascade="all, delete-orphan")
    change_records = relationship("ChangeRecord", back_populates="application", cascade="all, delete-orphan")
    contacts = relationship("Contact", secondary=contact_applications, back_populates="applications")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "job_title": self.job_title,
            "position": self.position,
            "location": self.location,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "status": self.status,
            "applied_date": self.applied_date.isoformat() if self.applied_date else None,
            "link": self.link,
            "description": self.description,
            "notes": self.notes,
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
    company_id = Column(Integer, ForeignKey("companies.id", name="fk_contacts_company_id_companies"))
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
    contact_id = Column(Integer, ForeignKey("contacts.id", name="fk_interactions_contact_id_contacts"), nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id", name="fk_interactions_application_id_applications"))
    interaction_type = Column(String(50))  # EMAIL, CALL, MEETING, etc
    date = Column(DateTime, nullable=False)
    subject = Column(String(255))  # Subject line for the interaction
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
            "subject": self.subject,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ChangeRecord(Base):
    """Model for tracking changes to applications."""

    __tablename__ = "change_records"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    change_type = Column(String(50), nullable=False)  # e.g., STATUS_CHANGE, CONTACT_ADDED, etc.
    old_value = Column(String(255))
    new_value = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    application = relationship("Application", back_populates="change_records")

    def to_dict(self):
        """Convert the change record to a dictionary."""
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
    source_company_id = Column(
        Integer, ForeignKey("companies.id", name="fk_company_relationships_source_company_id_companies"), nullable=False
    )
    related_company_id = Column(
        Integer,
        ForeignKey("companies.id", name="fk_company_relationships_related_company_id_companies"),
        nullable=False,
    )
    relationship_type = Column(String, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship definitions
    source_company = relationship("Company", foreign_keys=[source_company_id], back_populates="outgoing_relationships")
    related_company = relationship(
        "Company", foreign_keys=[related_company_id], back_populates="incoming_relationships"
    )

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "source_company_id": self.source_company_id,
            "related_company_id": self.related_company_id,
            "relationship_type": self.relationship_type,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
