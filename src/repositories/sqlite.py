"""SQLite implementation of database abstraction."""

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

    def _drop_column_with_indexes(self, conn, table: str, col: str) -> None:
        """Drop indexes referencing col, then drop the column itself."""
        idx_rows = conn.execute(
            text(f"SELECT `name` FROM pragma_index_list('{table}') WHERE `origin`='c'")
        ).fetchall()
        for (idx_name,) in idx_rows:
            refs = conn.execute(
                text("SELECT COUNT(*) FROM pragma_index_info(:name) WHERE `name`=:col"),
                {"name": idx_name, "col": col},
            ).scalar()
            if refs:
                conn.execute(text(f'DROP INDEX IF EXISTS "{idx_name}"'))
        conn.execute(text(f"ALTER TABLE {table} DROP COLUMN {col}"))

    def _drop_due_date_column(self) -> None:
        if not self._supports_drop_column():
            return
        with self.engine.connect() as conn:
            due_date_exists = conn.execute(
                text("SELECT COUNT(*) FROM pragma_table_info('word_stats') WHERE name='due_date'")
            ).scalar()
            if not due_date_exists:
                return

            self._drop_column_with_indexes(conn, "word_stats", "due_date")
            conn.commit()

    def _drop_legacy_columns(self) -> None:
        if not self._supports_drop_column():
            return
        with self.engine.connect() as conn:
            existing = {
                row[0]
                for row in conn.execute(
                    text("SELECT name FROM pragma_table_info('word_stats')")
                ).fetchall()
            }
            for col in ("interval_days", "ease_factor"):
                if col in existing:
                    self._drop_column_with_indexes(conn, "word_stats", col)
            conn.commit()

    def _supports_drop_column(self) -> bool:
        """SQLite added ALTER TABLE DROP COLUMN in version 3.35.0."""
        version = self.engine.dialect.server_version_info
        return not isinstance(version, tuple) or version >= (3, 35, 0)

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
