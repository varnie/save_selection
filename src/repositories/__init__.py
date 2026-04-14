"""Repositories package - data access layer."""

from repositories.base import AbstractDatabase, DatabaseFactory
from repositories.settings_repository import LanguageRepository, SettingsRepository, WOTDRepository
from repositories.sqlite import SQLiteDatabase
from repositories.stats_repository import StatsRepository
from repositories.word_repository import WordRepository

# Register SQLite as default implementation
DatabaseFactory.register("sqlite", SQLiteDatabase)

__all__ = [
    "AbstractDatabase",
    "DatabaseFactory",
    "LanguageRepository",
    "SQLiteDatabase",
    "SettingsRepository",
    "StatsRepository",
    "WOTDRepository",
    "WordRepository",
]
