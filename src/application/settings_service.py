"""Settings service - handles application settings."""

import time

from application.service_interfaces import AbstractSettingsService
from config import DEFAULT_SETTINGS
from domain.repositories import AbstractSettingsRepository
from infrastructure.autostart import AutostartManager


class SettingsService(AbstractSettingsService):
    """Service for managing application settings."""

    _CACHE_TTL = 30

    def __init__(self, settings_repo: AbstractSettingsRepository) -> None:
        self.settings_repo = settings_repo
        self._cache: dict | None = None
        self._cache_ts: float = 0

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        """Get a single setting."""
        setting = self.settings_repo.get(key)
        return setting.value if setting else default

    def set_setting(self, key: str, value: str) -> None:
        """Set a single setting."""
        self._cache = None
        self.settings_repo.set(key, value)

    def get_settings(self) -> dict:
        """Get app settings (cached with TTL)."""
        now = time.time()
        if self._cache and now - self._cache_ts < self._CACHE_TTL:
            return self._cache

        all_settings = self.settings_repo.get_all()

        result = {
            "review_interval": int(all_settings.get("review_interval", DEFAULT_SETTINGS["review_interval"])),
            "source_lang": all_settings.get("source_lang", DEFAULT_SETTINGS["source_lang"]),
            "target_lang": all_settings.get("target_lang", DEFAULT_SETTINGS["target_lang"]),
            "translation_provider": all_settings.get("translation_provider", DEFAULT_SETTINGS["translation_provider"]),
        }
        self._cache = result
        self._cache_ts = now
        return result

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
