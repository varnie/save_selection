"""Statistics repository - handles review stats and history."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func

from domain.entities import History, Stats, WordStats
from domain.repositories import AbstractStatsRepository
from infrastructure import mappers
from infrastructure.models import History as ORMHistory
from infrastructure.models import Language as ORMLanguage
from infrastructure.models import Translation as ORMTranslation
from infrastructure.models import Word as ORMWord
from infrastructure.models import WordStats as ORMWordStats
from repositories.base import AbstractDatabase


class StatsRepository(AbstractStatsRepository):
    """Repository for word statistics."""

    def __init__(self, db: AbstractDatabase):
        self.db = db

    def update_word_stats(
        self, word_id: int, interval_days: int, due_date: int, ease_factor: float
    ) -> None:
        """Update word stats."""
        stats = self.db.session.query(ORMWordStats).filter_by(word_id=word_id).first()

        if stats:
            stats.interval_days = interval_days
            stats.due_date = due_date
            stats.ease_factor = ease_factor
            stats.last_reviewed = int(datetime.now(timezone.utc).timestamp())
        else:
            stats = ORMWordStats(
                word_id=word_id,
                interval_days=interval_days,
                due_date=due_date,
                ease_factor=ease_factor,
                last_reviewed=int(datetime.now(timezone.utc).timestamp()),
            )
            self.db.session.add(stats)

        self.db.commit()

    def get_word_stats(self, word_id: int) -> Optional[WordStats]:
        """Get stats for a word."""
        orm = self.db.session.query(ORMWordStats).filter_by(word_id=word_id).first()
        if not orm:
            return None
        return mappers.map_word_stats(orm)

    def record_review(self, word_id: int) -> History:
        """Record a review in history and return domain entity."""
        orm_history = ORMHistory(word_id=word_id)
        self.db.session.add(orm_history)
        self.db.commit()
        return mappers.map_history(orm_history)

    def get_review_count(self, word_id: int) -> int:
        """Get number of reviews for a word (for sorting: least seen first)."""
        return (
            self.db.session.query(func.count(ORMHistory.id)).filter_by(word_id=word_id).scalar()
            or 0
        )

    def get_stats(self) -> Stats:
        """Get overall statistics."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        today_start = int(datetime(now.year, now.month, now.day).timestamp())

        total = (
            self.db.session.query(func.count(func.distinct(ORMTranslation.word_id))).scalar() or 0
        )

        today_words = (
            self.db.session.query(func.count(func.distinct(ORMWord.id)))
            .join(ORMTranslation, ORMWord.id == ORMTranslation.word_id)
            .filter(ORMWord.created_at >= today_start)
            .scalar()
            or 0
        )

        today_reviews = (
            self.db.session.query(func.count(ORMHistory.id))
            .filter(ORMHistory.reviewed_at >= today_start)
            .scalar()
            or 0
        )

        total_reviews = self.db.session.query(func.count(ORMHistory.id)).scalar() or 0

        now_ts = int(datetime.now(timezone.utc).timestamp())

        due_count = (
            self.db.session.query(func.count(ORMWordStats.id))
            .filter(ORMWordStats.due_date <= now_ts)
            .scalar()
            or 0
        )

        def interval_count(op) -> int:
            # Use LEFT JOIN to include words without stats (treat as learning/short)
            # This counts ALL words with translations, not just those with stats
            return (
                self.db.session.query(func.count(func.distinct(ORMWord.id)))
                .select_from(ORMWord)
                .join(ORMTranslation, ORMWord.id == ORMTranslation.word_id)
                .outerjoin(ORMWordStats, ORMWord.id == ORMWordStats.word_id)
                .filter(op)
                .scalar()
                or 0
            )

        # Learning (≤7 days): include words with interval ≤ 7 OR no stats (new words)
        short_interval = interval_count(
            (ORMWordStats.interval_days <= 7) | (ORMWordStats.interval_days.is_(None))
        )
        # Mastered (>7 days): only words with interval > 7 (definitely mastered)
        long_interval = interval_count(ORMWordStats.interval_days > 7)

        today_date = datetime.now(timezone.utc).date()
        rows = (
            self.db.session.query(func.date(ORMHistory.reviewed_at, "unixepoch").label("day"))
            .distinct()
            .order_by(func.date(ORMHistory.reviewed_at, "unixepoch").desc())
            .all()
        )

        streak = 0
        if rows:
            review_dates = {row[0] for row in rows}
            check_date = today_date
            while check_date.strftime("%Y-%m-%d") in review_dates:
                streak += 1
                check_date -= timedelta(days=1)

        return mappers.map_stats(
            {
                "total_words": total,
                "today_words": today_words,
                "today_reviews": today_reviews,
                "total_reviews": total_reviews,
                "due_count": due_count,
                "short_interval": short_interval,
                "long_interval": long_interval,
                "streak": streak,
            }
        )

    def get_language_counts(self) -> dict:
        """Get word count per language."""
        results = (
            self.db.session.query(
                ORMLanguage.code,
                ORMLanguage.name,
                func.count(func.distinct(ORMTranslation.word_id)).label("count"),
            )
            .join(ORMTranslation, ORMTranslation.language_id == ORMLanguage.id)
            .join(ORMWord, ORMWord.id == ORMTranslation.word_id)
            .group_by(ORMLanguage.id)
            .all()
        )

        return {row.code: (row.name, row.count) for row in results}
