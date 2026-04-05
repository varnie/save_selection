"""Database abstraction - DB-agnostic interface."""

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class AbstractDatabase(ABC):
    """Abstract database interface."""

    @abstractmethod
    def __init__(self, **kwargs: object) -> None:
        """Initialize database with optional configuration."""
        pass

    @abstractmethod
    def connect(self) -> None:
        """Connect to database."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    def commit(self) -> None:
        """Commit transaction."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Rollback transaction."""
        pass

    @property
    @abstractmethod
    def session(self) -> Any:
        """Get database session."""
        pass

    @abstractmethod
    def remove_session(self) -> None:
        """Remove scoped session (for threading)."""
        pass


class DatabaseFactory:
    """Factory for creating database instances."""

    _implementations: ClassVar[dict[str, type[AbstractDatabase]]] = {}

    @classmethod
    def register(cls, name: str, db_class: type[AbstractDatabase]) -> None:
        """Register a database implementation."""
        cls._implementations[name] = db_class

    @classmethod
    def create(cls, name: str, **kwargs) -> AbstractDatabase:
        """Create a database instance by name."""
        if name not in cls._implementations:
            raise ValueError(
                f"Unknown database: {name}. Available: {list(cls._implementations.keys())}"
            )
        return cls._implementations[name](**kwargs)
