#!/usr/bin/env python3
"""Notification service - handles notification logic."""

from typing import Callable, Optional

from constants import TEMP_PHRASE_FILE


class NotificationService:
    """Service for notification operations."""

    def __init__(
        self,
        get_next_word_fn: Callable[[], Optional[object]],
        get_translation_fn: Callable[[int], tuple[Optional[str], Optional[str]]],
        skip_word_fn: Callable[[int], None],
        format_interval_fn: Callable[[int], str],
        get_lang_abbrev_fn: Callable[[str], str],
    ):
        self._get_next_word = get_next_word_fn
        self._get_translation = get_translation_fn
        self._skip_word = skip_word_fn
        self._format_interval = format_interval_fn
        self._get_lang_abbrev = get_lang_abbrev_fn

    def get_next_word_notification(self) -> Optional[str]:
        """Get next word notification body."""
        word = self._get_next_word()
        if not word:
            return None

        phrase = word.phrase
        interval = word.interval_days

        translation, trans_lang = self._get_translation(word.id)

        interval_str = self._format_interval(interval)
        abbrev = self._get_lang_abbrev(trans_lang) if trans_lang else "—"

        body = f"<b>{phrase}</b> [{interval_str}]"
        if translation:
            body += f"\n→ {translation} [{abbrev}]"

        with open(TEMP_PHRASE_FILE, "w") as f:
            f.write(phrase)

        self._skip_word(word.id)

        return body
