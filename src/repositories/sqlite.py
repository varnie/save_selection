"""SQLite implementation of database abstraction."""

from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from infrastructure.models import Base
from repositories.base import AbstractDatabase as BaseDatabase


class SQLiteDatabase(BaseDatabase):
    """SQLite implementation of the database abstraction."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        # SQLite URL: sqlite:///path (relative) or sqlite:////path (absolute)
        url = f"sqlite:///{db_path}"
        self.engine = create_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False},
        )
        session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.ScopedSession = scoped_session(session_factory)
        self._connected = False

    @property
    def session(self) -> Session:
        return self.ScopedSession()

    def _create_index(self, name: str, table: str, *columns: str) -> None:
        cols = ", ".join(columns)
        with self.engine.connect() as conn:
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({cols})"))
            conn.commit()

    def connect(self) -> None:
        """Connect to database and create schema."""
        Base.metadata.create_all(self.engine)
        self._drop_due_date_column()
        self._drop_legacy_columns()
        self._create_index("idx_history_reviewed_at", "history", "reviewed_at")
        self._create_index("idx_history_word_id", "history", "word_id")
        self._create_index("idx_translation_word_id", "translations", "word_id")
        self._create_index("idx_translation_language_id", "translations", "language_id")
        self._create_index("idx_translation_word_lang", "translations", "word_id", "language_id")
        self._create_index("idx_word_stats_last_reviewed", "word_stats", "last_reviewed")
        self._connected = True

    def _drop_due_date_column(self) -> None:
        with self.engine.connect() as conn:
            due_date_exists = conn.execute(
                text("SELECT COUNT(*) FROM pragma_table_info('word_stats') WHERE name='due_date'")
            ).scalar()
            if not due_date_exists:
                return

            idx_rows = conn.execute(
                text("SELECT `name` FROM pragma_index_list('word_stats') WHERE `origin`='c'")
            ).fetchall()
            for (idx_name,) in idx_rows:
                refs_due = conn.execute(
                    text(
                        "SELECT COUNT(*) FROM pragma_index_info(:name) WHERE `name`='due_date'"
                    ),
                    {"name": idx_name},
                ).scalar()
                if refs_due:
                    conn.execute(text(f"DROP INDEX IF EXISTS \"{idx_name}\""))
            conn.execute(text("ALTER TABLE word_stats DROP COLUMN due_date"))
            conn.commit()

    def _drop_legacy_columns(self) -> None:
        with self.engine.connect() as conn:
            existing = {
                row[0]
                for row in conn.execute(
                    text("SELECT name FROM pragma_table_info('word_stats')")
                ).fetchall()
            }
            for col in ("interval_days", "ease_factor"):
                if col in existing:
                    idx_rows = conn.execute(
                        text("SELECT `name` FROM pragma_index_list('word_stats') WHERE `origin`='c'")
                    ).fetchall()
                    for (idx_name,) in idx_rows:
                        refs = conn.execute(
                            text(
                                "SELECT COUNT(*) FROM pragma_index_info(:name) WHERE `name`=:col"
                            ),
                            {"name": idx_name, "col": col},
                        ).scalar()
                        if refs:
                            conn.execute(text(f"DROP INDEX IF EXISTS \"{idx_name}\""))
                    conn.execute(text(f"ALTER TABLE word_stats DROP COLUMN {col}"))
            conn.commit()

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
