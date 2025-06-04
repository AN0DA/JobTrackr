import logging
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.db.models import ChangeRecord
from src.services.base_service import BaseService
from src.utils.decorators import db_operation

logger = logging.getLogger(__name__)


class ChangeRecordService(BaseService):
    """
    Service for managing change records.

    Provides methods to create, update, and retrieve change records for applications.
    """

    model_class = ChangeRecord
    entity_name = "change_record"

    def _create_entity_from_dict(self, data: dict[str, Any], session: Session) -> ChangeRecord:
        """
        Create a ChangeRecord from a dictionary.

        Args:
            data: Dictionary of change record attributes.
            session: SQLAlchemy session.
        Returns:
            ChangeRecord instance.
        """
        return ChangeRecord(
            application_id=data["application_id"],
            change_type=data["change_type"],
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
            notes=data.get("notes"),
        )

    def _update_entity_from_dict(self, record: ChangeRecord, data: dict[str, Any], session: Session) -> None:
        """
        Update a ChangeRecord from a dictionary.

        Args:
            record: ChangeRecord instance to update.
            data: Dictionary of updated attributes.
            session: SQLAlchemy session.
        """
        if "change_type" in data:
            record.change_type = data["change_type"]
        if "old_value" in data:
            record.old_value = data["old_value"]
        if "new_value" in data:
            record.new_value = data["new_value"]
        if "notes" in data:
            record.notes = data["notes"]

    def _entity_to_dict(self, record: ChangeRecord, include_details: bool = True) -> dict[str, Any]:
        """
        Convert a ChangeRecord to a dictionary.

        Args:
            record: ChangeRecord instance.
            include_details: Whether to include all details.
        Returns:
            Dictionary representation of the change record.
        """
        return {
            "id": record.id,
            "application_id": record.application_id,
            "created_at": record.created_at.isoformat(),
            "change_type": record.change_type,
            "old_value": record.old_value,
            "new_value": record.new_value,
            "notes": record.notes,
        }

    @db_operation
    def get_change_records(self, application_id: int, session: Session) -> list[dict[str, Any]]:
        """
        Get change records for an application.

        Args:
            application_id: ID of the application.
            session: SQLAlchemy session.
        Returns:
            List of change record dictionaries.
        """
        try:
            records = (
                session.query(ChangeRecord)
                .filter(ChangeRecord.application_id == application_id)
                .order_by(desc(ChangeRecord.created_at))
                .all()
            )
            return [record.to_dict() for record in records]
        except Exception as e:
            logger.error(f"Error fetching change records: {e}", exc_info=True)
            raise
