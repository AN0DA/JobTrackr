import logging
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.config import ChangeType
from src.db.models import Application, Company, Contact
from src.services.base_service import BaseService
from src.services.change_record_service import ChangeRecordService
from src.utils.decorators import db_operation

logger = logging.getLogger(__name__)


class ContactService(BaseService):
    """Service for contact-related operations."""

    model_class = Contact
    entity_name = "contact"

    def _create_entity_from_dict(self, data: dict[str, Any], session: Session) -> Contact:
        """Create a Contact object from a dictionary."""
        return Contact(
            name=data["name"],
            title=data.get("title"),
            email=data.get("email"),
            phone=data.get("phone"),
            notes=data.get("notes"),
            company_id=data.get("company_id"),
        )

    def _update_entity_from_dict(self, entity: Contact, data: dict[str, Any], session: Session) -> None:
        """Update a Contact object from a dictionary."""
        if "name" in data:
            entity.name = data["name"]
        if "title" in data:
            entity.title = data["title"]
        if "email" in data:
            entity.email = data["email"]
        if "phone" in data:
            entity.phone = data["phone"]
        if "notes" in data:
            entity.notes = data["notes"]
        if "company_id" in data:
            entity.company_id = data["company_id"]

    def _entity_to_dict(self, contact: Contact, include_details: bool = True) -> dict[str, Any]:
        """Convert a Contact object to a dictionary."""
        result = {
            "id": contact.id,
            "name": contact.name,
        }

        if include_details:
            result.update(
                {
                    "title": contact.title,
                    "email": contact.email,
                    "phone": contact.phone,
                    "notes": contact.notes,
                }
            )

            # Add company information if available
            if contact.company:
                result["company"] = {
                    "id": contact.company.id,
                    "name": contact.company.name,
                }

            # Add associated applications count
            result["application_count"] = len(contact.applications) if contact.applications else 0

            # Add interactions count
            result["interaction_count"] = len(contact.interactions) if contact.interactions else 0

        return result

    @db_operation
    def get_contacts(self, session: Session, company_id: int | None = None, **kwargs: Any) -> list[dict[str, Any]]:
        """Get contacts with optional filtering by company."""
        try:
            query = session.query(Contact)

            if company_id:
                query = query.filter(Contact.company_id == company_id)

            # Apply offset/limit
            offset = kwargs.get("offset", 0)
            limit = kwargs.get("limit", 50)

            contacts = query.offset(offset).limit(limit).all()

            return [self._entity_to_dict(contact) for contact in contacts]
        except Exception as e:
            logger.error(f"Error fetching contacts: {e}")
            raise

    @db_operation
    def search_contacts(self, search_term: str, session: Session) -> list[dict[str, Any]]:
        """Search for contacts by name, email, or title."""
        try:
            search_pattern = f"%{search_term}%"
            query = session.query(Contact).join(Company, isouter=True)

            conditions = [
                Contact.name.ilike(search_pattern),
                Contact.email.ilike(search_pattern),
                Contact.title.ilike(search_pattern),
                Contact.phone.ilike(search_pattern),
                Contact.notes.ilike(search_pattern),
                Company.name.ilike(search_pattern),
            ]

            contacts = query.filter(or_(*conditions)).all()
            return [self._entity_to_dict(contact) for contact in contacts]
        except Exception as e:
            logger.error(f"Error searching contacts: {e}")
            raise

    @db_operation
    def add_contact_to_application(self, application_id: int, contact_id: int, session: Session) -> bool:
        """Associate a contact with an application."""
        try:
            application = session.query(Application).filter(Application.id == application_id).first()
            contact = session.query(Contact).filter(Contact.id == contact_id).first()

            if not application or not contact:
                return False

            if contact not in application.contacts:
                application.contacts.append(contact)
                session.commit()

                # Record the change
                change_record_service = ChangeRecordService()
                change_record_service.create(
                    {
                        "application_id": application_id,
                        "change_type": ChangeType.CONTACT_ADDED.value,
                        "new_value": contact.name,
                        "notes": f"Added contact: {contact.name}",
                    }
                )

            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding contact to application: {e}")
            raise

    @db_operation
    def get_contacts_for_application(self, application_id: int, session: Session) -> list[dict[str, Any]]:
        """Get contacts associated with an application."""
        try:
            application = session.query(Application).filter(Application.id == application_id).first()

            if not application:
                return []

            return [self._entity_to_dict(contact) for contact in application.contacts]
        except Exception as e:
            logger.error(f"Error getting contacts for application {application_id}: {e}")
            raise

    @db_operation
    def remove_contact_from_application(self, application_id: int, contact_id: int, session: Session) -> bool:
        """Remove a contact from an application."""
        try:
            application = session.query(Application).filter(Application.id == application_id).first()
            contact = session.query(Contact).filter(Contact.id == contact_id).first()

            if not application or not contact:
                return False

            if contact in application.contacts:
                application.contacts.remove(contact)
                session.commit()

                # Record the change
                change_record_service = ChangeRecordService()
                change_record_service.create(
                    {
                        "application_id": application_id,
                        "change_type": ChangeType.CONTACT_ADDED.value,
                        "old_value": contact.name,
                        "notes": f"Removed contact: {contact.name}",
                    }
                )

            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error removing contact from application: {e}")
            raise
