#!/usr/bin/env python3
"""WOTD service - handles Word of the Day functionality."""

from typing import Optional

from domain.entities import Word
from domain.repositories import AbstractSettingsRepository, AbstractWOTDRepository
from domain.services import AbstractTranslationService, AbstractWordManagementService, AbstractWOTDService
from wotd import get_word_source, WordSourceType


class WOTDService(AbstractWOTDService):
    """Service for Word of the Day functionality."""

    def __init__(
        self,
        settings_repo: AbstractSettingsRepository,
        wotd_repo: AbstractWOTDRepository,
        word_service: AbstractWordManagementService,
        translation_service: AbstractTranslationService,
    ) -> None:
        self.settings_repo = settings_repo
        self.wotd_repo = wotd_repo
        self.word_service = word_service
        self.translation_service = translation_service

    def _get_setting(self, key: str, default: str) -> str:
        setting = self.settings_repo.get(key)
        return setting.value if setting else default

    def is_wotd_enabled(self) -> bool:
        """Check if Word of the Day is enabled."""
        enabled = self._get_setting("wotd_enabled", "false")
        return enabled == "true"

    def get_wotd_level(self) -> str:
        """Get the configured WOTD level."""
        return self._get_setting("wotd_level", "B2")

    def get_word_of_the_day(self) -> Optional[Word]:
        """Get Word of the Day - adds to vocab and returns Word entity."""
        if not self.is_wotd_enabled():
            return None

        if self.wotd_repo.get_today():
            return None

        level = self.get_wotd_level()
        source = get_word_source(WordSourceType.LOCAL)
        
        word_data = source.get_word(level)
        if not word_data:
            return None

        word = word_data["word"]
        word_level = word_data["level"]

        provider_name = self._get_setting("translation_provider", "google_direct")
        source_lang = self._get_setting("source_lang", "en")
        target_lang = self._get_setting("target_lang", "ru")

        translation = self.translation_service.translate(word, target_lang, source_lang, provider_name)
        
        if not translation:
            return None

        self.wotd_repo.mark_shown(word, word_level)

        word_entity, success = self.save_wotd_to_vocab(word, translation)
        return word_entity

    def save_wotd_to_vocab(self, word: str, translation: str = None) -> tuple[Optional[Word], bool]:
        """Save WOTD word to user's vocabulary."""
        try:
            result = self.word_service.add_word(word, translation, auto_translate=(translation is None))
            return result, True
        except Exception as e:
            print(f"Failed to save WOTD to vocab: {e}")
            return None, False
