"""Application service providing business logic for application-related operations."""

import logging
from datetime import datetime
from typing import List, Optional

from src.api.db.client import DgraphClient
from src.api.schema.types import Application, ApplicationStatus, Company, DashboardStats, StatusCount, Reminder
from src.api.schema.inputs import ApplicationInput

logger = logging.getLogger(__name__)


class ApplicationService:
    def __init__(self, dgraph_client: DgraphClient):
        self.db = dgraph_client

    def get_application(self, id: str) -> Optional[Application]:
        """Fetch a specific application by ID."""
        query = """
        query GetApplication($id: string) {
          application(func: uid($id)) {
            id: uid
            jobTitle
            position
            location
            salary
            status
            appliedDate
            link
            description
            notes
            tags
            createdAt
            updatedAt
            company {
              id: uid
              name
              website
              industry
              size
              logo
            }
          }
        }
        """
        try:
            result = self.db.query(query, {"id": id})
            if not result.get("application"):
                logger.info(f"Application with ID {id} not found")
                return None

            app_data = result["application"][0]
            return Application(
                id=app_data["id"],
                job_title=app_data["jobTitle"],
                position=app_data["position"],
                location=app_data.get("location"),
                salary=app_data.get("salary"),
                status=ApplicationStatus(app_data["status"]),
                applied_date=datetime.fromisoformat(app_data["appliedDate"]),
                link=app_data.get("link"),
                description=app_data.get("description"),
                notes=app_data.get("notes"),
                tags=app_data.get("tags"),
                created_at=datetime.fromisoformat(app_data["createdAt"]),
                updated_at=datetime.fromisoformat(app_data["updatedAt"]) if app_data.get("updatedAt") else None,
                company=Company(
                    id=app_data["company"]["id"],
                    name=app_data["company"]["name"],
                    website=app_data["company"].get("website"),
                    industry=app_data["company"].get("industry"),
                    size=app_data["company"].get("size"),
                    logo=app_data["company"].get("logo")
                ) if "company" in app_data else None
            )
        except Exception as e:
            logger.error(f"Error fetching application {id}: {e}")
            raise

    def get_applications(
            self,
            status: Optional[ApplicationStatus] = None,
            offset: int = 0,
            limit: int = 10
    ) -> List[Application]:
        """Fetch applications with optional filtering by status."""
        try:
            if status:
                query = """
                query GetApplications($status: string, $offset: string, $limit: string) {
                  applications(func: eq(status, $status), offset: $offset, first: $limit, orderdesc: appliedDate) {
                    id: uid
                    jobTitle
                    position
                    location
                    status
                    appliedDate
                    createdAt
                    company {
                      id: uid
                      name
                    }
                  }
                }
                """
                variables = {"status": status.value, "offset": str(offset), "limit": str(limit)}
            else:
                query = """
                query GetApplications($offset: string, $limit: string) {
                  applications(func: has(jobTitle), offset: $offset, first: $limit, orderdesc: appliedDate) {
                    id: uid
                    jobTitle
                    position
                    location
                    status
                    appliedDate
                    createdAt
                    company {
                      id: uid
                      name
                    }
                  }
                }
                """
                variables = {"offset": str(offset), "limit": str(limit)}

            result = self.db.query(query, variables)
            applications = []

            for app_data in result.get("applications", []):
                applications.append(Application(
                    id=app_data["id"],
                    job_title=app_data["jobTitle"],
                    position=app_data["position"],
                    location=app_data.get("location"),
                    status=ApplicationStatus(app_data["status"]),
                    applied_date=datetime.fromisoformat(app_data["appliedDate"]),
                    created_at=datetime.fromisoformat(app_data["createdAt"]),
                    company=Company(
                        id=app_data["company"]["id"],
                        name=app_data["company"]["name"]
                    ) if "company" in app_data else None
                ))

            return applications
        except Exception as e:
            logger.error(f"Error fetching applications: {e}")
            raise

    def create_application(self, input: ApplicationInput) -> Application:
        """Create a new application."""
        try:
            now = datetime.utcnow()

            # Convert to Dgraph format
            application_data = {
                "jobTitle": input.job_title,
                "position": input.position,
                "location": input.location,
                "salary": input.salary,
                "status": input.status.value,
                "appliedDate": input.applied_date.isoformat(),
                "link": input.link,
                "description": input.description,
                "notes": input.notes,
                "tags": input.tags,
                "createdAt": now.isoformat(),
                "company": {
                    "uid": input.company_id
                },
                "dgraph.type": "Application"  # Explicitly set Dgraph type
            }

            # Create the application
            result = self.db.mutate(application_data)
            if not result.get("uids") or "blank-0" not in result["uids"]:
                raise Exception("Failed to create application")

            app_id = result["uids"].get("blank-0")

            # Return the created application
            return self.get_application(app_id)
        except Exception as e:
            logger.error(f"Error creating application: {e}")
            raise

    def get_dashboard_stats(self) -> DashboardStats:
        """Get dashboard statistics."""
        try:
            # Get total applications count
            count_query = """
            {
              totalCount(func: has(jobTitle)) {
                count(uid)
              }
            }
            """
            count_result = self.db.query(count_query)
            total_count = count_result.get("totalCount", [{"count": 0}])[0]["count"]

            # Get applications by status
            status_query = """
            {
              saved(func: eq(status, "SAVED")) {
                count(uid)
              }
              applied(func: eq(status, "APPLIED")) {
                count(uid)
              }
              phoneScreen(func: eq(status, "PHONE_SCREEN")) {
                count(uid)
              }
              interview(func: eq(status, "INTERVIEW")) {
                count(uid)
              }
              technicalInterview(func: eq(status, "TECHNICAL_INTERVIEW")) {
                count(uid)
              }
              offer(func: eq(status, "OFFER")) {
                count(uid)
              }
              accepted(func: eq(status, "ACCEPTED")) {
                count(uid)
              }
              rejected(func: eq(status, "REJECTED")) {
                count(uid)
              }
              withdrawn(func: eq(status, "WITHDRAWN")) {
                count(uid)
              }
            }
            """
            status_result = self.db.query(status_query)

            # Get recent applications
            recent_query = """
            {
              recentApps(func: has(jobTitle), orderdesc: appliedDate, first: 5) {
                id: uid
                jobTitle
                position
                status
                appliedDate
                company {
                  id: uid
                  name
                }
              }
            }
            """
            recent_result = self.db.query(recent_query)

            # Get upcoming reminders
            reminders_query = """
            {
              upcomingReminders(func: eq(completed, false), orderasc: date, first: 5) {
                id: uid
                title
                description
                date
                completed
                application {
                  id: uid
                }
              }
            }
            """
            reminders_result = self.db.query(reminders_query)

            # Process status counts
            status_counts = []
            for status in ApplicationStatus:
                key = status.name.lower()
                if key == "phone_screen":
                    key = "phoneScreen"
                elif key == "technical_interview":
                    key = "technicalInterview"

                count = 0
                if key in status_result and status_result[key]:
                    count = status_result[key][0].get("count", 0)

                status_counts.append(StatusCount(
                    status=status,
                    count=count
                ))

            # Process recent applications
            recent_applications = []
            for app_data in recent_result.get("recentApps", []):
                recent_applications.append(Application(
                    id=app_data["id"],
                    job_title=app_data["jobTitle"],
                    position=app_data["position"],
                    status=ApplicationStatus(app_data["status"]),
                    applied_date=datetime.fromisoformat(app_data["appliedDate"]),
                    created_at=datetime.now(),  # Default value as it's required
                    company=Company(
                        id=app_data["company"]["id"],
                        name=app_data["company"]["name"]
                    ) if "company" in app_data else None
                ))

            # Process reminders
            reminders = []
            for reminder_data in reminders_result.get("upcomingReminders", []):
                reminders.append(Reminder(
                    id=reminder_data["id"],
                    title=reminder_data["title"],
                    description=reminder_data.get("description"),
                    date=datetime.fromisoformat(reminder_data["date"]),
                    completed=reminder_data["completed"],
                    application_id=reminder_data["application"]["id"] if "application" in reminder_data else None
                ))

            return DashboardStats(
                total_applications=total_count,
                applications_by_status=status_counts,
                recent_applications=recent_applications,
                upcoming_reminders=reminders
            )
        except Exception as e:
            logger.error(f"Error fetching dashboard stats: {e}")
            raise