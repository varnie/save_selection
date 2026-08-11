"""Service factory - creates services with proper dependency injection."""

from dataclasses import dataclass

from application.export_service import ExportService
from application.notification_service import NotificationService
from application.review_service import ReviewService
from application.service_interfaces import (
    AbstractTranslationService,
)
from application.settings_service import SettingsService
from application.translation_test_service import TranslationTestService
from application.word_service import WordManagementService
from application.wotd_service import WOTDService
from domain.repositories import (
    AbstractLanguageRepository,
    AbstractSettingsRepository,
    AbstractStatsRepository,
    AbstractWordRepository,
    AbstractWOTDRepository,
)
from infrastructure.word_source import LocalWordSource
from repositories.base import AbstractDatabase


@dataclass
class ServiceFactory:
    """Factory for creating services with proper DI."""

    db: AbstractDatabase
    word_repo: AbstractWordRepository
    stats_repo: AbstractStatsRepository
    settings_repo: AbstractSettingsRepository
    language_repo: AbstractLanguageRepository
    wotd_repo: AbstractWOTDRepository
    translation_service: AbstractTranslationService

    @property
    def settings_service(self) -> SettingsService:
        return SettingsService(self.settings_repo)

    def create_word_service(self) -> WordManagementService:
        """Create word management service."""
        return WordManagementService(
            word_repo=self.word_repo,
            language_repo=self.language_repo,
            settings_service=self.settings_service,
            translation_service=self.translation_service,
        )

    def create_review_service(self) -> ReviewService:
        """Create review service."""
        return ReviewService(
            word_repo=self.word_repo,
            stats_repo=self.stats_repo,
            settings_service=self.settings_service,
        )

    def create_wotd_service(self, word_service: WordManagementService) -> WOTDService:
        """Create WOTD service."""
        return WOTDService(
            settings_service=self.settings_service,
            wotd_repo=self.wotd_repo,
            word_service=word_service,
            translation_service=self.translation_service,
            word_source=LocalWordSource(),
        )

    def create_export_service(self) -> ExportService:
        """Create export service."""
        return ExportService(self.word_repo)

    def create_notification_service(
        self,
        review_service: ReviewService,
        word_service: WordManagementService,
    ) -> NotificationService:
        """Create notification service."""
        return NotificationService(
            review_service=review_service,
            word_service=word_service,
        )

    def create_translation_test_service(self) -> TranslationTestService:
        """Create translation test service."""
        return TranslationTestService(self.translation_service)
