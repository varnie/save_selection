"""Tests for translation provider fallback behavior."""

from unittest.mock import MagicMock, patch

import pytest


def _provider_returning(value, raise_exc=None):
    """Build a provider instance whose translate returns value or raises."""
    provider = MagicMock()
    if raise_exc is not None:
        provider.translate.side_effect = raise_exc
    else:
        provider.translate.return_value = value
    return provider


def test_fallback_to_working_provider():
    """When the selected provider fails, a working fallback is used."""
    from infrastructure.translation import TranslationServiceImpl

    failing = _provider_returning(None, raise_exc=RuntimeError("blocked"))
    working = _provider_returning("привет")

    with patch.object(
        TranslationServiceImpl, "FALLBACK_ORDER", ["google_direct", "mymemory"]
    ), patch(
        "infrastructure.translation.ProviderRegistry.get",
        side_effect=[failing, working],
    ):
        service = TranslationServiceImpl()
        result = service.translate("hello", provider_name="google_direct")

    assert result == "привет"


def test_all_providers_fail_raises():
    """If every provider fails, a TranslationError is raised."""
    from domain.exceptions import TranslationError
    from infrastructure.translation import TranslationServiceImpl

    failing = _provider_returning(None, raise_exc=RuntimeError("blocked"))

    with (
        patch.object(TranslationServiceImpl, "FALLBACK_ORDER", ["google_direct", "mymemory"]),
        patch("infrastructure.translation.ProviderRegistry.get", return_value=failing),
        pytest.raises(TranslationError),
    ):
        TranslationServiceImpl().translate("hello", provider_name="google_direct")


def test_mymemory_is_default_provider():
    """The default provider should be mymemory (Google direct is blocked)."""
    from infrastructure.translation import TranslationServiceImpl

    assert TranslationServiceImpl().translate.__defaults__[2] == "mymemory"
