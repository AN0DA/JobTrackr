import logging
from typing import Any

from sqlalchemy import or_

from src.db.database import get_session
from src.db.models import Application, ChangeType, Company, Contact
from src.services.change_record_service import ChangeRecordService

logger = logging.getLogger(__name__)


class ContactService:
    """Service for contact-related operations."""

    def get_contact(self, _id: int) -> dict[str, Any] | None:
        """Get a specific contact by ID."""
        session = get_session()
        try:
            contact = session.query(Contact).filter(Contact.id == _id).first()
            if not contact:
                return None

            return self._contact_to_dict(contact)
        except Exception as e:
            logger.error(f"Error fetching contact {_id}: {e}")
            raise
        finally:
            session.close()

    def get_contacts(self, company_id: int | None = None, offset: int = 0, limit: int = 50) -> list[dict[str, Any]]:
        """Get contacts with optional filtering by company."""
        session = get_session()
        try:
            query = session.query(Contact)

            if company_id:
                query = query.filter(Contact.company_id == company_id)

            contacts = query.offset(offset).limit(limit).all()

            return [self._contact_to_dict(contact) for contact in contacts]
        except Exception as e:
            logger.error(f"Error fetching contacts: {e}")
            raise
        finally:
            session.close()

    def create_contact(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new contact."""
        session = get_session()
        try:
            contact = Contact(
                name=data["name"],
                title=data.get("title"),
                email=data.get("email"),
                phone=data.get("phone"),
                notes=data.get("notes"),
                company_id=data.get("company_id"),
            )

            session.add(contact)
            session.commit()
            session.refresh(contact)

            return self._contact_to_dict(contact)
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating contact: {e}")
            raise
        finally:
            session.close()

    def update_contact(self, _id: int, data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing contact."""
        session = get_session()
        try:
            contact = session.query(Contact).filter(Contact.id == _id).first()
            if not contact:
                raise ValueError(f"Contact with ID {_id} not found")

            # Update fields
            if "name" in data:
                contact.name = data["name"]
            if "title" in data:
                contact.title = data["title"]
            if "email" in data:
                contact.email = data["email"]
            if "phone" in data:
                contact.phone = data["phone"]
            if "notes" in data:
                contact.notes = data["notes"]
            if "company_id" in data:
                contact.company_id = data["company_id"]

            session.commit()
            session.refresh(contact)

            return self._contact_to_dict(contact)
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating contact {_id}: {e}")
            raise
        finally:
            session.close()

    def delete_contact(self, _id: int) -> bool:
        """Delete a contact."""
        session = get_session()
        try:
            contact = session.query(Contact).filter(Contact.id == _id).first()
            if not contact:
                return False

            session.delete(contact)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting contact {_id}: {e}")
            raise
        finally:
            session.close()

    def search_contacts(self, search_term: str) -> list[dict[str, Any]]:
        """Search for contacts by name, email, or title."""
        session = get_session()
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
            return [self._contact_to_dict(contact) for contact in contacts]
        except Exception as e:
            logger.error(f"Error searching contacts: {e}")
            raise
        finally:
            session.close()

    def add_contact_to_application(self, application_id: int, contact_id: int) -> bool:
        """Associate a contact with an application."""
        session = get_session()
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
                change_record_service.create_change_record(
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
        finally:
            session.close()

    def _contact_to_dict(self, contact: Contact) -> dict[str, Any]:
        """Convert a Contact object to a dictionary."""
        result = {
            "id": contact.id,
            "name": contact.name,
            "title": contact.title,
            "email": contact.email,
            "phone": contact.phone,
            "notes": contact.notes,
        }

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
