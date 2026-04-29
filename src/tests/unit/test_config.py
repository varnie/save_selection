"""Tests for config module."""

import json
import os
from unittest.mock import mock_open, patch

import pytest

from config import DEFAULT_SETTINGS, read_config, write_config


class TestReadConfig:
    """Tests for read_config function."""

    def test_read_config_file_not_exists(self):
        """Test that read_config returns empty dict when file doesn't exist."""
        with patch("config.os.path.exists", return_value=False):
            result = read_config("/nonexistent/config.json")
            assert result == {}

    def test_read_config_valid_json(self):
        """Test that read_config reads valid JSON."""
        test_data = {"key": "value", "number": 123}
        with patch("config.os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(test_data))):
                result = read_config("/tmp/config.json")
                assert result == test_data

    def test_read_config_invalid_json(self):
        """Test that read_config returns empty dict on invalid JSON."""
        with patch("config.os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="invalid json")):
                result = read_config("/tmp/config.json")
                assert result == {}

    def test_read_config_exception_handling(self):
        """Test that read_config handles exceptions gracefully."""
        with patch("config.os.path.exists", return_value=True):
            with patch("builtins.open", side_effect=PermissionError("No permission")):
                result = read_config("/tmp/config.json")
                assert result == {}


class TestWriteConfig:
    """Tests for write_config function."""

    def test_write_config_success(self):
        """Test that write_config writes JSON successfully."""
        test_data = {"key": "value"}
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            with patch("config.os.path.dirname", return_value="/tmp"):
                with patch("config.os.makedirs"):
                    result = write_config("/tmp/config.json", test_data)
                    assert result is True
                    mock_file().write.assert_called()

    def test_write_config_creates_directory(self):
        """Test that write_config creates directory if needed."""
        test_data = {"key": "value"}
        with patch("builtins.open", mock_open()):
            with patch("config.os.path.dirname", return_value="/tmp/subdir"):
                with patch("config.os.makedirs") as mock_makedirs:
                    write_config("/tmp/subdir/config.json", test_data)
                    mock_makedirs.assert_called_once_with("/tmp/subdir", exist_ok=True)

    def test_write_config_no_directory(self):
        """Test write_config when config_file has no directory."""
        test_data = {"key": "value"}
        with patch("builtins.open", mock_open()):
            with patch("config.os.path.dirname", return_value=""):
                with patch("config.os.makedirs") as mock_makedirs:
                    result = write_config("config.json", test_data)
                    assert result is True
                    mock_makedirs.assert_not_called()

    def test_write_config_exception_handling(self):
        """Test that write_config handles exceptions gracefully."""
        test_data = {"key": "value"}
        with patch("builtins.open", side_effect=PermissionError("No permission")):
            result = write_config("/tmp/config.json", test_data)
            assert result is False


class TestDefaultSettings:
    """Tests for DEFAULT_SETTINGS."""

    def test_default_settings_exists(self):
        """Test that DEFAULT_SETTINGS is defined."""
        assert DEFAULT_SETTINGS is not None

    def test_default_settings_has_review_interval(self):
        """Test that DEFAULT_SETTINGS has review_interval."""
        assert "review_interval" in DEFAULT_SETTINGS
        assert DEFAULT_SETTINGS["review_interval"] == "3600"

    def test_default_settings_has_source_lang(self):
        """Test that DEFAULT_SETTINGS has source_lang."""
        assert "source_lang" in DEFAULT_SETTINGS
        assert DEFAULT_SETTINGS["source_lang"] == "en"

    def test_default_settings_has_target_lang(self):
        """Test that DEFAULT_SETTINGS has target_lang."""
        assert "target_lang" in DEFAULT_SETTINGS
        assert DEFAULT_SETTINGS["target_lang"] == "ru"

    def test_default_settings_has_translation_provider(self):
        """Test that DEFAULT_SETTINGS has translation_provider."""
        assert "translation_provider" in DEFAULT_SETTINGS
        assert DEFAULT_SETTINGS["translation_provider"] == "google_direct"
