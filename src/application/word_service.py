#!/usr/bin/env python3
"""Word management service - handles word CRUD operations."""

from domain.entities import Word
from domain.repositories import (
    AbstractWordRepository,
    AbstractLanguageRepository,
    AbstractSettingsRepository,
)
from application.service_interfaces import (
    AbstractTranslationService,
    AbstractWordManagementService,
)


class WordManagementService(AbstractWordManagementService):
    """Service for word CRUD operations."""

    MIN_PHRASE_LENGTH = 1
    MAX_PHRASE_LENGTH = 200

    def __init__(
        self,
        word_repo: AbstractWordRepository,
        language_repo: AbstractLanguageRepository,
        settings_repo: AbstractSettingsRepository,
        translation_service: AbstractTranslationService,
    ) -> None:
        self.word_repo = word_repo
        self.language_repo = language_repo
        self.settings_repo = settings_repo
        self.translation_service = translation_service

    def _get_target_lang(self) -> str:
        return (
            self.settings_repo.get("target_lang").value
            if self.settings_repo.get("target_lang")
            else "ru"
        )

    def _get_source_lang(self) -> str:
        return (
            self.settings_repo.get("source_lang").value
            if self.settings_repo.get("source_lang")
            else "en"
        )

    def _get_translation_provider(self) -> str:
        return (
            self.settings_repo.get("translation_provider").value
            if self.settings_repo.get("translation_provider")
            else "google_direct"
        )

    def add_word(
        self, phrase: str, translation: str | None = None, auto_translate: bool = False
    ) -> Word:
        """Add a new word or add translation to existing word."""
        if not phrase or not phrase.strip():
            raise ValueError("Phrase cannot be empty")

        phrase = phrase.strip().lower()

        if len(phrase) < self.MIN_PHRASE_LENGTH or len(phrase) > self.MAX_PHRASE_LENGTH:
            raise ValueError(
                f"Phrase length must be between {self.MIN_PHRASE_LENGTH} and {self.MAX_PHRASE_LENGTH}"
            )

        existing = self.word_repo.get_by_phrase(phrase)
        word_id = existing.id if existing else self.word_repo.add(phrase).id

        if translation or auto_translate:
            target_lang = self._get_target_lang()
            if translation:
                self.word_repo.add_translation(word_id, translation, target_lang)
            elif auto_translate:
                provider_name = self._get_translation_provider()
                source_lang = self._get_source_lang()
                trans = self.translation_service.translate(
                    phrase, target_lang, source_lang, provider_name
                )
                if trans:
                    self.word_repo.add_translation(word_id, trans, target_lang)

        return self.word_repo.get_by_phrase(phrase)

    def get_words(
        self, search: str | None = None, target_lang: str | None = None
    ) -> list[Word]:
        """Get all words with optional search and language filter."""
        return self.word_repo.get_all(search, target_lang)

    def get_word(self, phrase: str) -> Word | None:
        """Get word by phrase."""
        return self.word_repo.get_by_phrase(phrase)

    def get_translation(self, word_id: int) -> str | None:
        """Get translation for a word."""
        target_lang = self._get_target_lang()
        translation = self.word_repo.get_translation(word_id, target_lang)
        return translation.translation if translation else None

    def get_translation_with_lang(self, word_id: int) -> tuple[str | None, str | None]:
        """Get translation and its language code."""
        target_lang = self._get_target_lang()
        translation = self.word_repo.get_translation(word_id, target_lang)
        return (translation.translation if translation else None), target_lang

    def get_language_abbreviation(self, lang_code: str) -> str:
        """Get language abbreviation for a code."""
        lang = self.language_repo.get_by_code(lang_code)
        return lang.abbreviation if lang else lang_code.upper()

    def update_word(
        self, word_id: int, phrase: str, translation: str | None = None
    ) -> None:
        """Update word phrase and optionally translation."""
        if not phrase or not phrase.strip():
            raise ValueError("Phrase cannot be empty")

        phrase = phrase.strip().lower()

        if len(phrase) < self.MIN_PHRASE_LENGTH or len(phrase) > self.MAX_PHRASE_LENGTH:
            raise ValueError(
                f"Phrase length must be between {self.MIN_PHRASE_LENGTH} and {self.MAX_PHRASE_LENGTH}"
            )

        self.word_repo.update_word(word_id, phrase)
        if translation:
            target_lang = self._get_target_lang()
            self.word_repo.add_translation(word_id, translation, target_lang)

    def delete_word(self, phrase: str) -> None:
        """Delete a word."""
        self.word_repo.delete(phrase)

    def delete_word_by_id(self, word_id: int) -> None:
        """Delete a word by ID."""
        self.word_repo.delete_by_id(word_id)

    def delete_translation(self, word_id: int, target_lang: str) -> None:
        """Delete only translation for specific language, not the word."""
        self.word_repo.delete_translation(word_id, target_lang)

    def export_csv(self, filepath: str) -> None:
        """Export words to CSV."""
        import csv

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
