import logging
from datetime import datetime
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.config import ChangeType
from src.db.models import Application, Interaction
from src.services.base_service import BaseService
from src.services.change_record_service import ChangeRecordService
from src.utils.decorators import db_operation

logger = logging.getLogger(__name__)


class InteractionService(BaseService):
    """Service for interaction-related operations."""

    model_class = Interaction
    entity_name = "interaction"

    def _create_entity_from_dict(self, data: dict[str, Any], session: Session) -> Interaction:
        """Create an Interaction object from a dictionary."""
        # Ensure application exists
        application = session.query(Application).filter(Application.id == data["application_id"]).first()
        if not application:
            raise ValueError(f"Application with ID {data['application_id']} not found")

        # Handle date format
        date = data["date"]
        if isinstance(date, str):
            date = datetime.fromisoformat(date)

        return Interaction(
            application_id=data["application_id"],
            type=data["type"],
            date=date,
            notes=data.get("notes"),
        )

    def _update_entity_from_dict(self, entity: Interaction, data: dict[str, Any], session: Session) -> None:
        """Update an Interaction object from a dictionary."""
        if "type" in data:
            entity.type = data["type"]
        if "date" in data:
            if isinstance(data["date"], str):
                # Fix the datetime incompatible type assignment
                new_date = datetime.fromisoformat(data["date"])
                entity.date = new_date
            else:
                entity.date = data["date"]
        if "notes" in data:
            entity.notes = data["notes"]

    @db_operation
    def create(self, data: dict[str, Any], session: Session) -> dict[str, Any]:
        """Create a new interaction and record the change."""
        try:
            # Create using the parent method's implementation
            interaction = self._create_entity_from_dict(data, session)

            # Add to session and commit
            session.add(interaction)
            session.commit()
            session.refresh(interaction)

            # Record the change
            change_record_service = ChangeRecordService()
            change_record_service.create(
                {
                    "application_id": data["application_id"],
                    "change_type": ChangeType.INTERACTION_ADDED.value,
                    "new_value": data["type"],
                    "notes": f"Added {data['type']} interaction on {interaction.date.isoformat()}",
                }
            )

            return self._entity_to_dict(interaction)
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating interaction: {e}")
            raise

    def _entity_to_dict(self, interaction: Interaction, include_details: bool = True) -> dict[str, Any]:
        """Convert an Interaction to a dictionary."""
        result = {
            "id": interaction.id,
            "application_id": interaction.application_id,
            "type": interaction.type,
            "date": interaction.date.isoformat(),
            "notes": interaction.notes,
        }

        # Add contact information if available
        if include_details and interaction.contacts:
            result["contacts"] = [
                {"id": contact.id, "name": contact.name, "title": contact.title} for contact in interaction.contacts
            ]

        return result

    @db_operation
    def get_interactions(self, application_id: int, session: Session) -> list[dict[str, Any]]:
        """Get all interactions for an application."""
        try:
            interactions = (
                session.query(Interaction)
                .filter(Interaction.application_id == application_id)
                .order_by(desc(Interaction.date))
                .all()
            )

            return [self._entity_to_dict(interaction) for interaction in interactions]
        except Exception as e:
            logger.error(f"Error fetching interactions: {e}")
            raise

    @db_operation
    def delete(self, _id: int, session: Session) -> bool:
        """Delete an interaction and record the change."""
        try:
            interaction = session.query(Interaction).filter(Interaction.id == _id).first()
            if not interaction:
                return False

            application_id = interaction.application_id
            interaction_type = interaction.type
            interaction_date = interaction.date

            # Delete the interaction
            session.delete(interaction)
            session.commit()

            # Record the change
            change_record_service = ChangeRecordService()
            change_record_service.create(
                {
                    "application_id": application_id,
                    "change_type": ChangeType.INTERACTION_ADDED.value,
                    "old_value": interaction_type,
                    "notes": f"Deleted {interaction_type} interaction from {interaction_date.isoformat()}",
                }
            )

            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting interaction {_id}: {e}")
            raise
