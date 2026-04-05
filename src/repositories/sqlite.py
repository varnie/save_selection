"""SQLite implementation of database abstraction."""

from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from infrastructure.models import Base
from repositories.base import AbstractDatabase as BaseDatabase


class SQLiteDatabase(BaseDatabase):
    """SQLite implementation of the database abstraction."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.ScopedSession = scoped_session(session_factory)
        self._connected = False

    @property
    def session(self) -> Session:
        return self.ScopedSession()

    def connect(self) -> None:
        """Connect to database and create schema."""
        Base.metadata.create_all(self.engine)
        self._connected = True

    def commit(self) -> None:
        """Commit transaction."""
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def rollback(self) -> None:
        """Rollback transaction."""
        self.session.rollback()

    def close(self) -> None:
        """Close connection."""
        self.ScopedSession.remove()
        self._connected = False

    def remove_session(self) -> None:
        """Remove scoped session (for threading)."""
        self.ScopedSession.remove()

    @property
    def in_transaction(self) -> bool:
        """Check if in a transaction."""
        return self.session.in_transaction()

    def execute(self, query: Any) -> Any:
        """Execute a raw query."""
        return self.session.execute(query)

    def flush(self) -> None:
        """Flush pending changes."""
        self.session.flush()
