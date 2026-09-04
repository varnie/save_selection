"""Export service - handles all export operations."""

import csv

from application.service_interfaces import AbstractExportService, AbstractSettingsService
from domain.repositories import AbstractWordRepository


class ExportService(AbstractExportService):
    """Service for exporting words to various formats."""

    def __init__(
        self,
        word_repo: AbstractWordRepository,
        settings_service: AbstractSettingsService,
    ) -> None:
        self.word_repo = word_repo
        self.settings_service = settings_service

    def export_csv(self, filepath: str) -> None:
        """Export all words to CSV file."""
        words = self.word_repo.get_all()
        source_lang = self.settings_service.get_source_lang()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["source", "target", "source language", "target language"])
            for word in words:
                writer.writerow(
                    [
                        word.phrase,
                        word.translation,
                        source_lang,
                        word.language_code,
                    ]
                )
