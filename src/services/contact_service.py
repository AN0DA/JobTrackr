import logging
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from src.config import ChangeType
from src.db.models import Application, Company, Contact
from src.services.base_service import BaseService
from src.services.change_record_service import ChangeRecordService
from src.utils.decorators import db_operation

logger = logging.getLogger(__name__)


class ContactService(BaseService):
    """
    Service for contact-related operations.

    Provides methods to create, update, delete, and retrieve contacts and their associations with companies and applications.
    """

    model_class = Contact
    entity_name = "contact"

    def _create_entity_from_dict(self, data: dict[str, Any], session: Session) -> Contact:
        """
        Create a Contact object from a dictionary.

        Args:
            data: Dictionary of contact attributes.
            session: SQLAlchemy session.
        Returns:
            Contact instance.
        """
        return Contact(
            name=data["name"],
            title=data.get("title"),
            email=data.get("email"),
            phone=data.get("phone"),
            notes=data.get("notes"),
            company_id=data.get("company_id"),
        )

    def _update_entity_from_dict(self, entity: Contact, data: dict[str, Any], session: Session) -> None:
        """
        Update a Contact object from a dictionary.

        Args:
            entity: Contact instance to update.
            data: Dictionary of updated attributes.
            session: SQLAlchemy session.
        """
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
        """
        Convert a Contact object to a dictionary.

        Args:
            contact: Contact instance.
            include_details: Whether to include all details.
        Returns:
            Dictionary representation of the contact.
        """
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
        """
        Get contacts with optional filtering by company.

        Args:
            session: SQLAlchemy session.
            company_id: Optional company ID to filter contacts.
            **kwargs: Additional query options (offset, limit).
        Returns:
            List of contact dictionaries.
        """
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
        """
        Search for contacts by name, email, or title.

        Args:
            search_term: The search string.
            session: SQLAlchemy session.
        Returns:
            List of contact dictionaries matching the search.
        """
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
        """
        Associate a contact with an application.

        Args:
            application_id: ID of the application.
            contact_id: ID of the contact.
            session: SQLAlchemy session.
        Returns:
            True if association was successful, False otherwise.
        """
        try:
            application = session.query(Application).filter(Application.id == application_id).first()
            contact = session.query(Contact).filter(Contact.id == contact_id).first()

            if not application or not contact:
                return False

            # Check if the association already exists
            if contact in application.contacts:
                logger.debug(
                    f"Association already exists between contact {contact_id} and application {application_id}"
                )
                return True

            # Create the association
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
        """
        Get contacts associated with an application.

        Args:
            application_id: ID of the application.
            session: SQLAlchemy session.
        Returns:
            List of contact dictionaries associated with the application.
        """
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
        """
        Remove a contact from an application.

        Args:
            application_id: ID of the application.
            contact_id: ID of the contact.
            session: SQLAlchemy session.
        Returns:
            True if removal was successful, False otherwise.
        """
        try:
            application = session.query(Application).filter(Application.id == application_id).first()
            contact = session.query(Contact).filter(Contact.id == contact_id).first()

            if not application or not contact or contact not in application.contacts:
                logger.debug(f"No association found between contact {contact_id} and application {application_id}")
                return False

            # Remove the association
            application.contacts.remove(contact)
            session.commit()

            # Record the change
            change_record_service = ChangeRecordService()
            change_record_service.create(
                {
                    "application_id": application_id,
                    "change_type": ChangeType.CONTACT_REMOVED.value,
                    "old_value": contact.name,
                    "notes": f"Removed contact: {contact.name}",
                }
            )

            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error removing contact from application: {e}")
            raise

    @db_operation
    def get_associated_applications(self, contact_id: int, session: Session) -> list[dict[str, Any]]:
        """
        Get all applications associated with a contact.

        Args:
            contact_id: ID of the contact.
            session: SQLAlchemy session.
        Returns:
            List of application dictionaries associated with the contact.
        """
        try:
            logger.debug(f"Getting applications for contact {contact_id}")

            # Get contact with applications
            contact = (
                session.query(Contact)
                .options(joinedload(Contact.applications).joinedload(Application.company))
                .filter(Contact.id == contact_id)
                .first()
            )

            if not contact or not contact.applications:
                logger.debug(f"No applications found for contact {contact_id}")
                return []

            # Convert to dictionaries
            result = []
            for app in contact.applications:
                app_dict = app.to_dict()

                # Add company info if available
                if app.company:
                    app_dict["company"] = app.company.to_dict()

                result.append(app_dict)

            logger.debug(f"Found {len(result)} applications for contact {contact_id}")
            return result

        except Exception as e:
            logger.error(f"Error getting associated applications for contact {contact_id}: {e}", exc_info=True)
            raise

    @db_operation
    def associate_with_application(self, contact_id: int, application_id: int, session: Session) -> bool:
        """
        Associate a contact with an application.

        Args:
            contact_id: ID of the contact.
            application_id: ID of the application.
            session: SQLAlchemy session.
        Returns:
            True if association was successful, False otherwise.
        """
        try:
            logger.debug(f"Associating contact {contact_id} with application {application_id}")

            # Check if the contact exists
            contact = session.query(Contact).filter(Contact.id == contact_id).first()
            if not contact:
                logger.error(f"Contact {contact_id} not found")
                return False

            # Check if the application exists
            application = session.query(Application).filter(Application.id == application_id).first()
            if not application:
                logger.error(f"Application {application_id} not found")
                return False

            # Check if the association already exists
            if contact in application.contacts:
                logger.debug(
                    f"Association already exists between contact {contact_id} and application {application_id}"
                )
                return True

            # Create the association
            application.contacts.append(contact)
            session.commit()

            logger.debug(f"Created association between contact {contact_id} and application {application_id}")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error associating contact with application: {e}", exc_info=True)
            raise

    @db_operation
    def disassociate_from_application(self, contact_id: int, application_id: int, session: Session) -> bool:
        """
        Remove the association between a contact and an application.

        Args:
            contact_id: ID of the contact.
            application_id: ID of the application.
            session: SQLAlchemy session.
        Returns:
            True if disassociation was successful, False otherwise.
        """
        try:
            logger.debug(f"Removing association between contact {contact_id} and application {application_id}")

            # Get the application and contact
            application = session.query(Application).filter(Application.id == application_id).first()
            contact = session.query(Contact).filter(Contact.id == contact_id).first()

            if not application or not contact or contact not in application.contacts:
                logger.debug(f"No association found between contact {contact_id} and application {application_id}")
                return False

            # Delete the association
            application.contacts.remove(contact)
            session.commit()

            logger.debug(f"Removed association between contact {contact_id} and application {application_id}")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error removing association between contact and application: {e}", exc_info=True)
            raise
