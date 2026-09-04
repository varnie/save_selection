"""Tests for VocabService."""

from unittest.mock import MagicMock, patch

import pytest

from application.vocab_service import VocabService


class TestVocabService:
    """Tests for VocabService class."""

    @patch("application.vocab_service.ServiceFactory")
    def test_init_creates_services(self, mock_factory_class):
        """Test that __init__ creates all services."""
        mock_db = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_word_service.return_value = MagicMock()
        mock_factory.create_review_service.return_value = MagicMock()
        mock_factory.settings_service = MagicMock()
        mock_factory.create_export_service.return_value = MagicMock()
        mock_factory.create_wotd_service.return_value = MagicMock()
        mock_factory.create_notification_service.return_value = MagicMock()
        mock_factory.create_translation_test_service.return_value = MagicMock()
        mock_factory.language_repo = MagicMock()
        mock_factory_class.return_value = mock_factory

        service = VocabService(db=mock_db, factory=mock_factory)

        assert service._db == mock_db
        assert service.word_service is not None
        assert service.review_service is not None
        assert service.settings_service is not None

    def test_close_calls_db_close(self):
        """Test that close calls db.close()."""
        mock_db = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_word_service.return_value = MagicMock()
        mock_factory.create_review_service.return_value = MagicMock()
        mock_factory.settings_service = MagicMock()
        mock_factory.create_export_service.return_value = MagicMock()
        mock_factory.create_wotd_service.return_value = MagicMock()
        mock_factory.create_notification_service.return_value = MagicMock()
        mock_factory.create_translation_test_service.return_value = MagicMock()
        mock_factory.language_repo = MagicMock()

        service = VocabService(db=mock_db, factory=mock_factory)
        service.close()

        mock_db.close.assert_called_once()

    def test_remove_session_calls_db(self):
        """Test that remove_session calls db.remove_session()."""
        mock_db = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_word_service.return_value = MagicMock()
        mock_factory.create_review_service.return_value = MagicMock()
        mock_factory.settings_service = MagicMock()
        mock_factory.create_export_service.return_value = MagicMock()
        mock_factory.create_wotd_service.return_value = MagicMock()
        mock_factory.create_notification_service.return_value = MagicMock()
        mock_factory.create_translation_test_service.return_value = MagicMock()
        mock_factory.language_repo = MagicMock()

        service = VocabService(db=mock_db, factory=mock_factory)
        service.remove_session()

        mock_db.remove_session.assert_called_once()

    def test_getattr_delegates_to_word_service(self):
        """Test that __getattr__ delegates to word_service."""
        mock_db = MagicMock()
        mock_factory = MagicMock()
        mock_word_service = MagicMock()
        mock_word_service.add_word = MagicMock(return_value="added")
        mock_factory.create_word_service.return_value = mock_word_service
        mock_factory.create_review_service.return_value = MagicMock()
        mock_factory.settings_service = MagicMock()
        mock_factory.create_export_service.return_value = MagicMock()
        mock_factory.create_wotd_service.return_value = MagicMock()
        mock_factory.create_notification_service.return_value = MagicMock()
        mock_factory.create_translation_test_service.return_value = MagicMock()
        mock_factory.language_repo = MagicMock()

        service = VocabService(db=mock_db, factory=mock_factory)
        result = service.add_word("hello")

        assert result == "added"

    def test_getattr_raises_attribute_error(self):
        """Test that __getattr__ raises AttributeError for unknown attr."""
        mock_db = MagicMock()
        mock_factory = MagicMock()
        mock_factory.create_word_service.return_value = MagicMock(spec=[])
        mock_factory.create_review_service.return_value = MagicMock(spec=[])
        mock_factory.settings_service = MagicMock(spec=[])
        mock_factory.create_export_service.return_value = MagicMock(spec=[])
        mock_factory.create_wotd_service.return_value = MagicMock(spec=[])
        mock_factory.create_notification_service.return_value = MagicMock(spec=[])
        mock_factory.create_translation_test_service.return_value = MagicMock(spec=[])
        mock_factory.language_repo = MagicMock()

        service = VocabService(db=mock_db, factory=mock_factory)

        with pytest.raises(AttributeError, match="has no attribute 'nonexistent_method'"):
            _ = service.nonexistent_method

    @patch("application.vocab_service.ServiceFactory")
    def test_get_languages(self, mock_factory_class):
        """Test get_languages method."""
        mock_db = MagicMock()
        mock_factory = MagicMock()
        mock_language_repo = MagicMock()
        mock_language_repo.get_all.return_value = ["en", "ru"]
        mock_factory.language_repo = mock_language_repo
        mock_factory.create_word_service.return_value = MagicMock()
        mock_factory.create_review_service.return_value = MagicMock()
        mock_factory.settings_service = MagicMock()
        mock_factory.create_export_service.return_value = MagicMock()
        mock_factory.create_wotd_service.return_value = MagicMock()
        mock_factory.create_notification_service.return_value = MagicMock()
        mock_factory.create_translation_test_service.return_value = MagicMock()
        mock_factory_class.return_value = mock_factory

        service = VocabService(db=mock_db, factory=mock_factory)
        result = service.get_languages()

        assert result == ["en", "ru"]
        mock_language_repo.get_all.assert_called_once()

    @patch("application.vocab_service.ServiceFactory")
    def test_test_translation_api(self, mock_factory_class):
        """Test test_translation_api method."""
        mock_db = MagicMock()
        mock_factory = MagicMock()

        mock_settings_service = MagicMock()
        mock_settings_service.get_source_lang.return_value = "en"
        mock_settings_service.get_target_lang.return_value = "ru"
        mock_settings_service.get_translation_provider.return_value = "google_direct"

        mock_translation_test_service = MagicMock()
        mock_translation_test_service.test_connection.return_value = True

        mock_factory.language_repo = MagicMock()
        mock_factory.create_word_service.return_value = MagicMock()
        mock_factory.create_review_service.return_value = MagicMock()
        mock_factory.settings_service = mock_settings_service
        mock_factory.create_export_service.return_value = MagicMock()
        mock_factory.create_wotd_service.return_value = MagicMock()
        mock_factory.create_notification_service.return_value = MagicMock()
        mock_factory.create_translation_test_service.return_value = mock_translation_test_service
        mock_factory_class.return_value = mock_factory

        service = VocabService(db=mock_db, factory=mock_factory)

        result = service.test_translation_api()

        assert result is True
        mock_translation_test_service.test_connection.assert_called_once_with(
            "en", "ru", "google_direct"
        )
