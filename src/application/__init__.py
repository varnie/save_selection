#!/usr/bin/env python3
"""Application layer - service factory and configuration utilities."""

import os
from typing import Optional

from config import read_config
from constants import DEFAULT_DB_PATH, CONFIG_FILE
from application.vocab_service import VocabService
from repositories import (
    SQLiteDatabase,
    WordRepository,
    StatsRepository,
    SettingsRepository,
    LanguageRepository,
    WOTDRepository,
)
from infrastructure.translation import TranslationServiceImpl
from application.service_interfaces import (
    AbstractTranslationService,
    AbstractWordManagementService,
    AbstractReviewService,
    AbstractSettingsService,
    AbstractWOTDService,
)


def get_db_path(config_file: str = CONFIG_FILE) -> str:
    """Determine DB path from config file or default."""
    config = read_config(config_file)
    custom_data_dir = config.get("data_dir")

    if custom_data_dir:
        custom_db_path = os.path.join(os.path.expanduser(custom_data_dir), "vocab.db")
        os.makedirs(os.path.dirname(custom_db_path), exist_ok=True)
        return custom_db_path

    return DEFAULT_DB_PATH


def create_vocab_service(
    config_file: str = CONFIG_FILE,
    must_exist: bool = False,
    db_path: str | None = None,
) -> Optional[VocabService]:
    """Create and initialize VocabService with default implementations."""
    if db_path is None:
        db_path = get_db_path(config_file)

    if not os.path.exists(db_path):
        if must_exist:
            print(f"Error: Database not found at {db_path}")
            print("Please run the GUI app first to initialize the database.")
            return None

        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    db = SQLiteDatabase(db_path)
    db.connect()

    word_repo = WordRepository(db)
    stats_repo = StatsRepository(db)
    settings_repo = SettingsRepository(db)
    language_repo = LanguageRepository(db)
    wotd_repo = WOTDRepository(db)
    translation_service = TranslationServiceImpl()

    return VocabService(
        db=db,
        word_repo=word_repo,
        stats_repo=stats_repo,
        settings_repo=settings_repo,
        language_repo=language_repo,
        wotd_repo=wotd_repo,
        translation_service=translation_service,
    )


from application.word_service import WordManagementService
from application.review_service import ReviewService
from application.settings_service import SettingsService
from application.wotd_service import WOTDService

__all__ = [
    "VocabService",
    "WordManagementService",
    "ReviewService",
    "SettingsService",
    "WOTDService",
    "AbstractTranslationService",
    "AbstractWordManagementService",
    "AbstractReviewService",
    "AbstractSettingsService",
    "AbstractWOTDService",
    "create_vocab_service",
    "get_db_path",
]
