"""Domain layer - pure business entities and repository interfaces."""

from domain.entities import (
    History,
    Language,
    Setting,
    Stats,
    Translation,
    Word,
    WordStats,
    WOTDHistory,
)
from domain.repositories import (
    AbstractLanguageRepository,
    AbstractSettingsRepository,
    AbstractStatsRepository,
    AbstractWordRepository,
    AbstractWOTDRepository,
)

__all__ = [
    "AbstractLanguageRepository",
    "AbstractSettingsRepository",
    "AbstractStatsRepository",
    "AbstractWOTDRepository",
    "AbstractWordRepository",
    "History",
    "Language",
    "Setting",
    "Stats",
    "Translation",
    "WOTDHistory",
    "Word",
    "WordStats",
]
