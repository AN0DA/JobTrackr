"""Service for providing analytics on job applications."""

import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from collections import Counter

from sqlalchemy import func, desc
from sqlalchemy.orm import joinedload

from src.db.models import Application, Company, Interaction, Reminder
from src.db.database import get_session

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics operations."""

    def get_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics for job applications."""
        session = get_session()
        try:
            result = {}

            # Get total applications
            total_apps = session.query(func.count(Application.id)).scalar() or 0
            result["total_applications"] = total_apps

            if total_apps == 0:
                # Return empty data if no applications exist
                return self._get_empty_analytics()

            # Get status counts
            status_counts = (
                session.query(Application.status, func.count(Application.id))
                .group_by(Application.status)
                .all()
            )
            result["status_counts"] = [
                (status, count) for status, count in status_counts
            ]

            # Calculate response rate
            applied_count = sum(
                count for status, count in status_counts if status != "SAVED"
            )
            responded_count = sum(
                count
                for status, count in status_counts
                if status
                in [
                    "PHONE_SCREEN",
                    "INTERVIEW",
                    "TECHNICAL_INTERVIEW",
                    "OFFER",
                    "ACCEPTED",
                    "REJECTED",
                ]
            )

            response_rate = int(
                (responded_count / applied_count * 100) if applied_count > 0 else 0
            )
            result["response_rate"] = response_rate

            # Calculate interview rate
            interview_count = sum(
                count
                for status, count in status_counts
                if status
                in ["INTERVIEW", "TECHNICAL_INTERVIEW", "OFFER", "ACCEPTED", "REJECTED"]
            )

            interview_rate = int(
                (interview_count / applied_count * 100) if applied_count > 0 else 0
            )
            result["interview_rate"] = interview_rate

            # Calculate average time to interview
            # This requires more complex query to find applications that progressed to interview
            # For now we'll use a placeholder
            result["avg_days_to_interview"] = self._calculate_avg_days_to_interview(
                session
            )

            # Calculate applications per week
            result["apps_per_week"] = self._calculate_apps_per_week(session)

            # Get weekly application counts for timeline
            result["weekly_applications"] = self._get_weekly_applications(session)

            # Get top companies applied to
            top_companies = (
                session.query(
                    Company.name, func.count(Application.id).label("app_count")
                )
                .join(Application)
                .group_by(Company.name)
                .order_by(desc("app_count"))
                .limit(5)
                .all()
            )

            result["top_companies"] = [
                {
                    "name": name,
                    "applications": count,
                    "responses": self._get_company_response_count(session, name),
                    "interviews": self._get_company_interview_count(session, name),
                }
                for name, count in top_companies
            ]

            # Get recent activity (status changes, interviews, etc.)
            result["recent_activity"] = self._get_recent_activity(session)

            return result

        except Exception as e:
            logger.error(f"Error fetching analytics: {e}")
            raise
        finally:
            session.close()

    def _get_empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics when no applications exist."""
        return {
            "total_applications": 0,
            "status_counts": [],
            "response_rate": 0,
            "interview_rate": 0,
            "avg_days_to_interview": 0,
            "apps_per_week": 0,
            "weekly_applications": [],
            "top_companies": [],
            "recent_activity": [],
        }

    def _calculate_avg_days_to_interview(self, session) -> int:
        """Calculate average days from application to interview."""
        try:
            # Get applications that reached interview stage
            interview_apps = (
                session.query(Application)
                .filter(
                    Application.status.in_(
                        [
                            "INTERVIEW",
                            "TECHNICAL_INTERVIEW",
                            "OFFER",
                            "ACCEPTED",
                            "REJECTED",
                        ]
                    )
                )
                .all()
            )

            # For now, just estimate based on applied date and typical timelines
            # In a real implementation, we'd track actual interview dates
            if not interview_apps:
                return 0

            # Placeholder calculation - in real system would use interaction dates
            total_days = sum(
                (datetime.now() - app.applied_date).days for app in interview_apps
            )
            return int(total_days / len(interview_apps))
        except Exception as e:
            logger.error(f"Error calculating avg days to interview: {e}")
            return 0

    def _calculate_apps_per_week(self, session) -> float:
        """Calculate average applications per week."""
        try:
            # Get earliest and latest application dates
            earliest = session.query(func.min(Application.applied_date)).scalar()
            latest = session.query(func.max(Application.applied_date)).scalar()

            if not earliest or not latest:
                return 0

            # Calculate number of weeks
            days = (latest - earliest).days + 1
            weeks = max(days / 7, 1)  # Avoid division by zero

            # Count total applications
            total_apps = session.query(func.count(Application.id)).scalar() or 0

            return round(total_apps / weeks, 1)
        except Exception as e:
            logger.error(f"Error calculating applications per week: {e}")
            return 0

    def _get_weekly_applications(self, session) -> List[Tuple[str, int]]:
        """Get application counts by week."""
        try:
            # Get applications from the last 8 weeks
            end_date = datetime.now()
            start_date = end_date - timedelta(weeks=8)

            applications = (
                session.query(Application)
                .filter(Application.applied_date >= start_date)
                .all()
            )

            # Group by week
            weekly_counts = Counter()

            for app in applications:
                # Get the week starting Monday
                week_start = app.applied_date - timedelta(
                    days=app.applied_date.weekday()
                )
                week_key = week_start.strftime("%m/%d")
                weekly_counts[week_key] += 1

            # Sort by week
            return sorted(
                weekly_counts.items(), key=lambda x: datetime.strptime(x[0], "%m/%d")
            )
        except Exception as e:
            logger.error(f"Error getting weekly applications: {e}")
            return []

    def _get_company_response_count(self, session, company_name: str) -> int:
        """Get number of responses from a company."""
        try:
            return (
                session.query(func.count(Application.id))
                .join(Company)
                .filter(
                    Company.name == company_name,
                    Application.status.in_(
                        [
                            "PHONE_SCREEN",
                            "INTERVIEW",
                            "TECHNICAL_INTERVIEW",
                            "OFFER",
                            "ACCEPTED",
                            "REJECTED",
                        ]
                    ),
                )
                .scalar()
                or 0
            )
        except Exception as e:
            logger.error(f"Error getting company response count: {e}")
            return 0

    def _get_company_interview_count(self, session, company_name: str) -> int:
        """Get number of interviews with a company."""
        try:
            return (
                session.query(func.count(Application.id))
                .join(Company)
                .filter(
                    Company.name == company_name,
                    Application.status.in_(
                        [
                            "INTERVIEW",
                            "TECHNICAL_INTERVIEW",
                            "OFFER",
                            "ACCEPTED",
                            "REJECTED",
                        ]
                    ),
                )
                .scalar()
                or 0
            )
        except Exception as e:
            logger.error(f"Error getting company interview count: {e}")
            return 0

    def _get_recent_activity(self, session) -> List[Dict[str, Any]]:
        """Get recent activity related to applications."""
        try:
            # Get recent applications
            recent_apps = (
                session.query(Application)
                .options(joinedload(Application.company))
                .order_by(Application.applied_date.desc())
                .limit(5)
                .all()
            )

            # Get recent interactions
            recent_interactions = (
                session.query(Interaction)
                .options(
                    joinedload(Interaction.application).joinedload(Application.company)
                )
                .order_by(Interaction.date.desc())
                .limit(5)
                .all()
            )

            # Get upcoming reminders
            upcoming_reminders = (
                session.query(Reminder)
                .filter(Reminder.completed is False, Reminder.date >= datetime.now())
                .options(
                    joinedload(Reminder.application).joinedload(Application.company)
                )
                .order_by(Reminder.date)
                .limit(5)
                .all()
            )

            # Combine and sort activities
            activities = []

            # Add applications
            for app in recent_apps:
                activities.append(
                    {
                        "date": app.applied_date.strftime("%Y-%m-%d"),
                        "type": f"Applied ({app.status})",
                        "company": app.company.name if app.company else "Unknown",
                        "details": f"{app.job_title} - {app.position}",
                    }
                )

            # Add interactions
            for interaction in recent_interactions:
                if interaction.application:
                    company_name = (
                        interaction.application.company.name
                        if interaction.application.company
                        else "Unknown"
                    )
                    activities.append(
                        {
                            "date": interaction.date.strftime("%Y-%m-%d"),
                            "type": interaction.type,
                            "company": company_name,
                            "details": interaction.notes[:50] + "..."
                            if interaction.notes and len(interaction.notes) > 50
                            else interaction.notes or "",
                        }
                    )

            # Add reminders
            for reminder in upcoming_reminders:
                if reminder.application:
                    company_name = (
                        reminder.application.company.name
                        if reminder.application.company
                        else "Unknown"
                    )
                    activities.append(
                        {
                            "date": reminder.date.strftime("%Y-%m-%d"),
                            "type": "Reminder",
                            "company": company_name,
                            "details": reminder.title,
                        }
                    )

            # Sort by date (most recent first)
            activities.sort(key=lambda x: x["date"], reverse=True)
            return activities[:10]  # Return top 10

        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []
