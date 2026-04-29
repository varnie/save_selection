"""Vocabulary service - thin facade with auto-delegation."""

from typing import List

from application.factory import ServiceFactory
from domain.entities import Language
from infrastructure.database_manager import DatabaseManager


class VocabService:
    """Vocabulary service - thin facade with auto-delegation.

    Uses ServiceFactory to create services.
    Most methods auto-delegate to appropriate service via __getattr__.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        factory: ServiceFactory,
    ) -> None:
        self._db_manager = db_manager

        self.language_repo = factory.language_repo
        self.language_repo.init_defaults()

        self.word_service = factory.create_word_service()
        self.review_service = factory.create_review_service()
        self.settings_service = factory.create_settings_service()
        self.export_service = factory.create_export_service()
        self.wotd_service = factory.create_wotd_service(self.word_service)
        self.notification_service = factory.create_notification_service(
            review_service=self.review_service,
            word_service=self.word_service,
        )
        self.translation_test_service = factory.create_translation_test_service()

    def __getattr__(self, name: str) -> None:
        """Auto-delegate to services."""
        for svc in [
            self.word_service,
            self.review_service,
            self.settings_service,
            self.wotd_service,
            self.notification_service,
            self.export_service,
            self.translation_test_service,
        ]:
            if hasattr(svc, name):
                return getattr(svc, name)
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

    def close(self) -> None:
        self._db_manager.close()

    def remove_session(self) -> None:
        self._db_manager.remove_session()

    def get_languages(self) -> List[Language]:
        return self.language_repo.get_all()

    def test_translation_api(self) -> bool:
        source_lang = self.get_setting("source_lang", "en")
        target_lang = self.get_setting("target_lang", "ru")
        return self.translation_test_service.test_connection(source_lang, target_lang)
