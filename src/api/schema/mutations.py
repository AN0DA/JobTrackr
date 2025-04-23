"""GraphQL mutations."""

import strawberry

from src.api.db.client import DgraphClient
from src.api.schema.types import Application, Company
from src.api.schema.inputs import ApplicationInput, CompanyInput
from src.api.services.application_service import ApplicationService
from src.api.services.company_service import CompanyService

# Create a singleton DgraphClient
dgraph = DgraphClient()

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_application(self, input: ApplicationInput) -> Application:
        """Create a new job application."""
        service = ApplicationService(dgraph)
        return service.create_application(input)

    @strawberry.mutation
    def create_company(self, input: CompanyInput) -> Company:
        """Create a new company."""
        service = CompanyService(dgraph)
        return service.create_company(input)
