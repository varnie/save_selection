#!/usr/bin/env python3
"""Settings service - handles application settings."""

from domain.repositories import AbstractSettingsRepository
from application.service_interfaces import AbstractSettingsService
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
        return {
            "review_interval": int(self.get_setting("review_interval", "3600")),
            "source_lang": self.get_setting("source_lang", "en"),
            "target_lang": self.get_setting("target_lang", "ru"),
            "translation_provider": self.get_setting(
                "translation_provider", "google_direct"
            ),
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
