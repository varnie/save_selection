"""Word of the Day word sources."""

import csv
import os
import random
from abc import ABC, abstractmethod
from enum import Enum


class WordSourceType(Enum):
    LOCAL = "local"
    ONLINE = "online"


CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


class WordSource(ABC):
    """Abstract base class for word sources."""

    @abstractmethod
    def get_word(self, level: str) -> dict | None:
        """Get a random word for the given level.

        Returns:
            dict with 'word' and 'level' keys, or None if no word available
        """
        pass

    @abstractmethod
    def get_available_levels(self) -> list[str]:
        """Get list of available CEFR levels."""
        pass


class LocalWordSource(WordSource):
    """Local word list source with CEFR-level words from CSV."""

    def __init__(self):
        self.words = self._load_words()

    def _load_words(self) -> dict[str, list[str]]:
        """Load words from CSV file (headword,CEFR)."""
        base_path = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(base_path, "data", "ENGLISH_CERF_WORDS.csv")

        try:
            with open(csv_path, newline="") as f:
                reader = csv.DictReader(f)
                words: dict[str, list[str]] = {}
                for row in reader:
                    level = row.get("CEFR", "").upper()
                    word = row.get("headword", "").strip().lower()
                    if not level or not word:
                        continue
                    words.setdefault(level, [])
                    if word not in words[level]:
                        words[level].append(word)
                return words
        except (FileNotFoundError, KeyError, csv.Error):
            return {}

    def get_word(self, level: str) -> dict | None:
        """Get a random word for the given level."""
        level = level.upper()
        words = self.words.get(level, [])

        if not words:
            return None

        word = random.choice(words)  # noqa: S311 - not cryptographic, just word selection
        return {"word": word, "level": level}

    def get_available_levels(self) -> list[str]:
        """Get list of available CEFR levels from the word list."""
        return sorted(self.words.keys())


class OnlineWordSource(WordSource):
    """Online word source - placeholder for future implementation.

    This will fetch random words from external APIs when implemented.
    Currently returns None as no API is configured.
    """

    def __init__(self):
        self.api_url = None
        self.api_key = None

    def configure(self, api_url: str, api_key: str | None = None):
        """Configure the online source."""
        self.api_url = api_url
        self.api_key = api_key

    def get_word(self, level: str) -> dict | None:
        """Get a random word from online source.

        Note: Not yet implemented - returns None.
        """
        return None

    def get_available_levels(self) -> list[str]:
        """Get available levels - all CEFR levels."""
        return CEFR_LEVELS


def get_word_source(source_type: WordSourceType = WordSourceType.LOCAL) -> WordSource:
    """Factory function to get a word source.

    Args:
        source_type: WordSourceType enum value

    Returns:
        WordSource instance
    """
    if source_type == WordSourceType.ONLINE:
        return OnlineWordSource()
    return LocalWordSource()
