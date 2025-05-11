from datetime import datetime
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from src.db.models import Interaction
from src.services.base_service import BaseService
from src.utils.decorators import db_operation
from src.utils.logging import get_logger

logger = get_logger(__name__)


class InteractionService(BaseService):
    """Service for interaction-related operations."""

    model_class = Interaction
    entity_name = "interaction"

    def _create_entity_from_dict(self, data: dict[str, Any], session: Session) -> Interaction:
        """Create an Interaction object from a dictionary."""
        # Parse the date string to a datetime object
        date = data.get("date")
        if isinstance(date, str):
            try:
                date = datetime.fromisoformat(date.replace("Z", "+00:00"))
            except ValueError:
                # Try another format if ISO format fails
                date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")

        return Interaction(
            contact_id=data["contact_id"],
            application_id=data.get("application_id"),
            interaction_type=data["interaction_type"],
            date=date or datetime.utcnow(),
            subject=data.get("subject", ""),
            notes=data.get("notes", ""),
        )

    def _update_entity_from_dict(self, entity: Interaction, data: dict[str, Any], session: Session) -> None:
        """Update an Interaction object from a dictionary."""
        if "interaction_type" in data:
            entity.interaction_type = data["interaction_type"]

        if "date" in data:
            date = data["date"]
            if isinstance(date, str):
                try:
                    date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                except ValueError:
                    # Try another format if ISO format fails
                    date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
            entity.date = date

        if "subject" in data:
            entity.subject = data["subject"]

        if "notes" in data:
            entity.notes = data["notes"]

        if "application_id" in data:
            entity.application_id = data["application_id"]

    def _entity_to_dict(self, interaction: Interaction, include_details: bool = True) -> dict[str, Any]:
        """Convert an Interaction object to a dictionary."""
        result = {
            "id": interaction.id,
            "contact_id": interaction.contact_id,
            "interaction_type": interaction.interaction_type,
            "date": interaction.date.isoformat() if interaction.date else None,
        }

        if include_details:
            result.update(
                {
                    "application_id": interaction.application_id,
                    "subject": interaction.subject,
                    "notes": interaction.notes,
                    "created_at": interaction.created_at.isoformat() if interaction.created_at else None,
                    "updated_at": interaction.updated_at.isoformat() if interaction.updated_at else None,
                }
            )

            # Include contact information
            if interaction.contact:
                result["contact"] = {
                    "id": interaction.contact.id,
                    "name": interaction.contact.name,
                }

            # Include application information if available
            if interaction.application:
                result["application"] = {
                    "id": interaction.application.id,
                    "job_title": interaction.application.job_title,
                }

        return result

    @db_operation
    def get_interactions_by_contact(
        self, contact_id: int, session: Session, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get interactions for a specific contact."""
        try:
            logger.debug(f"Getting interactions for contact {contact_id}")

            # Query interactions for the contact
            query = (
                session.query(Interaction)
                .options(joinedload(Interaction.contact))
                .options(joinedload(Interaction.application))
                .filter(Interaction.contact_id == contact_id)
                .order_by(desc(Interaction.date))
            )

            # Apply pagination
            interactions = query.offset(offset).limit(limit).all()

            # Convert to dictionaries
            result = [self._entity_to_dict(interaction) for interaction in interactions]

            logger.debug(f"Found {len(result)} interactions for contact {contact_id}")
            return result

        except Exception as e:
            logger.error(f"Error getting interactions for contact {contact_id}: {e}", exc_info=True)
            raise

    @db_operation
    def get_interactions_by_application(
        self, application_id: int, session: Session, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get interactions for a specific application."""
        try:
            logger.debug(f"Getting interactions for application {application_id}")

            # Query interactions for the application
            query = (
                session.query(Interaction)
                .options(joinedload(Interaction.contact))
                .filter(Interaction.application_id == application_id)
                .order_by(desc(Interaction.date))
            )

            # Apply pagination
            interactions = query.offset(offset).limit(limit).all()

            # Convert to dictionaries
            result = [self._entity_to_dict(interaction) for interaction in interactions]

            logger.debug(f"Found {len(result)} interactions for application {application_id}")
            return result

        except Exception as e:
            logger.error(f"Error getting interactions for application {application_id}: {e}", exc_info=True)
            raise

    @db_operation
    def delete_interaction(self, interaction_id: int, session: Session) -> bool:
        """Delete an interaction."""
        try:
            logger.debug(f"Deleting interaction {interaction_id}")

            # Find the interaction
            interaction = session.query(Interaction).filter(Interaction.id == interaction_id).first()

            if not interaction:
                logger.debug(f"Interaction {interaction_id} not found")
                return False

            # Delete the interaction
            session.delete(interaction)
            session.commit()

            logger.debug(f"Deleted interaction {interaction_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting interaction {interaction_id}: {e}", exc_info=True)
            session.rollback()
            raise

    @db_operation
    def get_interactions(self, application_id: int, session: Session) -> list[dict]:
        """Get all interactions for an application."""
        try:
            interactions = (
                session.query(Interaction)
                .options(joinedload(Interaction.contact))
                .filter(Interaction.application_id == application_id)
                .order_by(Interaction.date.desc())
                .all()
            )
            return [self._entity_to_dict(interaction) for interaction in interactions]
        except Exception as e:
            logger.error(f"Error getting interactions: {e}", exc_info=True)
            return []
