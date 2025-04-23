"""GraphQL queries."""

import strawberry
from typing import List, Optional

from src.api.db.client import DgraphClient
from src.api.schema.types import Application, ApplicationStatus, DashboardStats
from src.api.services.application_service import ApplicationService

# Create a singleton DgraphClient
dgraph = DgraphClient()

@strawberry.type
class Query:
    @strawberry.field
    def get_application(self, id: strawberry.ID) -> Optional[Application]:
        """Get a specific application by ID."""
        service = ApplicationService(dgraph)
        return service.get_application(id)

    @strawberry.field
    def get_applications(
            self,
            status: Optional[ApplicationStatus] = None,
            offset: int = 0,
            limit: int = 10
    ) -> List[Application]:
        """Get a list of applications with optional status filter."""
        service = ApplicationService(dgraph)
        return service.get_applications(status, offset, limit)

    @strawberry.field
    def get_dashboard_stats(self) -> DashboardStats:
        """Get dashboard statistics."""
        service = ApplicationService(dgraph)
        return service.get_dashboard_stats()