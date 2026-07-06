"""Word management service - handles word CRUD operations."""

import logging
from datetime import datetime, timezone

from application.service_interfaces import (
    AbstractTranslationService,
    AbstractWordManagementService,
)
from domain.entities import Word
from domain.repositories import (
    AbstractLanguageRepository,
    AbstractSettingsRepository,
    AbstractWordRepository,
)
from infrastructure.translation import TranslationError

logger = logging.getLogger(__name__)


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
        return self._get_setting("target_lang", "ru")

    def _get_source_lang(self) -> str:
        return self._get_setting("source_lang", "en")

    def _get_setting(self, key: str, default: str) -> str:
        setting = self.settings_repo.get(key)
        return setting.value if setting else default

    def add_word(
        self, phrase: str, translation: str | None = None, auto_translate: bool = False
    ) -> Word:
        """Add a new word or add translation to existing word."""
        if not phrase or not phrase.strip():
            raise ValueError("Phrase cannot be empty")

        phrase = phrase.strip().lower()

        if len(phrase) < self.MIN_PHRASE_LENGTH or len(phrase) > self.MAX_PHRASE_LENGTH:
            raise ValueError(
                f"Phrase length must be {self.MIN_PHRASE_LENGTH}-{self.MAX_PHRASE_LENGTH}"
            )

        existing = self.word_repo.get_by_phrase(phrase)
        if existing:
            word_id = existing.id
        else:
            new_word = self.word_repo.add(phrase)
            word_id = new_word.id

        if translation or auto_translate:
            target_lang = self._get_target_lang()
            if translation:
                self.word_repo.add_translation(word_id, translation, target_lang)
            elif auto_translate:
                provider_name = self._get_setting("translation_provider", "google_direct")
                source_lang = self._get_source_lang()
                try:
                    trans = self.translation_service.translate(
                        phrase, target_lang, source_lang, provider_name
                    )
                except TranslationError:
                    logger.warning("Auto-translate failed for '%s', skipping", phrase)
                    trans = None
                if trans:
                    self.word_repo.add_translation(word_id, trans, target_lang)

        result = self.word_repo.get_by_phrase(phrase)
        if result is None:
            msg = f"Word not found after add: {phrase}"
            raise RuntimeError(msg)
        return result

    def get_words(
        self,
        search: str | None = None,
        target_lang: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Word]:
        """Get all words with optional search and language filter."""
        return self.word_repo.get_all(search, target_lang, limit, offset)

    def get_words_added_today(self) -> list[Word]:
        """Get words added today."""
        target_lang = self._get_target_lang()
        now = datetime.now(timezone.utc)
        today_start = int(datetime(now.year, now.month, now.day).timestamp())
        return self.word_repo.get_all(target_lang=target_lang, since=today_start)

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

    def update_word(self, word_id: int, phrase: str, translation: str | None = None) -> None:
        """Update word phrase and optionally translation."""
        if not phrase or not phrase.strip():
            raise ValueError("Phrase cannot be empty")

        phrase = phrase.strip().lower()

        if len(phrase) < self.MIN_PHRASE_LENGTH or len(phrase) > self.MAX_PHRASE_LENGTH:
            raise ValueError(
                f"Phrase length must be {self.MIN_PHRASE_LENGTH}-{self.MAX_PHRASE_LENGTH}"
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
