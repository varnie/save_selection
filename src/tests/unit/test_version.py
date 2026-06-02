"""Tests for version module."""

from unittest.mock import patch

from version import get_version


class TestGetVersion:
    """Tests for get_version function."""

    def test_get_version_returns_string(self):
        """Test that get_version returns a string."""
        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_version_reads_version_file(self):
        """Test that get_version reads from VERSION file."""
        with patch("version.VERSION_FILE", "/tmp/test_version"):
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__ = mock_open
                mock_open.return_value.__exit__ = mock_open
                mock_open.return_value.read.return_value = "1.2.3\n"
                version = get_version()
                assert version == "1.2.3"

    def test_get_version_strips_whitespace(self):
        """Test that get_version strips whitespace from version."""
        with patch("version.VERSION_FILE", "/tmp/test_version"):
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__ = mock_open
                mock_open.return_value.__exit__ = mock_open
                mock_open.return_value.read.return_value = "  1.2.3  \n"
                version = get_version()
                assert version == "1.2.3"

    def test_get_version_file_not_found(self):
        """Test that get_version returns 'unknown' when file not found."""
        with patch("version.VERSION_FILE", "/nonexistent/VERSION"):
            version = get_version()
            assert version == "unknown"
