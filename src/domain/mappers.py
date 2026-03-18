#!/usr/bin/env python3
"""Mappers for converting between ORM models and domain entities."""

from typing import Any

from infrastructure.models import Word as ORMWord, Translation as ORMTranslation, Language as ORMLanguage
from infrastructure.models import WordStats as ORMWordStats, History as ORMHistory, WOTDHistory as ORMWOTDHistory
from infrastructure.models import Setting as ORMSetting
from domain.entities import Word, Translation, Language, WordStats, History, WOTDHistory, Setting, Stats


def map_word(orm: ORMWord) -> Word:
    """Map ORM Word to domain entity."""
    return Word(
        id=orm.id,
        phrase=orm.phrase,
        created_at=orm.created_at,
    )


def map_word_with_details(orm: ORMWord) -> Word:
    """Map ORM Word to domain entity with translation and stats."""
    word = Word(
        id=orm.id,
        phrase=orm.phrase,
        created_at=orm.created_at,
    )
    
    if orm.translations:
        word.translation = orm.translations[0].translation
        word.language_code = orm.translations[0].language.code if orm.translations[0].language else ""
    
    if orm.stats:
        word.interval_days = orm.stats.interval_days
        word.due_date = orm.stats.due_date
        word.ease_factor = orm.stats.ease_factor
    
    return word


def map_translation(orm: ORMTranslation) -> Translation:
    """Map ORM Translation to domain entity."""
    return Translation(
        id=orm.id,
        word_id=orm.word_id,
        translation=orm.translation,
        language_id=orm.language_id,
        created_at=orm.created_at,
    )


def map_language(orm: ORMLanguage) -> Language:
    """Map ORM Language to domain entity."""
    return Language(
        id=orm.id,
        code=orm.code,
        name=orm.name,
        abbreviation=orm.abbreviation,
    )


def map_word_stats(orm: ORMWordStats) -> WordStats:
    """Map ORM WordStats to domain entity."""
    return WordStats(
        id=orm.id,
        word_id=orm.word_id,
        interval_days=orm.interval_days,
        due_date=orm.due_date,
        ease_factor=orm.ease_factor,
        last_reviewed=orm.last_reviewed,
    )


def map_history(orm: ORMHistory) -> History:
    """Map ORM History to domain entity."""
    return History(
        id=orm.id,
        word_id=orm.word_id,
        reviewed_at=orm.reviewed_at,
    )


def map_wotd_history(orm: ORMWOTDHistory) -> WOTDHistory:
    """Map ORM WOTDHistory to domain entity."""
    return WOTDHistory(
        id=orm.id,
        word=orm.word,
        level=orm.level,
        shown_date=orm.shown_date,
        created_at=orm.created_at,
    )


def map_setting(orm: ORMSetting) -> Setting:
    """Map ORM Setting to domain entity."""
    return Setting(
        key=orm.key,
        value=orm.value,
    )


def map_stats(data: dict[str, Any]) -> Stats:
    """Map dict to Stats domain entity."""
    return Stats(
        total_words=data.get("total_words", 0),
        today_words=data.get("today_words", 0),
        today_reviews=data.get("today_reviews", 0),
        total_reviews=data.get("total_reviews", 0),
        due_count=data.get("due_count", 0),
        short_interval=data.get("short_interval", 0),
        long_interval=data.get("long_interval", 0),
        streak=data.get("streak", 0),
    )
