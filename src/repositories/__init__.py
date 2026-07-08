"""Repositories package - data access layer."""

from repositories.base import AbstractDatabase
from repositories.language_repository import LanguageRepository
from repositories.settings_repository import SettingsRepository
from repositories.sqlite import SQLiteDatabase
from repositories.stats_repository import StatsRepository
from repositories.word_repository import WordRepository
from repositories.wotd_repository import WOTDRepository

__all__ = [
    "AbstractDatabase",
    "LanguageRepository",
    "SQLiteDatabase",
    "SettingsRepository",
    "StatsRepository",
    "WOTDRepository",
    "WordRepository",
]
