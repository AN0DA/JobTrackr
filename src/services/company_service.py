import logging
from typing import List, Optional, Dict, Any

from src.db.models import Company
from src.db.database import get_session

logger = logging.getLogger(__name__)


class CompanyService:
    """Service for company-related operations."""

    def get_company(self, id: int) -> Optional[Dict[str, Any]]:
        """Get a specific company by ID."""
        session = get_session()
        try:
            company = session.query(Company).filter(Company.id == id).first()
            if not company:
                return None

            return self._company_to_dict(company)
        except Exception as e:
            logger.error(f"Error fetching company {id}: {e}")
            raise
        finally:
            session.close()

    def get_companies(self) -> List[Dict[str, Any]]:
        """Get all companies."""
        session = get_session()
        try:
            companies = session.query(Company).all()
            return [self._company_to_dict(company, include_details=False) for company in companies]
        except Exception as e:
            logger.error(f"Error fetching companies: {e}")
            raise
        finally:
            session.close()

    def create_company(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new company."""
        session = get_session()
        try:
            # Create company object
            company = Company(
                name=data["name"],
                website=data.get("website"),
                industry=data.get("industry"),
                size=data.get("size"),
                logo=data.get("logo"),
                notes=data.get("notes")
            )

            # Add to session and commit
            session.add(company)
            session.commit()
            session.refresh(company)

            return self._company_to_dict(company)
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating company: {e}")
            raise
        finally:
            session.close()

    def update_company(self, id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing company."""
        session = get_session()
        try:
            # Get company
            company = session.query(Company).filter(Company.id == id).first()
            if not company:
                raise ValueError(f"Company with ID {id} not found")

            # Update fields
            if "name" in data:
                company.name = data["name"]
            if "website" in data:
                company.website = data["website"]
            if "industry" in data:
                company.industry = data["industry"]
            if "size" in data:
                company.size = data["size"]
            if "logo" in data:
                company.logo = data["logo"]
            if "notes" in data:
                company.notes = data["notes"]

            # Commit changes
            session.commit()
            session.refresh(company)

            return self._company_to_dict(company)
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating company {id}: {e}")
            raise
        finally:
            session.close()

    def delete_company(self, id: int) -> bool:
        """Delete a company."""
        session = get_session()
        try:
            company = session.query(Company).filter(Company.id == id).first()
            if not company:
                return False

            # Check if company has applications
            if company.applications:
                raise ValueError(f"Cannot delete company with ID {id} because it has associated applications")

            session.delete(company)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting company {id}: {e}")
            raise
        finally:
            session.close()

    def _company_to_dict(self, company: Company, include_details: bool = True) -> Dict[str, Any]:
        """Convert a Company object to a dictionary."""
        result = {
            "id": company.id,
            "name": company.name,
        }

        if include_details:
            result.update({
                "website": company.website,
                "industry": company.industry,
                "size": company.size,
                "logo": company.logo,
                "notes": company.notes
            })

        return result