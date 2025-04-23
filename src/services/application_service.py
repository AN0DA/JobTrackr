import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, desc

from src.db.models import Application, Company, Contact, Interaction, Document, Reminder, ApplicationStatus
from src.db.database import get_session

logger = logging.getLogger(__name__)


class ApplicationService:
    """Service for application-related operations."""

    def get_application(self, id: int) -> Optional[Dict[str, Any]]:
        """Get a specific application by ID."""
        session = get_session()
        try:
            app = session.query(Application).filter(Application.id == id).first()
            if not app:
                return None

            return self._application_to_dict(app)
        except Exception as e:
            logger.error(f"Error fetching application {id}: {e}")
            raise
        finally:
            session.close()

    def get_applications(
            self,
            status: Optional[str] = None,
            offset: int = 0,
            limit: int = 10,
            sort_by: str = "applied_date",
            sort_desc: bool = True
    ) -> List[Dict[str, Any]]:
        """Get applications with optional filtering and sorting."""
        session = get_session()
        try:
            query = session.query(Application).options(
                joinedload(Application.company)
            )

            if status:
                query = query.filter(Application.status == status)

            # Apply sorting
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
            applications = query.offset(offset).limit(limit).all()

            # Convert to dictionaries
            return [self._application_to_dict(app, include_details=False) for app in applications]

        except Exception as e:
            logger.error(f"Error fetching applications: {e}")
            raise
        finally:
            session.close()

    def create_application(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new application."""
        session = get_session()
        try:
            # Process tags if present
            tags = data.pop("tags", None)

            # Create application object
            app = Application(
                job_title=data["job_title"],
                position=data["position"],
                location=data.get("location"),
                salary=data.get("salary"),
                status=data["status"],
                applied_date=datetime.fromisoformat(data["applied_date"]) if isinstance(data["applied_date"], str) else
                data["applied_date"],
                link=data.get("link"),
                description=data.get("description"),
                notes=data.get("notes"),
                company_id=data["company_id"]
            )

            # Set tags if they were provided
            if tags:
                app.tags = tags

            # Add to session and commit
            session.add(app)
            session.commit()
            session.refresh(app)

            return self._application_to_dict(app)
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating application: {e}")
            raise
        finally:
            session.close()

    def update_application(self, id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing application."""
        session = get_session()
        try:
            # Get application
            app = session.query(Application).filter(Application.id == id).first()
            if not app:
                raise ValueError(f"Application with ID {id} not found")

            # Handle tags separately
            if "tags" in data:
                app.tags = data.pop("tags")

            # Update other fields
            for key, value in data.items():
                if hasattr(app, key):
                    if key == "applied_date" and isinstance(value, str):
                        setattr(app, key, datetime.fromisoformat(value))
                    else:
                        setattr(app, key, value)

            # Commit changes
            session.commit()
            session.refresh(app)

            return self._application_to_dict(app)
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating application {id}: {e}")
            raise
        finally:
            session.close()

    def search_applications(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for applications by keyword."""
        session = get_session()
        try:
            # Use ilike for case-insensitive search across multiple columns
            search_pattern = f"%{search_term}%"

            query = session.query(Application).join(
                Company, Application.company_id == Company.id, isouter=True
            ).filter(
                or_(
                    Application.job_title.ilike(search_pattern),
                    Application.position.ilike(search_pattern),
                    Application.description.ilike(search_pattern),
                    Application.notes.ilike(search_pattern),
                    Application.location.ilike(search_pattern),
                    Company.name.ilike(search_pattern)
                )
            ).order_by(Application.applied_date.desc())

            applications = query.all()
            return [self._application_to_dict(app, include_details=False) for app in applications]

        except Exception as e:
            logger.error(f"Error searching applications: {e}")
            raise
        finally:
            session.close()

    def get_applications_for_export(self, include_notes=True, include_interactions=True, include_reminders=True) -> \
    List[Dict[str, Any]]:
        """Get all applications with optional details for export."""
        session = get_session()
        try:
            # Base query for applications with company info
            query = session.query(Application).options(
                joinedload(Application.company)
            ).order_by(Application.applied_date.desc())

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
                    "link": app.link or ""
                }

                # Add tags
                if app.tags:
                    app_data["tags"] = ", ".join(app.tags)

                # Add notes if requested
                if include_notes:
                    app_data["description"] = app.description or ""
                    app_data["notes"] = app.notes or ""

                # Add interactions if requested
                if include_interactions and app.interactions:
                    interactions = []
                    for i, interaction in enumerate(sorted(app.interactions, key=lambda x: x.date)):
                        interactions.append({
                            "date": interaction.date.isoformat(),
                            "type": interaction.type,
                            "notes": interaction.notes or ""
                        })
                    app_data["interactions"] = interactions

                # Add reminders if requested
                if include_reminders and app.reminders:
                    reminders = []
                    for i, reminder in enumerate(sorted(app.reminders, key=lambda x: x.date)):
                        reminders.append({
                            "title": reminder.title,
                            "date": reminder.date.isoformat(),
                            "completed": "Yes" if reminder.completed else "No",
                            "description": reminder.description or ""
                        })
                    app_data["reminders"] = reminders

                result.append(app_data)

            return result

        except Exception as e:
            logger.error(f"Error getting applications for export: {e}")
            raise
        finally:
            session.close()

    def _application_to_dict(self, app: Application, include_details: bool = True) -> Dict[str, Any]:
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
            result["company"] = {
                "id": app.company.id,
                "name": app.company.name
            }

        # Include additional details if requested
        if include_details:
            result.update({
                "location": app.location,
                "salary": app.salary,
                "link": app.link,
                "description": app.description,
                "notes": app.notes,
                "tags": app.tags,  # Now properly handled
                "updated_at": app.updated_at.isoformat() if app.updated_at else None,
            })

        return result

    def delete_application(self, id: int) -> bool:
        """Delete an application."""
        session = get_session()
        try:
            app = session.query(Application).filter(Application.id == id).first()
            if not app:
                return False

            session.delete(app)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting application {id}: {e}")
            raise
        finally:
            session.close()

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        session = get_session()
        try:
            # Get total applications count
            total_count = session.query(func.count(Application.id)).scalar() or 0

            # Get counts by status
            status_counts = []
            for status in ApplicationStatus:
                count = session.query(func.count(Application.id)).filter(
                    Application.status == status.value).scalar() or 0
                status_counts.append({
                    "status": status.value,
                    "count": count
                })

            # Get recent applications
            recent_apps = session.query(Application).order_by(Application.applied_date.desc()).limit(5).all()
            recent_applications = [self._application_to_dict(app, include_details=False) for app in recent_apps]

            # Get upcoming reminders
            upcoming_reminders = session.query(Reminder).filter(Reminder.completed == False).order_by(
                Reminder.date).limit(5).all()
            reminders = [self._reminder_to_dict(reminder) for reminder in upcoming_reminders]

            return {
                "total_applications": total_count,
                "applications_by_status": status_counts,
                "recent_applications": recent_applications,
                "upcoming_reminders": reminders
            }
        except Exception as e:
            logger.error(f"Error fetching dashboard stats: {e}")
            raise
        finally:
            session.close()

    def add_interaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an interaction to an application."""
        session = get_session()
        try:
            from src.db.models import Interaction

            # Create interaction object
            interaction = Interaction(
                application_id=data["application_id"],
                type=data["type"],
                date=datetime.fromisoformat(data["date"]) if isinstance(data["date"], str) else data["date"],
                notes=data.get("notes")
            )

            # Add to session and commit
            session.add(interaction)
            session.commit()
            session.refresh(interaction)

            return {
                "id": interaction.id,
                "type": interaction.type,
                "date": interaction.date.isoformat(),
                "notes": interaction.notes,
                "application_id": interaction.application_id
            }
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating interaction: {e}")
            raise
        finally:
            session.close()

    def _application_to_dict(self, app: Application, include_details: bool = True) -> Dict[str, Any]:
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
            result["company"] = {
                "id": app.company.id,
                "name": app.company.name
            }

        # Include additional details if requested
        if include_details:
            result.update({
                "location": app.location,
                "salary": app.salary,
                "link": app.link,
                "description": app.description,
                "notes": app.notes,
                "updated_at": app.updated_at.isoformat() if app.updated_at else None,
            })

        return result

    def _reminder_to_dict(self, reminder: Reminder) -> Dict[str, Any]:
        """Convert a Reminder object to a dictionary."""
        return {
            "id": reminder.id,
            "title": reminder.title,
            "description": reminder.description,
            "date": reminder.date.isoformat(),
            "completed": reminder.completed,
            "application_id": reminder.application_id
        }