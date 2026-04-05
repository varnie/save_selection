"""Settings service - handles application settings."""

from application.service_interfaces import AbstractSettingsService
from domain.repositories import AbstractSettingsRepository
from infrastructure.autostart import AutostartManager


class SettingsService(AbstractSettingsService):
    """Service for managing application settings."""

    def __init__(self, settings_repo: AbstractSettingsRepository) -> None:
        self.settings_repo = settings_repo

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        """Get a single setting."""
        setting = self.settings_repo.get(key)
        return setting.value if setting else default

    def set_setting(self, key: str, value: str) -> None:
        """Set a single setting."""
        self.settings_repo.set(key, value)

    def get_settings(self) -> dict:
        """Get app settings."""
        review_interval = self.get_setting("review_interval")
        source_lang = self.get_setting("source_lang")
        target_lang = self.get_setting("target_lang")
        translation_provider = self.get_setting("translation_provider")

        return {
            "review_interval": int(review_interval) if review_interval else 3600,
            "source_lang": source_lang or "en",
            "target_lang": target_lang or "ru",
            "translation_provider": translation_provider or "google_direct",
        }

    def save_settings(self, settings: dict) -> None:
        """Save app settings."""
        for key, value in settings.items():
            self.set_setting(key, str(value))

        if "autostart" in settings:
            self._set_autostart(settings["autostart"] == "true")

    def _set_autostart(self, enable: bool) -> None:
        """Enable or disable autostart."""
        if enable:
            AutostartManager.enable()
        else:
            AutostartManager.disable()
