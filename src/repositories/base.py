"""Database abstraction - DB-agnostic interface."""

from abc import ABC, abstractmethod
from typing import Any


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
