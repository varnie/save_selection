"""Review service - handles spaced repetition review logic."""

from datetime import datetime, timezone
from typing import Optional

from application.service_interfaces import AbstractReviewService
from domain.entities import Word
from domain.repositories import (
    AbstractSettingsRepository,
    AbstractStatsRepository,
    AbstractWordRepository,
)


class ReviewService(AbstractReviewService):
    """Service for review operations with SM-2 algorithm."""

    def __init__(
        self,
        word_repo: AbstractWordRepository,
        stats_repo: AbstractStatsRepository,
        settings_repo: AbstractSettingsRepository,
    ) -> None:
        self.word_repo = word_repo
        self.stats_repo = stats_repo
        self.settings_repo = settings_repo

    def _get_setting(self, key: str, default: str) -> str:
        setting = self.settings_repo.get(key)
        return setting.value if setting else default

    def get_next_word(self) -> Optional[Word]:
        """Get next word due for review - least seen first, then by due date."""
        target_lang = self._get_setting("target_lang", "ru")
        words = self.word_repo.get_due(limit=50, target_lang=target_lang)

        if not words:
            return None

        word_ids = [w.id for w in words]
        review_counts = self.stats_repo.get_review_counts(word_ids)

        def sort_key(word: Word) -> tuple:
            return (review_counts.get(word.id, 0), word.due_date or 0)

        sorted_words = sorted(words, key=sort_key)
        return sorted_words[0]

    def review_word(self, word_id: int, quality: int = 3) -> None:
        """Review a word with SM-2 quality rating (0-5)."""
        stats = self.stats_repo.get_word_stats(word_id)

        if stats:
            interval = stats.interval_days
            ease = stats.ease_factor
            due = stats.due_date
        else:
            interval = 1
            ease = 2.5
            due = 0

        now = int(datetime.now(timezone.utc).timestamp())

        if quality < 3:
            new_interval = 1
            new_ease = max(1.3, ease - 0.2)
        else:
            new_ease = ease + 0.1 - (quality - 3) * 0.08
            new_ease = max(1.3, new_ease)

            if due == 0:
                new_interval = int(interval * new_ease * 0.5)
                new_interval = max(1, new_interval)
            else:
                new_interval = int(interval * new_ease)
                new_interval = min(new_interval, 180)

        new_due = now + new_interval * 86400

        self.stats_repo.update_word_stats(word_id, new_interval, new_due, new_ease)
        self.stats_repo.record_review(word_id)

    def skip_word(self, word_id: int) -> None:
        """Skip word - move to end of queue by updating due date."""
        self.stats_repo.record_review(word_id)

        stats = self.stats_repo.get_word_stats(word_id)
        current_interval = stats.interval_days if stats else 1
        current_ease = stats.ease_factor if stats else 2.5

        new_due = int(datetime.now(timezone.utc).timestamp()) + 600

        self.stats_repo.update_word_stats(word_id, current_interval, new_due, current_ease)

    def get_stats(self) -> dict:
        """Get statistics."""
        stats = self.stats_repo.get_stats()
        return {
            "total_words": stats.total_words,
            "today_words": stats.today_words,
            "today_reviews": stats.today_reviews,
            "total_reviews": stats.total_reviews,
            "due_count": stats.due_count,
            "short_interval": stats.short_interval,
            "long_interval": stats.long_interval,
            "streak": stats.streak,
        }

    def get_language_counts(self) -> dict:
        """Get word count per language."""
        return self.stats_repo.get_language_counts()

    def format_interval(self, interval: int) -> str:
        """Format interval days to human-readable string."""
        if interval == 1:
            return "1 day"
        elif interval < 30:
            return f"{interval} days"
        elif interval < 365:
            return f"{interval // 30} mo"
        else:
            return f"{interval // 365} yr"
