#!/usr/bin/env python3
"""Abstract service interfaces - application layer defines contracts."""

from abc import ABC, abstractmethod
from typing import Optional

from domain.entities import Word


class AbstractTranslationService(ABC):
    """Abstract interface for translation operations."""

    @abstractmethod
    def translate(
        self,
        text: str,
        target_lang: str = "ru",
        source_lang: str = "en",
        provider_name: str = "google_direct",
    ) -> str:
        """Translate text to target language using specified provider."""
        pass


class AbstractWordManagementService(ABC):
    """Abstract interface for word management operations."""

    @abstractmethod
    def add_word(
        self,
        phrase: str,
        translation: Optional[str] = None,
        auto_translate: bool = False,
    ) -> Word:
        """Add a new word or add translation to existing word."""
        pass

    @abstractmethod
    def get_words(
        self, search: Optional[str] = None, target_lang: Optional[str] = None
    ) -> list[Word]:
        """Get all words with optional search and language filter."""
        pass

    @abstractmethod
    def get_translation(self, word_id: int) -> Optional[str]:
        """Get translation for a word."""
        pass

    @abstractmethod
    def get_translation_with_lang(
        self, word_id: int
    ) -> tuple[Optional[str], Optional[str]]:
        """Get translation and its language code."""
        pass

    @abstractmethod
    def get_language_abbreviation(self, lang_code: str) -> str:
        """Get language abbreviation for a code."""
        pass

    @abstractmethod
    def update_word(
        self, word_id: int, phrase: str, translation: Optional[str] = None
    ) -> None:
        """Update word phrase and optionally translation."""
        pass

    @abstractmethod
    def delete_word(self, phrase: str) -> None:
        """Delete a word."""
        pass

    @abstractmethod
    def delete_word_by_id(self, word_id: int) -> None:
        """Delete a word by ID."""
        pass

    @abstractmethod
    def delete_translation(self, word_id: int, target_lang: str) -> None:
        """Delete only translation for specific language, not the word."""
        pass

    @abstractmethod
    def export_csv(self, filepath: str) -> None:
        """Export words to CSV."""
        pass


class AbstractReviewService(ABC):
    """Abstract interface for review operations."""

    @abstractmethod
    def get_next_word(self) -> Optional[Word]:
        """Get next word due for review with translation in current target language."""
        pass

    @abstractmethod
    def review_word(self, word_id: int, quality: int = 3) -> None:
        """Review a word with SM-2 quality rating (0-5)."""
        pass

    @abstractmethod
    def skip_word(self, word_id: int) -> None:
        """Skip word - move to end of queue by updating due date."""
        pass

    @abstractmethod
    def get_stats(self) -> dict:
        """Get statistics."""
        pass

    @abstractmethod
    def get_language_counts(self) -> dict:
        """Get word count per language."""
        pass

    @abstractmethod
    def format_interval(self, interval: int) -> str:
        """Format interval days to human-readable string."""
        pass


class AbstractSettingsService(ABC):
    """Abstract interface for settings operations."""

    @abstractmethod
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a single setting."""
        pass

    @abstractmethod
    def set_setting(self, key: str, value: str) -> None:
        """Set a single setting."""
        pass

    @abstractmethod
    def get_settings(self) -> dict:
        """Get app settings."""
        pass

    @abstractmethod
    def save_settings(self, settings: dict) -> None:
        """Save app settings."""
        pass


class AbstractWOTDService(ABC):
    """Abstract interface for Word of the Day operations."""

    @abstractmethod
    def is_wotd_enabled(self) -> bool:
        """Check if Word of the Day is enabled."""
        pass

    @abstractmethod
    def get_wotd_level(self) -> str:
        """Get the configured WOTD level."""
        pass

    @abstractmethod
    def get_word_of_the_day(self) -> Optional[Word]:
        """Get Word of the Day - adds to vocab and returns Word entity."""
        pass

    @abstractmethod
    def save_wotd_to_vocab(
        self, word: str, translation: Optional[str] = None
    ) -> tuple[Optional[Word], bool]:
        """Save WOTD word to user's vocabulary."""
        pass


class AbstractWordManagementService(ABC):
    """Abstract interface for word management operations."""

    @abstractmethod
    def add_word(
        self, phrase: str, translation: str | None = None, auto_translate: bool = False
    ):
        """Add a new word or add translation to existing word."""
        pass

    @abstractmethod
    def get_words(self, search: str | None = None, target_lang: str | None = None):
        """Get all words with optional search and language filter."""
        pass

    @abstractmethod
    def get_translation(self, word_id: int) -> str | None:
        """Get translation for a word."""
        pass

    @abstractmethod
    def get_translation_with_lang(self, word_id: int) -> tuple[str | None, str | None]:
        """Get translation and its language code."""
        pass

    @abstractmethod
    def get_language_abbreviation(self, lang_code: str) -> str:
        """Get language abbreviation for a code."""
        pass

    @abstractmethod
    def update_word(
        self, word_id: int, phrase: str, translation: str | None = None
    ) -> None:
        """Update word phrase and optionally translation."""
        pass

    @abstractmethod
    def delete_word(self, phrase: str) -> None:
        """Delete a word."""
        pass

    @abstractmethod
    def delete_word_by_id(self, word_id: int) -> None:
        """Delete a word by ID."""
        pass

    @abstractmethod
    def delete_translation(self, word_id: int, target_lang: str) -> None:
        """Delete only translation for specific language, not the word."""
        pass

    @abstractmethod
    def export_csv(self, filepath: str) -> None:
        """Export words to CSV."""
        pass


class AbstractReviewService(ABC):
    """Abstract interface for review operations."""

    @abstractmethod
    def get_next_word(self):
        """Get next word due for review with translation in current target language."""
        pass

    @abstractmethod
    def review_word(self, word_id: int, quality: int = 3) -> None:
        """Review a word with SM-2 quality rating (0-5)."""
        pass

    @abstractmethod
    def skip_word(self, word_id: int) -> None:
        """Skip word - move to end of queue by updating due date."""
        pass

    @abstractmethod
    def get_stats(self) -> dict:
        """Get statistics."""
        pass

    @abstractmethod
    def get_language_counts(self) -> dict:
        """Get word count per language."""
        pass

    @abstractmethod
    def format_interval(self, interval: int) -> str:
        """Format interval days to human-readable string."""
        pass


class AbstractSettingsService(ABC):
    """Abstract interface for settings operations."""

    @abstractmethod
    def get_setting(self, key: str, default: str | None = None) -> str | None:
        """Get a single setting."""
        pass

    @abstractmethod
    def set_setting(self, key: str, value: str) -> None:
        """Set a single setting."""
        pass

    @abstractmethod
    def get_settings(self) -> dict:
        """Get app settings."""
        pass

    @abstractmethod
    def save_settings(self, settings: dict) -> None:
        """Save app settings."""
        pass


class AbstractWOTDService(ABC):
    """Abstract interface for Word of the Day operations."""

    @abstractmethod
    def is_wotd_enabled(self) -> bool:
        """Check if Word of the Day is enabled."""
        pass

    @abstractmethod
    def get_wotd_level(self) -> str:
        """Get the configured WOTD level."""
        pass

    @abstractmethod
    def get_word_of_the_day(self):
        """Get Word of the Day - adds to vocab and returns Word entity."""
        pass

    @abstractmethod
    def save_wotd_to_vocab(self, word: str, translation: str | None = None) -> tuple:
        """Save WOTD word to user's vocabulary."""
        pass
