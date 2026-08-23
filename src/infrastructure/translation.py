"""Translation providers."""

import logging
from abc import ABC, abstractmethod
from typing import ClassVar

import requests

from application.service_interfaces import AbstractTranslationService
from domain.exceptions import TranslationError

logger = logging.getLogger(__name__)


class TranslationProvider(ABC):
    """Abstract base class for translation providers."""

    @abstractmethod
    def translate(self, text: str, target_lang: str = "ru", source_lang: str = "en") -> str:
        """Translate text to target language."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return provider display name."""
        pass


class GoogleDirectProvider(TranslationProvider):
    """Google Translate provider using direct HTTP requests."""

    def __init__(self):
        self.base_url = "https://translate.googleapis.com/translate_a/single"

    def translate(self, text: str, target_lang: str = "ru", source_lang: str = "en") -> str:
        """Translate text using Google Translate."""
        try:
            response = requests.get(
                self.base_url,
                params={
                    "client": "gtx",
                    "sl": source_lang,
                    "tl": target_lang,
                    "dt": "t",
                    "q": text,
                },
                timeout=12,
            )
            response.raise_for_status()
            data = response.json()

            if data and data[0]:
                for item in data[0]:
                    if item[0]:
                        return item[0].strip()

            return ""
        except Exception as e:
            logger.warning("GoogleDirect translation failed: %s", e)
            raise TranslationError(f"GoogleDirect translation failed: {e}") from e

    def get_name(self) -> str:
        return "Google Translate (direct)"


class GoogleDeepTranslatorProvider(TranslationProvider):
    """Google Translate provider using deep-translator library."""

    def __init__(self):
        from deep_translator import GoogleTranslator

        self.translator = GoogleTranslator(source="en", target="ru")

    def translate(self, text: str, target_lang: str = "ru", source_lang: str = "en") -> str:
        """Translate text using Google Translate via deep-translator."""
        try:
            self.translator.source = source_lang
            self.translator.target = target_lang
            result = self.translator.translate(text)
            if isinstance(result, list):
                result = result[0] if result else ""
            return result.strip() if result else ""
        except Exception as e:
            logger.warning("GoogleDeep translation failed: %s", e)
            raise TranslationError(f"GoogleDeep translation failed: {e}") from e

    def get_name(self) -> str:
        return "Google Translate (deep-translator)"


class MyMemoryProvider(TranslationProvider):
    """MyMemory Translation API (free, rate-limited)."""

    def __init__(self):
        from deep_translator import MyMemoryTranslator

        self.translator = MyMemoryTranslator(source="en-US", target="ru-RU")

    def translate(self, text: str, target_lang: str = "ru", source_lang: str = "en") -> str:
        """Translate text using MyMemory API."""
        try:
            lang_map = {
                "ru": "ru-RU",
                "en": "en-US",
                "de": "de-DE",
                "fr": "fr-FR",
                "es": "es-ES",
                "it": "it-IT",
                "pt": "pt-PT",
                "uk": "uk-UA",
            }
            src_lang = lang_map.get(source_lang, f"{source_lang}-{source_lang.upper()}")
            tgt_lang = lang_map.get(target_lang, f"{target_lang}-{target_lang.upper()}")

            self.translator.source = src_lang
            self.translator.target = tgt_lang
            result = self.translator.translate(text)
            if isinstance(result, list):
                result = result[0] if result else ""
            return result.strip() if result else ""
        except Exception as e:
            logger.warning("MyMemory translation failed: %s", e)
            raise TranslationError(f"MyMemory translation failed: {e}") from e

    def get_name(self) -> str:
        return "MyMemory (free)"


class ProviderRegistry:
    """Registry of translation providers."""

    _providers: ClassVar[dict[str, type[TranslationProvider]]] = {
        "google_direct": GoogleDirectProvider,
        "google_deep": GoogleDeepTranslatorProvider,
        "mymemory": MyMemoryProvider,
    }

    @classmethod
    def get(cls, provider_name: str) -> TranslationProvider:
        """Get provider by name."""
        provider_class = cls._providers.get(provider_name)
        if provider_class:
            return provider_class()
        return GoogleDirectProvider()

    @classmethod
    def list_providers(cls) -> list[tuple[str, str]]:
        """List available providers."""
        return [(name, cls.get(name).get_name()) for name in cls._providers]


class TranslationServiceImpl(AbstractTranslationService):
    """Implementation of TranslationService using provider registry."""

    # Fallback order tried when the selected provider fails (429, blocked, etc.).
    # NOTE: "easygoogle" is intentionally excluded — its underlying library
    # touches a local error.txt file on failure and is unreliable.
    FALLBACK_ORDER = ["google_deep", "mymemory"]

    def translate(
        self,
        text: str,
        target_lang: str = "ru",
        source_lang: str = "en",
        provider_name: str = "mymemory",
    ) -> str:
        """Translate text using the specified provider.

        If the selected provider fails, other available providers are tried
        in fallback order so translation keeps working even when one backend
        is blocked (e.g. Google returning HTTP 429).
        """
        providers_to_try = [provider_name] + [p for p in self.FALLBACK_ORDER if p != provider_name]

        last_error: Exception | None = None
        for name in providers_to_try:
            try:
                provider = ProviderRegistry.get(name)
                result = provider.translate(text, target_lang, source_lang)
                if result:
                    return result
            except Exception as e:  # noqa: BLE001 - try next provider on any failure
                logger.warning("Translation via '%s' failed: %s", name, e)
                last_error = e

        if last_error is not None:
            raise TranslationError(f"All translation providers failed: {last_error}") from last_error
        raise TranslationError("All translation providers returned empty results")
