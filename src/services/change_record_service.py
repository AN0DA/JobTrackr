import logging
from typing import List, Dict, Any

from sqlalchemy import desc

from src.db.models import ChangeRecord
from src.db.database import get_session

logger = logging.getLogger(__name__)


class ChangeRecordService:
    """Service for managing change records."""

    def create_change_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new change record."""
        session = get_session()
        try:
            # Create change record
            record = ChangeRecord(
                application_id=data["application_id"],
                change_type=data["change_type"],
                old_value=data.get("old_value"),
                new_value=data.get("new_value"),
                notes=data.get("notes"),
            )

            # Add to session and commit
            session.add(record)
            session.commit()
            session.refresh(record)

            return self._record_to_dict(record)
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating change record: {e}")
            raise
        finally:
            session.close()

    def get_change_records(self, application_id: int) -> List[Dict[str, Any]]:
        """Get change records for an application."""
        session = get_session()
        try:
            records = (
                session.query(ChangeRecord)
                .filter(ChangeRecord.application_id == application_id)
                .order_by(desc(ChangeRecord.timestamp))
                .all()
            )

            return [self._record_to_dict(record) for record in records]
        except Exception as e:
            logger.error(f"Error fetching change records: {e}")
            raise
        finally:
            session.close()

    def _record_to_dict(self, record: ChangeRecord) -> Dict[str, Any]:
        """Convert a ChangeRecord to a dictionary."""
        return {
            "id": record.id,
            "application_id": record.application_id,
            "timestamp": record.timestamp.isoformat(),
            "change_type": record.change_type,
            "old_value": record.old_value,
            "new_value": record.new_value,
            "notes": record.notes,
        }
