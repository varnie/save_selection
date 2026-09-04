"""WOTD service - handles Word of the Day functionality."""

import logging

from application.service_interfaces import (
    AbstractSettingsService,
    AbstractTranslationService,
    AbstractWordManagementService,
    AbstractWOTDService,
    WordSource,
)
from config import DEFAULT_WOTD_LEVEL, WOTD_ENABLED_KEY, WOTD_LEVEL_KEY
from domain.entities import Word
from domain.exceptions import TranslationError
from domain.repositories import AbstractWOTDRepository

logger = logging.getLogger(__name__)


class WOTDService(AbstractWOTDService):
    """Service for Word of the Day functionality."""

    def __init__(
        self,
        settings_service: AbstractSettingsService,
        wotd_repo: AbstractWOTDRepository,
        word_service: AbstractWordManagementService,
        translation_service: AbstractTranslationService,
        word_source: WordSource,
    ) -> None:
        self.settings_service = settings_service
        self.wotd_repo = wotd_repo
        self.word_service = word_service
        self.translation_service = translation_service
        self.word_source = word_source

    def is_wotd_enabled(self) -> bool:
        """Check if Word of the Day is enabled."""
        enabled = self.settings_service.get_setting(WOTD_ENABLED_KEY, "false")
        return enabled == "true"

    def get_wotd_level(self) -> str:
        """Get the configured WOTD level."""
        return self.settings_service.get_setting(WOTD_LEVEL_KEY, DEFAULT_WOTD_LEVEL) or DEFAULT_WOTD_LEVEL

    def get_word_of_the_day(self) -> Word | None:
        """Get Word of the Day - adds to vocab and returns Word entity."""
        if not self.is_wotd_enabled():
            return None

        if self.wotd_repo.get_today():
            return None

        level = self.get_wotd_level()
        word_data = self.word_source.get_word(level)
        if not word_data:
            return None

        word = word_data["word"]
        word_level = word_data["level"]

        provider_name = self.settings_service.get_translation_provider()
        source_lang = self.settings_service.get_source_lang()
        target_lang = self.settings_service.get_target_lang()

        try:
            translation = self.translation_service.translate(
                word, target_lang, source_lang, provider_name
            )
        except TranslationError:
            logger.warning("WOTD translation failed for '%s', skipping", word)
            return None

        if not translation:
            return None

        self.wotd_repo.mark_shown(word, word_level)

        word_entity, _ = self.save_wotd_to_vocab(word, translation)
        return word_entity

    def save_wotd_to_vocab(
        self, word: str, translation: str | None = None
    ) -> tuple[Word | None, bool]:
        """Save WOTD word to user's vocabulary."""
        try:
            result = self.word_service.add_word(
                word, translation, auto_translate=(translation is None)
            )
            return result, True
        except Exception as e:
            logger.exception("Failed to save WOTD to vocab: %s", e)
            return None, False
