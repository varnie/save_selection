"""Notification service - handles notification logic."""

from constants import TEMP_PHRASE_FILE

from application.review_service import ReviewService
from application.word_service import WordManagementService


class NotificationService:
    """Service for notification operations."""

    def __init__(
        self,
        review_service: "ReviewService",
        word_service: "WordManagementService",
    ):
        self._review = review_service
        self._word = word_service

    def get_next_word_notification(self) -> str | None:
        """Get next word notification body."""
        word = self._review.get_next_word()
        if not word:
            return None

        phrase = word.phrase
        interval = word.interval_days

        translation, trans_lang = self._word.get_translation_with_lang(word.id)

        interval_str = self._review.format_interval(interval)
        abbrev = self._word.get_language_abbreviation(trans_lang) if trans_lang else "—"

        body = f"<b>{phrase}</b> [{interval_str}]"
        if translation:
            body += f"\n→ {translation} [{abbrev}]"

        with open(TEMP_PHRASE_FILE, "w") as f:
            f.write(phrase)

        self._review.review_word(word.id, quality=3)

        return body
