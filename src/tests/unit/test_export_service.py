"""Unit tests for ExportService."""

import os
import pytest


class TestExportService:
    """Tests for ExportService."""

    def test_export_csv_creates_file(self, export_service, temp_csv_file):
        """Test that CSV export creates a file."""
        export_service.export_csv(temp_csv_file)

        assert os.path.exists(temp_csv_file)

    def test_export_csv_contains_headers(self, export_service, word_service, temp_csv_file):
        """Test that CSV contains expected headers."""
        word_service.add_word("test", translation="тест")

        export_service.export_csv(temp_csv_file)

        with open(temp_csv_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "source" in content.lower()
        assert "target" in content.lower()

    def test_export_csv_contains_data(self, export_service, word_service, temp_csv_file):
        """Test that CSV contains word data."""
        word_service.add_word("hello", translation="привет")

        export_service.export_csv(temp_csv_file)

        with open(temp_csv_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "hello" in content
        assert "привет" in content
