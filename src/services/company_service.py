import logging
from typing import Any

from sqlalchemy.orm import Session

from src.config import CompanyType
from src.db.database import get_session
from src.db.models import Company, CompanyRelationship
from src.services.base_service import BaseService

logger = logging.getLogger(__name__)


class CompanyService(BaseService):
    """Service for company-related operations."""

    model_class = Company
    entity_name = "company"

    def _create_entity_from_dict(self, data: dict[str, Any], session: Session) -> Company:
        """Create a Company object from a dictionary."""
        return Company(
            name=data["name"],
            website=data.get("website"),
            industry=data.get("industry"),
            size=data.get("size"),
            type=data.get("type", CompanyType.DIRECT_EMPLOYER.value),
            notes=data.get("notes"),
        )

    def _update_entity_from_dict(self, entity: Company, data: dict[str, Any], session: Session) -> None:
        """Update a Company object from a dictionary."""
        if "name" in data:
            entity.name = data["name"]
        if "website" in data:
            entity.website = data["website"]
        if "industry" in data:
            entity.industry = data["industry"]
        if "size" in data:
            entity.size = data["size"]
        if "type" in data:
            entity.type = data["type"]
        if "notes" in data:
            entity.notes = data["notes"]

    def _entity_to_dict(self, company: Company, include_details: bool = True) -> dict[str, Any]:
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
                    "type": company.type,
                    "notes": company.notes,
                }
            )

        return result

    def get_company_types(self) -> list[str]:
        """Get all available company types."""
        return [ct.value for ct in CompanyType]

    def create_relationship(
        self, source_id: int, target_id: int, relationship_type: str, notes: str | None = None
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

    def update_relationship(self, relationship_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing company relationship."""
        session = get_session()
        try:
            relationship = session.query(CompanyRelationship).filter(CompanyRelationship.id == relationship_id).first()

            if not relationship:
                raise ValueError(f"Relationship {relationship_id} not found")

            # Update fields
            if "relationship_type" in data:
                relationship.relationship_type = data["relationship_type"]
            if "notes" in data:
                relationship.notes = data["notes"]

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
            logger.error(f"Error updating relationship: {e}")
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

    def get_relationship(self, relationship_id: int) -> dict[str, Any] | None:
        """Get a specific relationship by ID."""
        session = get_session()
        try:
            relationship = session.query(CompanyRelationship).filter(CompanyRelationship.id == relationship_id).first()

            if not relationship:
                return None

            return {
                "id": relationship.id,
                "source_id": relationship.source_company_id,
                "target_id": relationship.target_company_id,
                "relationship_type": relationship.relationship_type,
                "notes": relationship.notes,
            }
        except Exception as e:
            logger.error(f"Error getting relationship {relationship_id}: {e}")
            raise
        finally:
            session.close()
