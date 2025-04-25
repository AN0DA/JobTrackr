import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import desc

from src.db.models import Interaction, Application, ChangeType
from src.db.database import get_session
from src.services.change_record_service import ChangeRecordService

logger = logging.getLogger(__name__)


class InteractionService:
    """Service for interaction-related operations."""

    def get_interaction(self, id: int) -> Optional[Dict[str, Any]]:
        """Get a specific interaction by ID."""
        session = get_session()
        try:
            interaction = (
                session.query(Interaction).filter(Interaction.id == id).first()
            )
            if not interaction:
                return None

            return self._interaction_to_dict(interaction)
        except Exception as e:
            logger.error(f"Error fetching interaction {id}: {e}")
            raise
        finally:
            session.close()

    def get_interactions(self, application_id: int) -> List[Dict[str, Any]]:
        """Get all interactions for an application."""
        session = get_session()
        try:
            interactions = (
                session.query(Interaction)
                .filter(Interaction.application_id == application_id)
                .order_by(desc(Interaction.date))
                .all()
            )

            return [
                self._interaction_to_dict(interaction) for interaction in interactions
            ]
        except Exception as e:
            logger.error(f"Error fetching interactions: {e}")
            raise
        finally:
            session.close()

    def create_interaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new interaction and record the change."""
        session = get_session()
        try:
            # Ensure application exists
            application = (
                session.query(Application)
                .filter(Application.id == data["application_id"])
                .first()
            )

            if not application:
                raise ValueError(
                    f"Application with ID {data['application_id']} not found"
                )

            # Create interaction
            interaction = Interaction(
                application_id=data["application_id"],
                type=data["type"],
                date=datetime.fromisoformat(data["date"])
                if isinstance(data["date"], str)
                else data["date"],
                notes=data.get("notes"),
            )

            # Add to session and commit
            session.add(interaction)
            session.commit()
            session.refresh(interaction)

            # Record the change
            change_record_service = ChangeRecordService()
            change_record_service.create_change_record(
                {
                    "application_id": data["application_id"],
                    "change_type": ChangeType.INTERACTION_ADDED.value,
                    "new_value": data["type"],
                    "notes": f"Added {data['type']} interaction on {interaction.date.isoformat()}",
                }
            )

            return self._interaction_to_dict(interaction)
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating interaction: {e}")
            raise
        finally:
            session.close()

    def update_interaction(self, id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing interaction."""
        session = get_session()
        try:
            # Get interaction
            interaction = (
                session.query(Interaction).filter(Interaction.id == id).first()
            )
            if not interaction:
                raise ValueError(f"Interaction with ID {id} not found")

            # Update fields
            if "type" in data:
                interaction.type = data["type"]
            if "date" in data:
                interaction.date = (
                    datetime.fromisoformat(data["date"])
                    if isinstance(data["date"], str)
                    else data["date"]
                )
            if "notes" in data:
                interaction.notes = data["notes"]

            # Commit changes
            session.commit()
            session.refresh(interaction)

            return self._interaction_to_dict(interaction)
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating interaction {id}: {e}")
            raise
        finally:
            session.close()

    def delete_interaction(self, id: int) -> bool:
        """Delete an interaction."""
        session = get_session()
        try:
            interaction = (
                session.query(Interaction).filter(Interaction.id == id).first()
            )
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
            change_record_service.create_change_record(
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
            logger.error(f"Error deleting interaction {id}: {e}")
            raise
        finally:
            session.close()

    def _interaction_to_dict(self, interaction: Interaction) -> Dict[str, Any]:
        """Convert an Interaction to a dictionary."""
        result = {
            "id": interaction.id,
            "application_id": interaction.application_id,
            "type": interaction.type,
            "date": interaction.date.isoformat(),
            "notes": interaction.notes,
        }

        # Add contact information if available
        if interaction.contacts:
            result["contacts"] = [
                {"id": contact.id, "name": contact.name, "title": contact.title}
                for contact in interaction.contacts
            ]

        return result
