"""Company service providing business logic for company-related operations."""

import logging
from typing import Optional

from src.api.db.client import DgraphClient
from src.api.schema.types import Company
from src.api.schema.inputs import CompanyInput

logger = logging.getLogger(__name__)


class CompanyService:
    def __init__(self, dgraph_client: DgraphClient):
        self.db = dgraph_client

    def create_company(self, input: CompanyInput) -> Company:
        """Create a new company."""
        try:
            # Convert to Dgraph format
            company_data = {
                "name": input.name,
                "website": input.website,
                "industry": input.industry,
                "size": input.size,
                "logo": input.logo,
                "notes": input.notes,
                "dgraph.type": "Company"  # Explicitly set Dgraph type
            }

            # Create the company
            result = self.db.mutate(company_data)
            if not result.get("uids") or "blank-0" not in result["uids"]:
                raise Exception("Failed to create company")

            company_id = result["uids"]["blank-0"]

            # Get and return the created company
            return self.get_company(company_id)
        except Exception as e:
            logger.error(f"Error creating company: {e}")
            raise

    def get_company(self, id: str) -> Optional[Company]:
        """Fetch a specific company by ID."""
        try:
            query = """
            query GetCompany($id: string) {
              company(func: uid($id)) {
                id: uid
                name
                website
                industry
                size
                logo
                notes
              }
            }
            """
            result = self.db.query(query, {"id": id})

            if not result.get("company") or not result["company"]:
                logger.info(f"Company with ID {id} not found")
                return None

            company_data = result["company"][0]

            return Company(
                id=company_data["id"],
                name=company_data["name"],
                website=company_data.get("website"),
                industry=company_data.get("industry"),
                size=company_data.get("size"),
                logo=company_data.get("logo"),
                notes=company_data.get("notes")
            )
        except Exception as e:
            logger.error(f"Error fetching company {id}: {e}")
            raise
