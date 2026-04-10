"""Database manager - handles database lifecycle."""

from repositories.base import AbstractDatabase


class DatabaseManager:
    """Manages database lifecycle - cleanup responsibilities only."""

    def __init__(self, db: AbstractDatabase) -> None:
        self._db = db

    def close(self) -> None:
        """Close database connection."""
        self._db.close()

    def remove_session(self) -> None:
        """Remove scoped session (for threading)."""
        self._db.remove_session()
