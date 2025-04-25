"""Service for reminder-related operations."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime


from src.db.models import Reminder
from src.db.database import get_session

logger = logging.getLogger(__name__)


class ReminderService:
    """Service for reminder-related operations."""

    def get_reminder(self, id: int) -> Optional[Dict[str, Any]]:
        """Get a specific reminder by ID."""
        session = get_session()
        try:
            reminder = session.query(Reminder).filter(Reminder.id == id).first()
            if not reminder:
                return None

            return self._reminder_to_dict(reminder)
        except Exception as e:
            logger.error(f"Error fetching reminder {id}: {e}")
            raise
        finally:
            session.close()

    def get_reminders(
        self, application_id: Optional[int] = None, completed: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Get reminders with optional filtering."""
        session = get_session()
        try:
            query = session.query(Reminder)

            if application_id is not None:
                query = query.filter(Reminder.application_id == application_id)

            if completed is not None:
                query = query.filter(Reminder.completed == completed)

            # Order by date
            query = query.order_by(Reminder.date)

            reminders = query.all()
            return [self._reminder_to_dict(reminder) for reminder in reminders]
        except Exception as e:
            logger.error(f"Error fetching reminders: {e}")
            raise
        finally:
            session.close()

    def create_reminder(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new reminder."""
        session = get_session()
        try:
            # Create reminder object
            reminder = Reminder(
                title=data["title"],
                description=data.get("description"),
                date=datetime.fromisoformat(data["date"])
                if isinstance(data["date"], str)
                else data["date"],
                completed=data.get("completed", False),
                application_id=data.get("application_id"),
            )

            # Add to session and commit
            session.add(reminder)
            session.commit()
            session.refresh(reminder)

            return self._reminder_to_dict(reminder)
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating reminder: {e}")
            raise
        finally:
            session.close()

    def update_reminder(self, id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing reminder."""
        session = get_session()
        try:
            # Get reminder
            reminder = session.query(Reminder).filter(Reminder.id == id).first()
            if not reminder:
                raise ValueError(f"Reminder with ID {id} not found")

            # Update fields
            if "title" in data:
                reminder.title = data["title"]
            if "description" in data:
                reminder.description = data["description"]
            if "date" in data:
                reminder.date = (
                    datetime.fromisoformat(data["date"])
                    if isinstance(data["date"], str)
                    else data["date"]
                )
            if "completed" in data:
                reminder.completed = data["completed"]
            if "application_id" in data:
                reminder.application_id = data["application_id"]

            # Commit changes
            session.commit()
            session.refresh(reminder)

            return self._reminder_to_dict(reminder)
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating reminder {id}: {e}")
            raise
        finally:
            session.close()

    def delete_reminder(self, id: int) -> bool:
        """Delete a reminder."""
        session = get_session()
        try:
            reminder = session.query(Reminder).filter(Reminder.id == id).first()
            if not reminder:
                return False

            session.delete(reminder)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting reminder {id}: {e}")
            raise
        finally:
            session.close()

    def _reminder_to_dict(self, reminder: Reminder) -> Dict[str, Any]:
        """Convert a Reminder object to a dictionary."""
        return {
            "id": reminder.id,
            "title": reminder.title,
            "description": reminder.description,
            "date": reminder.date.isoformat(),
            "completed": reminder.completed,
            "application_id": reminder.application_id,
        }
