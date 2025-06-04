from typing import Any, Generic, TypeVar

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.db.models import Base
from src.utils.decorators import db_operation
from src.utils.logging import get_logger

# Define type for models
ModelType = TypeVar("ModelType", bound=Base)

# Get module logger
logger = get_logger(__name__)


class BaseService(Generic[ModelType]):
    """
    Abstract base class for service classes.

    Provides common CRUD operations and utility methods for derived service classes.
    """

    # The model this service manages (overridden in subclasses)
    model_class: type[ModelType] | None = None

    # Name of this entity type (for error messages)
    entity_name: str = "record"

    def __init__(self) -> None:
        """Initialize the service with a logger specific to the subclass."""
        self.logger = get_logger(self.__class__.__name__)

    @db_operation
    def get(self, _id: int, session: Session) -> dict[str, Any] | None:
        """
        Retrieve an entity by ID.

        Args:
            _id: ID of the entity to retrieve.
            session: SQLAlchemy session.
        Returns:
            Dictionary representation of the entity, or None if not found.
        """
        if not self.model_class:
            raise NotImplementedError("model_class must be defined in the subclass")

        try:
            self.logger.debug(f"Fetching {self.entity_name} with ID {_id}")
            entity = session.query(self.model_class).filter(self.model_class.id == _id).first()

            if not entity:
                self.logger.info(f"{self.entity_name.capitalize()} with ID {_id} not found")
                return None

            return self._entity_to_dict(entity)
        except Exception as e:
            self.logger.error(f"Error fetching {self.entity_name} {_id}: {e}", exc_info=True)
            raise

    @db_operation
    def get_all(self, session: Session, **kwargs: Any) -> list[dict[str, Any]]:
        """Get all entities with optional filtering."""
        if not self.model_class:
            raise NotImplementedError("model_class must be defined in the subclass")

        try:
            # Build query with filtering
            sort_by = kwargs.get("sort_by")
            sort_desc = kwargs.get("sort_desc", False)
            offset = kwargs.get("offset", 0)
            limit = kwargs.get("limit")

            self.logger.debug(
                f"Getting {self.entity_name}s with sort_by={sort_by}, "
                f"sort_desc={sort_desc}, offset={offset}, limit={limit}"
            )

            query = session.query(self.model_class)

            # Apply sorting
            if sort_by and hasattr(self.model_class, sort_by):
                if sort_desc:
                    query = query.order_by(desc(getattr(self.model_class, sort_by)))
                else:
                    query = query.order_by(getattr(self.model_class, sort_by))

            # Apply offset/limit if provided
            if offset:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            entities = query.all()
            self.logger.debug(f"Found {len(entities)} {self.entity_name}(s)")

            return [self._entity_to_dict(entity, include_details=True) for entity in entities]

        except Exception as e:
            self.logger.error(f"Error fetching {self.entity_name}s: {e}", exc_info=True)
            raise

    @db_operation
    def create(self, data: dict[str, Any], session: Session) -> dict[str, Any]:
        """
        Create a new entity from a dictionary of data.

        Args:
            data: Dictionary of entity attributes.
            session: SQLAlchemy session.
        Returns:
            Dictionary representation of the created entity.
        """
        if not self.model_class:
            raise NotImplementedError("model_class must be defined in the subclass")

        try:
            self.logger.info(f"Creating new {self.entity_name}")
            self.logger.debug(f"Creation data: {data}")

            # Create entity object - implementation varies by entity type
            entity = self._create_entity_from_dict(data, session)

            # Add to session and commit
            session.add(entity)
            session.commit()
            session.refresh(entity)

            self.logger.info(f"{self.entity_name.capitalize()} created with ID {entity.id}")

            return self._entity_to_dict(entity)
        except Exception as e:
            self.logger.error(f"Error creating {self.entity_name}: {e}", exc_info=True)
            raise

    @db_operation
    def update(self, _id: int, data: dict[str, Any], session: Session) -> dict[str, Any]:
        """
        Update an existing entity by ID with new data.

        Args:
            _id: ID of the entity to update.
            data: Dictionary of updated attributes.
            session: SQLAlchemy session.
        Returns:
            Dictionary representation of the updated entity.
        """
        if not self.model_class:
            raise NotImplementedError("model_class must be defined in the subclass")

        try:
            # Get entity
            self.logger.info(f"Updating {self.entity_name} with ID {_id}")
            self.logger.debug(f"Update data: {data}")

            entity = session.query(self.model_class).filter(self.model_class.id == _id).first()
            if not entity:
                error_msg = f"{self.entity_name.capitalize()} with ID {_id} not found"
                self.logger.warning(error_msg)
                raise ValueError(error_msg)

            # Update fields - implementation varies by entity type
            self._update_entity_from_dict(entity, data, session)

            # Commit changes
            session.commit()
            session.refresh(entity)

            self.logger.info(f"{self.entity_name.capitalize()} {_id} updated successfully")
            return self._entity_to_dict(entity)
        except Exception as e:
            self.logger.error(f"Error updating {self.entity_name} {_id}: {e}", exc_info=True)
            raise

    @db_operation
    def delete(self, _id: int, session: Session) -> bool:
        """
        Delete an entity by ID.

        Args:
            _id: ID of the entity to delete.
            session: SQLAlchemy session.
        """
        if not self.model_class:
            raise NotImplementedError("model_class must be defined in the subclass")

        try:
            self.logger.info(f"Deleting {self.entity_name} with ID {_id}")

            entity = session.query(self.model_class).filter(self.model_class.id == _id).first()
            if not entity:
                self.logger.warning(f"{self.entity_name.capitalize()} with ID {_id} not found for deletion")
                return False

            # Additional deletion logic can be implemented in subclasses
            session.delete(entity)
            session.commit()

            self.logger.info(f"{self.entity_name.capitalize()} {_id} deleted successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting {self.entity_name} {_id}: {e}", exc_info=True)
            raise

    def _create_entity_from_dict(self, data: dict[str, Any], session: Session) -> ModelType:
        """
        Abstract method to create an entity from a dictionary.

        Args:
            data: Dictionary of entity attributes.
            session: SQLAlchemy session.
        Returns:
            Entity instance.
        """
        raise NotImplementedError("Subclasses must implement _create_entity_from_dict")

    def _update_entity_from_dict(self, entity: ModelType, data: dict[str, Any], session: Session) -> None:
        """
        Abstract method to update an entity from a dictionary.

        Args:
            entity: Entity instance to update.
            data: Dictionary of updated attributes.
            session: SQLAlchemy session.
        """
        raise NotImplementedError("Subclasses must implement _update_entity_from_dict")

    def _entity_to_dict(self, entity: ModelType, include_details: bool = True) -> dict[str, Any]:
        """
        Abstract method to convert an entity to a dictionary.

        Args:
            entity: Entity instance.
            include_details: Whether to include all details.
        Returns:
            Dictionary representation of the entity.
        """
        raise NotImplementedError("Subclasses must implement _entity_to_dict")
