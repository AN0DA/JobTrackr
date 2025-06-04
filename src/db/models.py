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
    """
    ORM model for a company.

    Represents a company entity, including its name, industry, website, type, size,
    notes, and timestamps. Companies can have applications, contacts, and relationships
    with other companies.
    """

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    industry = Column(String(255))
    website = Column(String(255))
    type = Column(String(50))
    size = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applications = relationship("Application", back_populates="company")
    contacts = relationship("Contact", back_populates="company")
    outgoing_relationships = relationship(
        "CompanyRelationship", foreign_keys="CompanyRelationship.source_company_id", back_populates="source_company"
    )
    incoming_relationships = relationship(
        "CompanyRelationship", foreign_keys="CompanyRelationship.related_company_id", back_populates="related_company"
    )

    def to_dict(self):
        """
        Convert the company instance to a dictionary.

        Returns:
            dict: Dictionary representation of the company.
        """
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
    """
    ORM model for a job application.

    Represents a job application, including job title, position, location, salary range,
    status, application date, link, description, notes, and timestamps. Linked to a company,
    contacts, interactions, and change records.
    """

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

    company_id = Column(Integer, ForeignKey("companies.id"))
    company = relationship("Company", back_populates="applications")
    interactions = relationship("Interaction", back_populates="application", cascade="all, delete-orphan")
    change_records = relationship("ChangeRecord", back_populates="application", cascade="all, delete-orphan")
    contacts = relationship("Contact", secondary=contact_applications, back_populates="applications")

    def to_dict(self):
        """
        Convert the application instance to a dictionary.

        Returns:
            dict: Dictionary representation of the application.
        """
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
    """
    ORM model for a contact person.

    Represents a contact associated with a company and applications, including name, title,
    email, phone, notes, and timestamps.
    """

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

    company = relationship("Company", back_populates="contacts")
    applications = relationship("Application", secondary=contact_applications, back_populates="contacts")
    interactions = relationship("Interaction", back_populates="contact")

    def to_dict(self):
        """
        Convert the contact instance to a dictionary.

        Returns:
            dict: Dictionary representation of the contact.
        """
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
    """
    ORM model for tracking communication with contacts.

    Represents an interaction (such as email, call, or meeting) between a contact and an
    application, including type, date, subject, notes, and timestamps.
    """

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

    contact = relationship("Contact", back_populates="interactions")
    application = relationship("Application")

    def to_dict(self):
        """
        Convert the interaction instance to a dictionary.

        Returns:
            dict: Dictionary representation of the interaction.
        """
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
    """
    ORM model for tracking changes to applications.

    Records changes to an application, such as status changes or contact additions, including
    old and new values, notes, and timestamp.
    """

    __tablename__ = "change_records"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    change_type = Column(String(50), nullable=False)  # e.g., STATUS_CHANGE, CONTACT_ADDED, etc.
    old_value = Column(String(255))
    new_value = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="change_records")

    def to_dict(self):
        """
        Convert the change record to a dictionary.

        Returns:
            dict: Dictionary representation of the change record.
        """
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
    """
    ORM model for relationships between companies.

    Represents a relationship between two companies, including the type of relationship,
    notes, and timestamps.
    """

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

    source_company = relationship("Company", foreign_keys=[source_company_id], back_populates="outgoing_relationships")
    related_company = relationship(
        "Company", foreign_keys=[related_company_id], back_populates="incoming_relationships"
    )

    def to_dict(self):
        """
        Convert the company relationship instance to a dictionary.

        Returns:
            dict: Dictionary representation of the company relationship.
        """
        return {
            "id": self.id,
            "source_company_id": self.source_company_id,
            "related_company_id": self.related_company_id,
            "relationship_type": self.relationship_type,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
