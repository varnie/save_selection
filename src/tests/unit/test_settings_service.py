"""Unit tests for SettingsService."""


class TestSettingsService:
    """Tests for SettingsService."""

    def test_get_setting_default(self, settings_service):
        """Test getting setting with default value."""
        value = settings_service.get_setting("nonexistent", "default_value")
        assert value == "default_value"

    def test_set_setting(self, settings_service):
        """Test setting a value."""
        settings_service.set_setting("test_key", "test_value")

        value = settings_service.get_setting("test_key")
        assert value == "test_value"

    def test_get_settings_returns_dict(self, settings_service):
        """Test getting all settings."""
        settings = settings_service.get_settings()

        assert isinstance(settings, dict)
        assert "source_lang" in settings
        assert "target_lang" in settings

    def test_save_settings(self, settings_service):
        """Test saving multiple settings."""
        settings = {
            "source_lang": "en",
            "target_lang": "de",
            "review_interval": "3600",
        }
        settings_service.save_settings(settings)

        assert settings_service.get_setting("source_lang") == "en"
        assert settings_service.get_setting("target_lang") == "de"

    def test_get_setting_returns_none_for_missing(self, settings_service):
        """Test that missing setting returns None."""
        value = settings_service.get_setting("missing_key")
        assert value is None
