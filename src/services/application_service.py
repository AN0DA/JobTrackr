import logging
from datetime import datetime
from typing import Any

from sqlalchemy import desc, func, or_, update
from sqlalchemy.orm import Session, joinedload

from src.config import ApplicationStatus, ChangeType
from src.db.models import Application, Company
from src.services.base_service import BaseService
from src.services.change_record_service import ChangeRecordService
from src.utils.decorators import db_operation

logger = logging.getLogger(__name__)


class ApplicationService(BaseService):
    """
    Service for application-related operations.

    Provides methods to create, update, delete, and retrieve job applications and their related data.
    """

    model_class = Application
    entity_name = "application"

    def _create_entity_from_dict(self, data: dict[str, Any], session: Session) -> Application:
        """
        Create an Application object from a dictionary.

        Args:
            data: Dictionary of application attributes.
            session: SQLAlchemy session.
        Returns:
            Application instance.
        """
        # Handle date conversion if needed
        applied_date = data["applied_date"]
        if isinstance(applied_date, str):
            applied_date = datetime.fromisoformat(applied_date)

        return Application(
            job_title=data["job_title"],
            position=data["position"],
            location=data.get("location"),
            salary_min=data.get("salary_min"),
            salary_max=data.get("salary_max"),
            status=data["status"],
            applied_date=applied_date,
            link=data.get("link"),
            description=data.get("description"),
            notes=data.get("notes"),
            company_id=data["company_id"],
        )

    def _update_entity_from_dict(self, entity: Application, data: dict[str, Any], session: Session) -> None:
        """
        Update an Application object from a dictionary.

        Args:
            entity: Application instance to update.
            data: Dictionary of updated attributes.
            session: SQLAlchemy session.
        """
        # Track changes for important fields
        change_records = []

        # Check for status change
        if "status" in data and data["status"] != entity.status:
            change_records.append(
                {
                    "application_id": entity.id,
                    "change_type": ChangeType.STATUS_CHANGE.value,
                    "old_value": entity.status,
                    "new_value": data["status"],
                    "notes": f"Status changed from {entity.status} to {data['status']}",
                }
            )

        # Update fields
        for key, value in data.items():
            if hasattr(entity, key):
                # Special case for applied_date
                if key == "applied_date" and isinstance(value, str):
                    setattr(entity, key, datetime.fromisoformat(value))
                else:
                    setattr(entity, key, value)

        # Record changes after session is committed
        self._record_changes(entity.id, change_records)

    def _record_changes(self, app_id: int, change_records: list[dict[str, Any]]) -> None:
        """Record changes to the application."""
        change_record_service = ChangeRecordService()
        for record in change_records:
            change_record_service.create(record)

    def _entity_to_dict(self, application: Application, include_details: bool = True) -> dict[str, Any]:
        """
        Convert an Application object to a dictionary.

        Args:
            application: Application instance.
            include_details: Whether to include all details.
        Returns:
            Dictionary representation of the application.
        """
        result = {
            "id": application.id,
            "job_title": application.job_title,
            "position": application.position,
            "status": application.status,
            "applied_date": application.applied_date.isoformat(),
            "created_at": application.created_at.isoformat(),
        }

        # Add company information if available
        if application.company:
            result["company"] = {"id": application.company.id, "name": application.company.name}

        # Include additional details if requested
        if include_details:
            result.update(
                {
                    "location": application.location,
                    "salary_min": application.salary_min,
                    "salary_max": application.salary_max,
                    "link": application.link,
                    "description": application.description,
                    "notes": application.notes,
                    "updated_at": application.updated_at.isoformat() if application.updated_at else None,
                }
            )

        return result

    def get_applications(self, session: Session, company_id: int | None = None, status: str | None = None, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Get applications with optional filtering by company or status.

        Args:
            session: SQLAlchemy session.
            company_id: Optional company ID to filter applications.
            status: Optional status to filter applications.
            **kwargs: Additional query options (offset, limit).
        Returns:
            List of application dictionaries.
        """
        try:
            query = session.query(Application).options(joinedload(Application.company))

            if company_id:
                query = query.filter(Application.company_id == company_id)
            if status:
                query = query.filter(Application.status == status)

            # Apply sorting
            sort_by = kwargs.get("sort_by", "applied_date")
            sort_desc = kwargs.get("sort_desc", True)

            if sort_by == "job_title":
                query = query.order_by(desc(Application.job_title) if sort_desc else Application.job_title)
            elif sort_by == "position":
                query = query.order_by(desc(Application.position) if sort_desc else Application.position)
            elif sort_by == "company":
                query = query.join(Company).order_by(desc(Company.name) if sort_desc else Company.name)
            elif sort_by == "status":
                query = query.order_by(desc(Application.status) if sort_desc else Application.status)
            else:  # Default to applied_date
                query = query.order_by(desc(Application.applied_date) if sort_desc else Application.applied_date)

            # Apply pagination
            offset = kwargs.get("offset", 0)
            limit = kwargs.get("limit", None)
            if limit is not None:
                applications = query.offset(offset).limit(limit).all()
            else:
                applications = query.offset(offset).all()

            # Convert to dictionaries
            return [self._entity_to_dict(app, include_details=False) for app in applications]

        except Exception as e:
            logger.error(f"Error fetching applications: {e}")
            raise

    def search_applications(self, search_term: str, session: Session) -> list[dict[str, Any]]:
        """
        Search for applications by position, company, or notes.

        Args:
            search_term: The search string.
            session: SQLAlchemy session.
        Returns:
            List of application dictionaries matching the search.
        """
        search_pattern = f"%{search_term}%"

        # Create base query
        query = session.query(Application).join(Company, isouter=True)

        # Add search conditions
        search_fields = [
            Application.job_title,
            Application.position,
            Application.description,
            Application.notes,
            Application.location,
            Company.name,
        ]

        conditions = [field.ilike(search_pattern) for field in search_fields]
        query = query.filter(or_(*conditions)).order_by(Application.applied_date.desc())

        applications = query.all()
        return [self._entity_to_dict(app, include_details=False) for app in applications]

    def get_applications_for_contact(self, contact_id: int, session: Session) -> list[dict[str, Any]]:
        """
        Get all applications associated with a contact.

        Args:
            contact_id: ID of the contact.
            session: SQLAlchemy session.
        Returns:
            List of application dictionaries associated with the contact.
        """
        # Implementation needed
        raise NotImplementedError("Method not implemented")

    def get_applications_for_company(self, company_id: int, session: Session) -> list[dict[str, Any]]:
        """
        Get all applications for a specific company.

        Args:
            company_id: ID of the company.
            session: SQLAlchemy session.
        Returns:
            List of application dictionaries for the company.
        """
        try:
            query = session.query(Application).filter(Application.company_id == company_id)
            applications = query.order_by(Application.applied_date.desc()).all()
            return [self._entity_to_dict(app, include_details=False) for app in applications]
        except Exception as e:
            logger.error(f"Error fetching applications for company {company_id}: {e}")
            raise

    def get_status_counts(self, session: Session) -> dict[str, int]:
        """
        Get counts of applications by status.

        Args:
            session: SQLAlchemy session.
        Returns:
            Dictionary mapping status to count.
        """
        # Implementation needed
        raise NotImplementedError("Method not implemented")

    def get_recent_applications(self, session: Session, limit: int = 5) -> list[dict[str, Any]]:
        """
        Get the most recently created applications.

        Args:
            session: SQLAlchemy session.
            limit: Maximum number of recent applications to retrieve.
        Returns:
            List of recent application dictionaries.
        """
        # Implementation needed
        raise NotImplementedError("Method not implemented")

    def add_interaction(self, data: dict[str, Any]) -> dict[str, Any]:
        """Add an interaction to an application."""
        from src.services.interaction_service import InteractionService

        interaction_service = InteractionService()
        return interaction_service.create(data)

    @db_operation
    def update_status(self, application_id, new_status, session):
        """
        Update the status of an application directly using its ID.
        This avoids the entity refresh issue in the base update method.

        Args:
            application_id: The ID of the application to update
            new_status: The new status to set
        """
        try:
            # Używamy bezpośredniego zapytania UPDATE, które nie wymaga odświeżania encji
            update_stmt = update(Application).where(Application.id == application_id).values(status=new_status)
            session.execute(update_stmt)
            session.commit()
            logger.info(f"Updated application status for ID {application_id} to {new_status}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating application status for ID {application_id}: {e}", exc_info=True)
            raise
        finally:
            session.close()
