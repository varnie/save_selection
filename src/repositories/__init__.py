#!/usr/bin/env python3
"""Repositories package - data access layer."""

from repositories.base import AbstractDatabase, DatabaseFactory
from repositories.sqlite import SQLiteDatabase
from repositories.word_repository import WordRepository, StatsRepository
from repositories.settings_repository import SettingsRepository, LanguageRepository, WOTDRepository

# Register SQLite as default implementation
DatabaseFactory.register('sqlite', SQLiteDatabase)

__all__ = [
    'AbstractDatabase',
    'DatabaseFactory',
    'SQLiteDatabase',
    'WordRepository',
    'StatsRepository',
    'SettingsRepository',
    'LanguageRepository',
    'WOTDRepository',
]
