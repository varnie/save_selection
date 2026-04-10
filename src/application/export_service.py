"""Export service - handles all export operations."""

import csv

from application.service_interfaces import AbstractExportService
from domain.repositories import AbstractWordRepository


class ExportService(AbstractExportService):
    """Service for exporting words to various formats."""

    def __init__(self, word_repo: AbstractWordRepository) -> None:
        self.word_repo = word_repo

    def export_csv(self, filepath: str) -> None:
        """Export all words to CSV file."""
        words = self.word_repo.get_all()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["source", "target", "source language", "target language"])
            for word in words:
                writer.writerow(
                    [
                        word.phrase,
                        word.translation,
                        "en",
                        word.language_code,
                    ]
                )
