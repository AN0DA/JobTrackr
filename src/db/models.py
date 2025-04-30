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

from src.config import CompanyType
from src.db.database import Base

# Association tables for many-to-many relationships
application_contact = Table(
    "application_contact",
    Base.metadata,
    Column("application_id", ForeignKey("applications.id"), primary_key=True),
    Column("contact_id", ForeignKey("contacts.id"), primary_key=True),
)

interaction_contact = Table(
    "interaction_contact",
    Base.metadata,
    Column("interaction_id", ForeignKey("interactions.id"), primary_key=True),
    Column("contact_id", ForeignKey("contacts.id"), primary_key=True),
)


class CompanyRelationship(Base):
    __tablename__ = "company_relationships"

    id = Column(Integer, primary_key=True)
    source_company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    target_company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    relationship_type = Column(String, nullable=False)  # e.g., "recruits_for", "parent_company", etc.
    notes = Column(Text)

    # Relationships
    source_company = relationship(
        "Company",
        foreign_keys=[source_company_id],
        back_populates="outgoing_relationships",
    )
    target_company = relationship(
        "Company",
        foreign_keys=[target_company_id],
        back_populates="incoming_relationships",
    )

    def __repr__(self) -> str:
        return f"<CompanyRelationship(source={self.source_company_id}, target={self.target_company_id}, type='{self.relationship_type}')>"


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    website = Column(String)
    industry = Column(String, index=True)
    size = Column(String)
    type = Column(String, default=CompanyType.DIRECT_EMPLOYER.value)  # Default to direct employer
    notes = Column(Text)

    # Relationships
    applications = relationship("Application", back_populates="company")
    contacts = relationship("Contact", back_populates="company")
    outgoing_relationships = relationship(
        "CompanyRelationship",
        foreign_keys=[CompanyRelationship.source_company_id],
        back_populates="source_company",
        cascade="all, delete-orphan",
    )
    incoming_relationships = relationship(
        "CompanyRelationship",
        foreign_keys=[CompanyRelationship.target_company_id],
        back_populates="target_company",
        cascade="all, delete-orphan",
    )


class Application(Base):
    __tablename__ = "applications"

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

    # Foreign keys
    company_id = Column(Integer, ForeignKey("companies.id"))

    # Relationships
    company = relationship("Company", back_populates="applications")
    contacts = relationship("Contact", secondary=application_contact, back_populates="applications")
    interactions = relationship("Interaction", back_populates="application", cascade="all, delete-orphan")
    change_records = relationship("ChangeRecord", back_populates="application", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Application(id={self.id}, job_title='{self.job_title}', company_id={self.company_id})>"


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    title = Column(String)
    email = Column(String, index=True)
    phone = Column(String)
    notes = Column(Text)

    # Foreign keys
    company_id = Column(Integer, ForeignKey("companies.id"))

    # Relationships
    company = relationship("Company", back_populates="contacts")
    applications = relationship("Application", secondary=application_contact, back_populates="contacts")
    interactions = relationship("Interaction", secondary=interaction_contact, back_populates="contacts")

    def __repr__(self) -> str:
        return f"<Contact(id={self.id}, name='{self.name}')>"


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    notes = Column(Text)

    # Foreign keys
    application_id = Column(Integer, ForeignKey("applications.id"))

    # Relationships
    application = relationship("Application", back_populates="interactions")
    contacts = relationship("Contact", secondary=interaction_contact, back_populates="interactions")

    def __repr__(self) -> str:
        return f"<Interaction(id={self.id}, type='{self.type}')>"


class ChangeRecord(Base):
    __tablename__ = "change_records"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    change_type = Column(String, nullable=False, index=True)
    old_value = Column(String)
    new_value = Column(String)
    notes = Column(Text)

    # Relationships
    application = relationship("Application", back_populates="change_records")

    def __repr__(self) -> str:
        return f"<ChangeRecord(id={self.id}, app_id={self.application_id}, type='{self.change_type}')>"
