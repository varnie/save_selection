"""Statistics repository - handles review stats and history."""

from datetime import datetime, timedelta, timezone

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
        self, word_id: int
    ) -> None:
        """Update word stats (set last_reviewed to now)."""
        now = int(datetime.now(timezone.utc).timestamp())
        stats = self.db.session.query(ORMWordStats).filter_by(word_id=word_id).first()

        if stats:
            stats.last_reviewed = now
        else:
            stats = ORMWordStats(
                word_id=word_id,
                last_reviewed=now,
            )
            self.db.session.add(stats)

        self.db.commit()

    def get_word_stats(self, word_id: int) -> WordStats | None:
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

    def get_review_counts(self, word_ids: list[int]) -> dict[int, int]:
        """Get review counts for multiple words in one query."""
        if not word_ids:
            return {}
        rows = (
            self.db.session.query(ORMHistory.word_id, func.count(ORMHistory.id))
            .filter(ORMHistory.word_id.in_(word_ids))
            .group_by(ORMHistory.word_id)
            .all()
        )
        return {row[0]: row[1] for row in rows}

    def get_stats(self) -> Stats:
        """Get overall statistics."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        today_start = int(datetime(now.year, now.month, now.day).timestamp())
        today_date = now.date()

        db = self.db.session

        # Combined: total words + today's new words
        total_today = (
            db.query(
                func.count(func.distinct(ORMTranslation.word_id)).label("total"),
                func.count(func.distinct(ORMWord.id)).filter(ORMWord.created_at >= today_start).label("today_words"),
            )
            .select_from(ORMWord)
            .join(ORMTranslation, ORMWord.id == ORMTranslation.word_id)
            .first()
        )
        total = total_today.total or 0
        today_words = total_today.today_words or 0

        # Combined: total reviews + today's reviews
        review_counts = (
            db.query(
                func.count(ORMHistory.id).label("total_reviews"),
                func.count(ORMHistory.id).filter(ORMHistory.reviewed_at >= today_start).label("today_reviews"),
            )
            .first()
        )
        total_reviews = review_counts.total_reviews or 0
        today_reviews = review_counts.today_reviews or 0

        # Streak — single query for distinct review dates
        rows = (
            db.query(func.date(ORMHistory.reviewed_at, "unixepoch").label("day"))
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
