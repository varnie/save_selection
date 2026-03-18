#!/usr/bin/env python3
"""Vocabulary service - delegates to specialized services."""

from application.review_service import ReviewService
from application.settings_service import SettingsService
from application.word_service import WordManagementService
from application.wotd_service import WOTDService
from constants import TEMP_PHRASE_FILE
from domain.entities import Word, Language
from domain.repositories import (
    AbstractWordRepository, AbstractStatsRepository, AbstractSettingsRepository,
    AbstractLanguageRepository, AbstractWOTDRepository,
)
from domain.services import (
    AbstractTranslationService, )
from infrastructure.translation import TranslationServiceImpl
from repositories import AbstractDatabase


class VocabService:
    """Vocabulary service - delegates to specialized services.
    
    All dependencies are injected via constructor (dependency injection).
    Use create_vocab_service() factory for convenient instantiation.
    """

    def __init__(
        self,
        db: AbstractDatabase,
        word_repo: AbstractWordRepository,
        stats_repo: AbstractStatsRepository,
        settings_repo: AbstractSettingsRepository,
        language_repo: AbstractLanguageRepository,
        wotd_repo: AbstractWOTDRepository,
        translation_service: AbstractTranslationService,
    ) -> None:
        self.db = db
        self.word_repo = word_repo
        self.stats_repo = stats_repo
        self.settings_repo = settings_repo
        self.language_repo = language_repo
        self.wotd_repo = wotd_repo
        self.translation_service = translation_service

        self.language_repo.init_defaults()

        self.word_service = WordManagementService(
            self.word_repo, self.language_repo, self.settings_repo, self.translation_service
        )
        self.review_service = ReviewService(
            self.word_repo, self.stats_repo, self.settings_repo
        )
        self.settings_service = SettingsService(self.settings_repo)
        self.wotd_service = WOTDService(
            self.settings_repo, self.wotd_repo, self.word_service, self.translation_service
        )

    def get_settings(self) -> dict:
        return self.settings_service.get_settings()

    def get_languages(self) -> list[Language]:
        return self.language_repo.get_all()

    def save_settings(self, settings: dict) -> None:
        return self.settings_service.save_settings(settings)

    def set_setting(self, key: str, value: str) -> None:
        return self.settings_service.set_setting(key, value)

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        return self.settings_service.get_setting(key, default)

    def add_word(self, phrase: str, translation: str | None = None, auto_translate: bool = False) -> Word:
        return self.word_service.add_word(phrase, translation, auto_translate)

    def get_words(self, search: str | None = None, target_lang: str | None = None) -> list[Word]:
        return self.word_service.get_words(search, target_lang)

    def get_translation(self, word_id: int) -> str | None:
        return self.word_service.get_translation(word_id)

    def get_translation_with_lang(self, word_id: int) -> tuple[str | None, str | None]:
        return self.word_service.get_translation_with_lang(word_id)

    def get_language_abbreviation(self, lang_code: str) -> str:
        return self.word_service.get_language_abbreviation(lang_code)

    def update_word(self, word_id: int, phrase: str, translation: str | None = None) -> None:
        return self.word_service.update_word(word_id, phrase, translation)

    def delete_word(self, phrase: str) -> None:
        return self.word_service.delete_word(phrase)

    def delete_word_by_id(self, word_id: int) -> None:
        return self.word_service.delete_word_by_id(word_id)

    def delete_translation(self, word_id: int, target_lang: str) -> None:
        return self.word_service.delete_translation(word_id, target_lang)

    def export_csv(self, filepath: str) -> None:
        return self.word_service.export_csv(filepath)

    def get_next_word(self) -> Word | None:
        return self.review_service.get_next_word()

    def review_word(self, word_id: int, quality: int = 3) -> None:
        return self.review_service.review_word(word_id, quality)

    def skip_word(self, word_id: int) -> None:
        return self.review_service.skip_word(word_id)

    def get_stats(self) -> dict:
        return self.review_service.get_stats()

    def get_language_counts(self) -> dict:
        return self.review_service.get_language_counts()

    def format_interval(self, interval: int) -> str:
        return self.review_service.format_interval(interval)

    def get_next_word_notification(self) -> str | None:
        word = self.get_next_word()
        if not word:
            return None
        
        phrase = word.phrase
        interval = word.interval_days
        
        translation, trans_lang = self.get_translation_with_lang(word.id)
        
        interval_str = self.format_interval(interval)
        abbrev = self.get_language_abbreviation(trans_lang) if trans_lang else "—"
        
        body = f"<b>{phrase}</b> [{interval_str}]"
        if translation:
            body += f"\n→ {translation} [{abbrev}]"

        with open(TEMP_PHRASE_FILE, "w") as f:
            f.write(phrase)
        
        self.skip_word(word.id)
        
        return body

    def is_wotd_enabled(self) -> bool:
        return self.wotd_service.is_wotd_enabled()

    def get_wotd_level(self) -> str:
        return self.wotd_service.get_wotd_level()

    def get_word_of_the_day(self) -> Word | None:
        return self.wotd_service.get_word_of_the_day()

    def save_wotd_to_vocab(self, word: str, translation: str | None = None) -> tuple[Word | None, bool]:
        return self.wotd_service.save_wotd_to_vocab(word, translation)

    def test_translation_api(self) -> bool:
        try:
            provider = TranslationServiceImpl()
            source_lang = self.get_setting("source_lang", "en")
            target_lang = self.get_setting("target_lang", "ru")
            result = provider.translate("hello", target_lang, source_lang)
            return bool(result)
        except Exception:
            return False

    def close(self) -> None:
        self.db.close()

    def remove_session(self) -> None:
        self.db.remove_session()
