#!/usr/bin/env python3
"""Translation test service - handles translation API testing."""

from typing import Optional

from application.service_interfaces import AbstractTranslationService


class TranslationTestService:
    """Service for testing translation API connectivity."""

    def __init__(self, translation_service: AbstractTranslationService) -> None:
        self._translation_service = translation_service

    def test_connection(self, source_lang: str = "en", target_lang: str = "ru") -> bool:
        """Test translation API with a simple query."""
        try:
            result = self._translation_service.translate(
                "hello", target_lang or "ru", source_lang or "en"
            )
            return bool(result)
        except Exception:
            return False
