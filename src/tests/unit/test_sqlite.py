"""Tests for SQLite database implementation."""

from unittest.mock import MagicMock, patch

import pytest

from repositories.sqlite import SQLiteDatabase


class TestSQLiteDatabase:
    """Tests for SQLiteDatabase class."""

    @patch("repositories.sqlite.create_engine")
    @patch("repositories.sqlite.scoped_session")
    @patch("repositories.sqlite.sessionmaker")
    def test_init_creates_engine_with_correct_url(self, mock_sessionmaker, mock_scoped, mock_create_engine):
        """Test that __init__ creates engine with correct SQLite URL."""
        SQLiteDatabase("/tmp/test.db")
        # For absolute paths, SQLite needs sqlite:////path (4 slashes)
        mock_create_engine.assert_called_once_with(
            "sqlite:////tmp/test.db",
            echo=False,
            connect_args={"check_same_thread": False},
        )

    @patch("repositories.sqlite.create_engine")
    @patch("repositories.sqlite.scoped_session")
    @patch("repositories.sqlite.sessionmaker")
    def test_init_creates_engine_with_relative_path(self, mock_sessionmaker, mock_scoped, mock_create_engine):
        """Test that __init__ creates engine with correct URL for relative path."""
        SQLiteDatabase("relative/test.db")
        # For relative paths, SQLite needs sqlite:///path (3 slashes)
        mock_create_engine.assert_called_once_with(
            "sqlite:///relative/test.db",
            echo=False,
            connect_args={"check_same_thread": False},
        )

    @patch("repositories.sqlite.create_engine")
    @patch("repositories.sqlite.scoped_session")
    @patch("repositories.sqlite.sessionmaker")
    def test_init_sets_db_path(self, mock_sessionmaker, mock_scoped, mock_create_engine):
        """Test that __init__ sets db_path attribute."""
        db = SQLiteDatabase("/tmp/test.db")
        assert db.db_path == "/tmp/test.db"

    @patch("repositories.sqlite.create_engine")
    @patch("repositories.sqlite.scoped_session")
    @patch("repositories.sqlite.sessionmaker")
    def test_session_property_returns_scoped_session(self, mock_sessionmaker, mock_scoped, mock_create_engine):
        """Test that session property returns a new scoped session."""
        mock_scoped_instance = MagicMock()
        mock_scoped.return_value = mock_scoped_instance
        mock_scoped_instance.return_value = "session_obj"

        db = SQLiteDatabase("/tmp/test.db")
        session = db.session
        assert session == "session_obj"

    @patch("repositories.sqlite.Base")
    @patch("repositories.sqlite.create_engine")
    @patch("repositories.sqlite.scoped_session")
    @patch("repositories.sqlite.sessionmaker")
    def test_connect_creates_tables(self, mock_sessionmaker, mock_scoped, mock_create_engine, mock_base):
        """Test that connect creates all tables."""
        db = SQLiteDatabase("/tmp/test.db")
        db.connect()
        mock_base.metadata.create_all.assert_called_once_with(mock_create_engine.return_value)

    @patch("repositories.sqlite.create_engine")
    @patch("repositories.sqlite.scoped_session")
    @patch("repositories.sqlite.sessionmaker")
    def test_connect_sets_connected_flag(self, mock_sessionmaker, mock_scoped, mock_create_engine):
        """Test that connect sets _connected to True."""
        db = SQLiteDatabase("/tmp/test.db")
        db.connect()
        assert db._connected is True

    @patch("repositories.sqlite.create_engine")
    @patch("repositories.sqlite.scoped_session")
    @patch("repositories.sqlite.sessionmaker")
    def test_commit_success(self, mock_sessionmaker, mock_scoped, mock_create_engine):
        """Test that commit calls session commit."""
        mock_session = MagicMock()
        mock_scoped_instance = MagicMock()
        mock_scoped_instance.return_value = mock_session
        mock_scoped.return_value = mock_scoped_instance

        db = SQLiteDatabase("/tmp/test.db")
        db.commit()
        mock_session.commit.assert_called_once()

    @patch("repositories.sqlite.create_engine")
    @patch("repositories.sqlite.scoped_session")
    @patch("repositories.sqlite.sessionmaker")
    def test_commit_rollback_on_error(self, mock_sessionmaker, mock_scoped, mock_create_engine):
        """Test that commit rolls back on error."""
        mock_session = MagicMock()
        mock_session.commit.side_effect = Exception("DB error")
        mock_scoped_instance = MagicMock()
        mock_scoped_instance.return_value = mock_session
        mock_scoped.return_value = mock_scoped_instance

        db = SQLiteDatabase("/tmp/test.db")
        with pytest.raises(Exception, match="DB error"):
            db.commit()
        mock_session.rollback.assert_called_once()

    @patch("repositories.sqlite.create_engine")
    @patch("repositories.sqlite.scoped_session")
    @patch("repositories.sqlite.sessionmaker")
    def test_rollback_calls_session_rollback(self, mock_sessionmaker, mock_scoped, mock_create_engine):
        """Test that rollback calls session rollback."""
        mock_session = MagicMock()
        mock_scoped_instance = MagicMock()
        mock_scoped_instance.return_value = mock_session
        mock_scoped.return_value = mock_scoped_instance

        db = SQLiteDatabase("/tmp/test.db")
        db.rollback()
        mock_session.rollback.assert_called_once()

    @patch("repositories.sqlite.create_engine")
    @patch("repositories.sqlite.scoped_session")
    @patch("repositories.sqlite.sessionmaker")
    def test_close_calls_remove_and_sets_flag(self, mock_sessionmaker, mock_scoped, mock_create_engine):
        """Test that close removes scoped session and sets connected to False."""
        mock_scoped_instance = MagicMock()
        mock_scoped.return_value = mock_scoped_instance

        db = SQLiteDatabase("/tmp/test.db")
        db._connected = True
        db.close()
        mock_scoped_instance.remove.assert_called_once()
        assert db._connected is False

    @patch("repositories.sqlite.create_engine")
    @patch("repositories.sqlite.scoped_session")
    @patch("repositories.sqlite.sessionmaker")
    def test_remove_session_calls_scoped_remove(self, mock_sessionmaker, mock_scoped, mock_create_engine):
        """Test that remove_session calls ScopedSession.remove()."""
        mock_scoped_instance = MagicMock()
        mock_scoped.return_value = mock_scoped_instance

        db = SQLiteDatabase("/tmp/test.db")
        db.remove_session()
        mock_scoped_instance.remove.assert_called_once()
