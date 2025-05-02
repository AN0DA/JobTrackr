import logging
from datetime import datetime
from typing import Any

from sqlalchemy import desc, func, or_, update
from sqlalchemy.orm import Session, joinedload

from src.config import ApplicationStatus, ChangeType
from src.db.database import get_session
from src.db.models import Application, Company
from src.services.base_service import BaseService
from src.services.change_record_service import ChangeRecordService
from src.utils.decorators import db_operation

logger = logging.getLogger(__name__)


class ApplicationService(BaseService):
    """Service for application-related operations."""

    model_class = Application
    entity_name = "application"

    def _create_entity_from_dict(self, data: dict[str, Any], session: Session) -> Application:
        """Create an Application object from a dictionary."""
        # Handle date conversion if needed
        applied_date = data["applied_date"]
        if isinstance(applied_date, str):
            applied_date = datetime.fromisoformat(applied_date)

        return Application(
            job_title=data["job_title"],
            position=data["position"],
            location=data.get("location"),
            salary=data.get("salary"),
            status=data["status"],
            applied_date=applied_date,
            link=data.get("link"),
            description=data.get("description"),
            notes=data.get("notes"),
            company_id=data["company_id"],
        )

    def _update_entity_from_dict(self, app: Application, data: dict[str, Any], session: Session) -> None:
        """Update an Application object from a dictionary."""
        # Track changes for important fields
        change_records = []

        # Check for status change
        if "status" in data and data["status"] != app.status:
            change_records.append(
                {
                    "application_id": app.id,
                    "change_type": ChangeType.STATUS_CHANGE.value,
                    "old_value": app.status,
                    "new_value": data["status"],
                    "notes": f"Status changed from {app.status} to {data['status']}",
                }
            )

        # Update fields
        for key, value in data.items():
            if hasattr(app, key):
                # Special case for applied_date
                if key == "applied_date" and isinstance(value, str):
                    setattr(app, key, datetime.fromisoformat(value))
                else:
                    setattr(app, key, value)

        # Record changes after session is committed
        self._record_changes(app.id, change_records)

    def _record_changes(self, app_id: int, change_records: list[dict[str, Any]]) -> None:
        """Record changes to the application."""
        change_record_service = ChangeRecordService()
        for record in change_records:
            change_record_service.create(record)

    def _entity_to_dict(self, app: Application, include_details: bool = True) -> dict[str, Any]:
        """Convert an Application object to a dictionary."""
        result = {
            "id": app.id,
            "job_title": app.job_title,
            "position": app.position,
            "status": app.status,
            "applied_date": app.applied_date.isoformat(),
            "created_at": app.created_at.isoformat(),
        }

        # Add company information if available
        if app.company:
            result["company"] = {"id": app.company.id, "name": app.company.name}

        # Include additional details if requested
        if include_details:
            result.update(
                {
                    "location": app.location,
                    "salary": app.salary,
                    "link": app.link,
                    "description": app.description,
                    "notes": app.notes,
                    "updated_at": app.updated_at.isoformat() if app.updated_at else None,
                }
            )

        return result

    def get_applications(self, status: str | None = None, **kwargs) -> list[dict[str, Any]]:
        """Get applications with optional filtering and sorting."""
        session = get_session()
        try:
            query = session.query(Application).options(joinedload(Application.company))

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
            limit = kwargs.get("limit", 10)
            applications = query.offset(offset).limit(limit).all()

            # Convert to dictionaries
            return [self._entity_to_dict(app, include_details=False) for app in applications]

        except Exception as e:
            logger.error(f"Error fetching applications: {e}")
            raise
        finally:
            session.close()

    def search_applications(self, search_term: str) -> list[dict[str, Any]]:
        """Search for applications by keyword."""
        session = get_session()
        try:
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
        finally:
            session.close()

    def get_applications_by_company(self, company_id: int) -> list[dict[str, Any]]:
        """Get applications for a specific company."""
        session = get_session()
        try:
            query = session.query(Application).filter(Application.company_id == company_id)
            applications = query.order_by(Application.applied_date.desc()).all()
            return [self._entity_to_dict(app, include_details=False) for app in applications]
        except Exception as e:
            logger.error(f"Error fetching applications for company {company_id}: {e}")
            raise
        finally:
            session.close()

    def get_applications_for_export(
        self, include_notes=True, include_interactions=True, include_reminders=True
    ) -> list[dict[str, Any]]:
        """Get all applications with optional details for export."""
        session = get_session()
        try:
            # Base query for applications with company info
            query = (
                session.query(Application)
                .options(joinedload(Application.company))
                .order_by(Application.applied_date.desc())
            )

            applications = query.all()
            result = []

            for app in applications:
                # Start with basic application info
                app_data = {
                    "id": app.id,
                    "job_title": app.job_title,
                    "company": app.company.name if app.company else "",
                    "company_website": app.company.website if app.company else "",
                    "position": app.position,
                    "location": app.location or "",
                    "salary": app.salary or "",
                    "status": app.status,
                    "applied_date": app.applied_date.isoformat(),
                    "link": app.link or "",
                }

                # Add notes if requested
                if include_notes:
                    app_data["description"] = app.description or ""
                    app_data["notes"] = app.notes or ""

                # Add interactions if requested
                if include_interactions and app.interactions:
                    interactions = []
                    for _, interaction in enumerate(sorted(app.interactions, key=lambda x: x.date)):
                        interactions.append(
                            {
                                "date": interaction.date.isoformat(),
                                "type": interaction.type,
                                "notes": interaction.notes or "",
                            }
                        )
                    app_data["interactions"] = interactions

                result.append(app_data)

            return result

        except Exception as e:
            logger.error(f"Error getting applications for export: {e}")
            raise
        finally:
            session.close()

    def get_dashboard_stats(self) -> dict[str, Any]:
        """Get dashboard statistics."""
        session = get_session()
        try:
            # Get total applications count
            total_count = session.query(func.count(Application.id)).scalar() or 0

            # Get counts by status
            status_counts = []
            for status in ApplicationStatus:
                count = (
                    session.query(func.count(Application.id)).filter(Application.status == status.value).scalar() or 0
                )
                status_counts.append({"status": status.value, "count": count})

            # Get recent applications
            recent_apps = session.query(Application).order_by(Application.applied_date.desc()).limit(5).all()
            recent_applications = [self._entity_to_dict(app, include_details=False) for app in recent_apps]

            return {
                "total_applications": total_count,
                "applications_by_status": status_counts,
                "recent_applications": recent_applications,
            }
        except Exception as e:
            logger.error(f"Error fetching dashboard stats: {e}")
            raise
        finally:
            session.close()

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
