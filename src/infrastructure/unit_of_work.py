"""Unit of Work pattern for transactional operations."""

from typing import Any, Optional

from repositories.base import AbstractDatabase


class UnitOfWork:
    """Unit of Work for managing database transactions."""

    def __init__(self, database: AbstractDatabase) -> None:
        self._db = database
        self._committed = False

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Optional[Any],
    ) -> None:
        if exc_type is not None or not self._committed:
            self._db.rollback()

    def commit(self) -> None:
        """Commit the current transaction."""
        self._db.commit()
        self._committed = True

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self._db.rollback()
        self._committed = True

    @property
    def session(self) -> Any:
        """Get the current database session."""
        return self._db.session
