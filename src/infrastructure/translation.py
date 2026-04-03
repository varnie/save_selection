#!/usr/bin/env python3
"""Translation providers."""

from abc import ABC, abstractmethod
import requests

from application.service_interfaces import AbstractTranslationService


class TranslationProvider(ABC):
    """Abstract base class for translation providers."""

    @abstractmethod
    def translate(
        self, text: str, target_lang: str = "ru", source_lang: str = "en"
    ) -> str:
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

    def translate(
        self, text: str, target_lang: str = "ru", source_lang: str = "en"
    ) -> str:
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
            print(f"Translation error: {e}")
            return ""

    def get_name(self) -> str:
        return "Google Translate (direct)"


class GoogleDeepTranslatorProvider(TranslationProvider):
    """Google Translate provider using deep-translator library."""

    def __init__(self):
        from deep_translator import GoogleTranslator

        self.translator = GoogleTranslator(source="en", target="ru")

    def translate(
        self, text: str, target_lang: str = "ru", source_lang: str = "en"
    ) -> str:
        """Translate text using Google Translate via deep-translator."""
        try:
            self.translator.source = source_lang
            self.translator.target = target_lang
            result = self.translator.translate(text)
            return result.strip() if result else ""
        except Exception as e:
            print(f"Translation error: {e}")
            return ""

    def get_name(self) -> str:
        return "Google Translate (deep-translator)"


class EasyGoogleProvider(TranslationProvider):
    """Google Translate provider using easygoogletranslate library."""

    def __init__(self):
        from easygoogletranslate import EasyGoogleTranslate

        self.translator = EasyGoogleTranslate(
            source_language="en", target_language="ru"
        )

    def translate(
        self, text: str, target_lang: str = "ru", source_lang: str = "en"
    ) -> str:
        """Translate text using easygoogletranslate."""
        try:
            self.translator.source_language = source_lang
            self.translator.target_language = target_lang
            result = self.translator.translate(text)
            return result.strip() if result else ""
        except Exception as e:
            print(f"Translation error: {e}")
            return ""

    def get_name(self) -> str:
        return "EasyGoogle Translate"


class MyMemoryProvider(TranslationProvider):
    """MyMemory Translation API (free, rate-limited)."""

    def __init__(self):
        from deep_translator import MyMemoryTranslator

        self.translator = MyMemoryTranslator(source="en-US", target="ru-RU")

    def translate(
        self, text: str, target_lang: str = "ru", source_lang: str = "en"
    ) -> str:
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
            return result.strip() if result else ""
        except Exception as e:
            print(f"Translation error: {e}")
            return ""

    def get_name(self) -> str:
        return "MyMemory (free)"


class ProviderRegistry:
    """Registry of translation providers."""

    _providers = {
        "google_direct": GoogleDirectProvider,
        "google_deep": GoogleDeepTranslatorProvider,
        "easygoogle": EasyGoogleProvider,
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
    def list_providers(cls) -> list:
        """List available providers."""
        return [(name, cls.get(name).get_name()) for name in cls._providers.keys()]


class TranslationServiceImpl(AbstractTranslationService):
    """Implementation of TranslationService using provider registry."""

    def translate(
        self,
        text: str,
        target_lang: str = "ru",
        source_lang: str = "en",
        provider_name: str = "google_direct",
    ) -> str:
        """Translate text using the specified provider."""
        provider = ProviderRegistry.get(provider_name)
        return provider.translate(text, target_lang, source_lang)
