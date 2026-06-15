"""Review service - handles spaced repetition review logic."""

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
        """Get next word for review - least recently seen first, then by review count."""
        target_lang = self._get_setting("target_lang", "ru")
        words = self.word_repo.get_for_review(limit=50, target_lang=target_lang)

        if not words:
            return None

        word_ids = [w.id for w in words]
        review_counts = self.stats_repo.get_review_counts(word_ids)

        def sort_key(word: Word) -> tuple:
            return (review_counts.get(word.id, 0), word.last_reviewed or 0)

        sorted_words = sorted(words, key=sort_key)
        return sorted_words[0]

    def review_word(self, word_id: int) -> None:
        """Review a word - advance interval via SM-2 and mark as last reviewed."""
        stats = self.stats_repo.get_word_stats(word_id)
        interval = stats.interval_days if stats else 1
        ease = stats.ease_factor if stats else 2.5

        new_ease = ease + 0.1
        new_ease = max(1.3, new_ease)
        new_interval = int(interval * new_ease)
        new_interval = min(new_interval, 180)
        new_interval = max(1, new_interval)

        self.stats_repo.update_word_stats(word_id, new_interval, new_ease)
        self.stats_repo.record_review(word_id)

    def skip_word(self, word_id: int) -> None:
        """Skip word - mark as reviewed and reset interval."""
        self.stats_repo.record_review(word_id)
        self.stats_repo.update_word_stats(word_id, 1, 2.5)

    def get_stats(self) -> dict:
        """Get statistics."""
        stats = self.stats_repo.get_stats()
        return {
            "total_words": stats.total_words,
            "today_words": stats.today_words,
            "today_reviews": stats.today_reviews,
            "total_reviews": stats.total_reviews,

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
