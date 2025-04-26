import logging
from typing import Any

from src.db.database import get_session
from src.db.models import Company, CompanyRelationship, CompanyType

logger = logging.getLogger(__name__)


class CompanyService:
    """Service for company-related operations."""

    def get_company(self, _id: int) -> dict[str, Any] | None:
        """Get a specific company by ID."""
        session = get_session()
        try:
            company = session.query(Company).filter(Company.id == _id).first()
            if not company:
                return None

            return self._company_to_dict(company)
        except Exception as e:
            logger.error(f"Error fetching company {_id}: {e}")
            raise
        finally:
            session.close()

    def get_companies(self) -> list[dict[str, Any]]:
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

    def create_company(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new company."""
        session = get_session()
        try:
            # Create company object
            company = Company(
                name=data["name"],
                website=data.get("website"),
                industry=data.get("industry"),
                size=data.get("size"),
                notes=data.get("notes"),
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

    def update_company(self, _id: int, data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing company."""
        session = get_session()
        try:
            # Get company
            company = session.query(Company).filter(Company.id == _id).first()
            if not company:
                raise ValueError(f"Company with ID {_id} not found")

            # Update fields
            if "name" in data:
                company.name = data["name"]
            if "website" in data:
                company.website = data["website"]
            if "industry" in data:
                company.industry = data["industry"]
            if "size" in data:
                company.size = data["size"]
            if "notes" in data:
                company.notes = data["notes"]

            # Commit changes
            session.commit()
            session.refresh(company)

            return self._company_to_dict(company)
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating company {_id}: {e}")
            raise
        finally:
            session.close()

    def delete_company(self, _id: int) -> bool:
        """Delete a company."""
        session = get_session()
        try:
            company = session.query(Company).filter(Company.id == _id).first()
            if not company:
                return False

            # Check if company has applications
            if company.applications:
                raise ValueError(f"Cannot delete company with ID {_id} because it has associated applications")

            session.delete(company)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting company {_id}: {e}")
            raise
        finally:
            session.close()

    def get_company_types(self) -> list[str]:
        """Get all available company types."""
        return [ct.value for ct in CompanyType]

    def create_relationship(
        self, source_id: int, target_id: int, relationship_type: str, notes: str = None
    ) -> dict[str, Any]:
        """Create a new relationship between companies."""
        session = get_session()
        try:
            # Verify both companies exist
            source = session.query(Company).filter(Company.id == source_id).first()
            target = session.query(Company).filter(Company.id == target_id).first()

            if not source or not target:
                raise ValueError("Source or target company not found")

            relationship = CompanyRelationship(
                source_company_id=source_id,
                target_company_id=target_id,
                relationship_type=relationship_type,
                notes=notes,
            )

            session.add(relationship)
            session.commit()
            session.refresh(relationship)

            return {
                "id": relationship.id,
                "source_company_id": relationship.source_company_id,
                "target_company_id": relationship.target_company_id,
                "relationship_type": relationship.relationship_type,
                "notes": relationship.notes,
            }
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating company relationship: {e}")
            raise
        finally:
            session.close()

    def get_related_companies(self, company_id: int) -> list[dict[str, Any]]:
        """Get companies related to the given company."""
        session = get_session()
        try:
            # Get outgoing relationships
            outgoing = (
                session.query(CompanyRelationship).filter(CompanyRelationship.source_company_id == company_id).all()
            )

            # Get incoming relationships
            incoming = (
                session.query(CompanyRelationship).filter(CompanyRelationship.target_company_id == company_id).all()
            )

            results = []

            # Process outgoing relationships
            for rel in outgoing:
                target = session.query(Company).filter(Company.id == rel.target_company_id).first()
                if target:
                    results.append(
                        {
                            "relationship_id": rel.id,
                            "company_id": target.id,
                            "company_name": target.name,
                            "company_type": target.type,
                            "relationship_type": rel.relationship_type,
                            "direction": "outgoing",
                            "notes": rel.notes,
                        }
                    )

            # Process incoming relationships
            for rel in incoming:
                source = session.query(Company).filter(Company.id == rel.source_company_id).first()
                if source:
                    results.append(
                        {
                            "relationship_id": rel.id,
                            "company_id": source.id,
                            "company_name": source.name,
                            "company_type": source.type,
                            "relationship_type": rel.relationship_type,
                            "direction": "incoming",
                            "notes": rel.notes,
                        }
                    )

            return results
        except Exception as e:
            logger.error(f"Error getting related companies: {e}")
            raise
        finally:
            session.close()

    def _company_to_dict(self, company: Company, include_details: bool = True) -> dict[str, Any]:
        """Convert a Company object to a dictionary."""
        result = {
            "id": company.id,
            "name": company.name,
        }

        if include_details:
            result.update(
                {
                    "website": company.website,
                    "industry": company.industry,
                    "size": company.size,
                    "notes": company.notes,
                }
            )

        return result
