"""Application layer - service factory and configuration utilities."""

import logging
import os

from application.export_service import ExportService
from application.factory import ServiceFactory
from application.review_service import ReviewService
from application.service_interfaces import (
    AbstractExportService,
    AbstractNotificationService,
    AbstractReviewService,
    AbstractSettingsService,
    AbstractTranslationService,
    AbstractWordManagementService,
    AbstractWOTDService,
)
from application.settings_service import SettingsService
from application.vocab_service import VocabService
from application.word_service import WordManagementService
from application.wotd_service import WOTDService
from config import DATA_DIR_KEY, read_config
from constants import CONFIG_FILE, DEFAULT_DB_PATH
from infrastructure.translation import TranslationServiceImpl
from repositories import (
    LanguageRepository,
    SettingsRepository,
    SQLiteDatabase,
    StatsRepository,
    WordRepository,
    WOTDRepository,
)

logger = logging.getLogger(__name__)


def get_db_path(config_file: str = CONFIG_FILE) -> str:
    """Determine DB path from config file or default."""
    config = read_config(config_file)
    custom_data_dir = config.get(DATA_DIR_KEY)

    if isinstance(custom_data_dir, str):
        custom_db_path = os.path.join(os.path.expanduser(custom_data_dir), "vocab.db")
        dir_path = os.path.dirname(custom_db_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        return custom_db_path

    return DEFAULT_DB_PATH


def create_vocab_service(
    config_file: str = CONFIG_FILE,
    must_exist: bool = False,
    db_path: str | None = None,
) -> VocabService | None:
    """Create and initialize VocabService with default implementations."""
    final_db_path = get_db_path(config_file) if db_path is None else db_path

    if not os.path.exists(final_db_path):
        if must_exist:
            logger.error("Database not found at %s", final_db_path)
            logger.info("Please run the GUI app first to initialize the database.")
            return None

        os.makedirs(os.path.dirname(final_db_path), exist_ok=True)

    db = SQLiteDatabase(final_db_path)
    db.connect()

    word_repo = WordRepository(db)
    stats_repo = StatsRepository(db)
    settings_repo = SettingsRepository(db)
    language_repo = LanguageRepository(db)
    wotd_repo = WOTDRepository(db)
    translation_service = TranslationServiceImpl()

    factory = ServiceFactory(
        db=db,
        word_repo=word_repo,
        stats_repo=stats_repo,
        settings_repo=settings_repo,
        language_repo=language_repo,
        wotd_repo=wotd_repo,
        translation_service=translation_service,
    )

    return VocabService(
        db=db,
        factory=factory,
    )


__all__ = [
    "AbstractExportService",
    "AbstractNotificationService",
    "AbstractReviewService",
    "AbstractSettingsService",
    "AbstractTranslationService",
    "AbstractWOTDService",
    "AbstractWordManagementService",
    "ExportService",
    "ReviewService",
    "SettingsService",
    "VocabService",
    "WOTDService",
    "WordManagementService",
    "create_vocab_service",
    "get_db_path",
]
