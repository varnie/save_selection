"""Word repository - handles word CRUD operations."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from domain.entities import History, Stats, Translation, Word, WordStats
from domain.repositories import AbstractStatsRepository, AbstractWordRepository
from infrastructure import mappers
from infrastructure.models import History as ORMHistory
from infrastructure.models import (
    Language as ORMLanguage,
)
from infrastructure.models import (
    Translation as ORMTranslation,
)
from infrastructure.models import (
    Word as ORMWord,
)
from infrastructure.models import WordStats as ORMWordStats
from repositories.base import AbstractDatabase


class WordRepository(AbstractWordRepository):
    """Repository for word operations."""

    def __init__(self, db: AbstractDatabase):
        self.db = db

    def add(self, phrase: str) -> Word:
        """Add a word, return its domain entity."""
        phrase = phrase.lower()
        orm_word = self.db.session.query(ORMWord).filter_by(phrase=phrase).first()
        if orm_word:
            return mappers.map_word(orm_word)
        orm_word = ORMWord(phrase=phrase)
        self.db.session.add(orm_word)
        self.db.commit()
        return mappers.map_word(orm_word)

    def get_by_phrase(self, phrase: str) -> Optional[Word]:
        """Get word by phrase."""
        orm_word = self.db.session.query(ORMWord).filter_by(phrase=phrase.lower()).first()
        if not orm_word:
            return None
        return mappers.map_word_with_details(orm_word)

    def exists(self, phrase: str) -> bool:
        """Check if word exists."""
        return self.get_by_phrase(phrase) is not None

    def get_all(
        self, search: Optional[str] = None, target_lang: Optional[str] = None
    ) -> list[Word]:
        """Get all words with stats."""
        lang = None
        if target_lang:
            lang = self.db.session.query(ORMLanguage).filter_by(code=target_lang).first()
            if not lang:
                return []

        query = self.db.session.query(ORMWord).options(
            joinedload(ORMWord.stats),
            joinedload(ORMWord.translations).joinedload(ORMTranslation.language),
        )

        if lang:
            query = query.join(
                ORMTranslation,
                (ORMTranslation.word_id == ORMWord.id) & (ORMTranslation.language_id == lang.id),
            )

        if search:
            search_term = f"%{search}%"
            if lang:
                query = query.filter(
                    (ORMWord.phrase.ilike(search_term))
                    | (ORMTranslation.translation.ilike(search_term))
                )
            else:
                query = query.filter(ORMWord.phrase.ilike(search_term))

        orm_words = query.distinct().order_by(ORMWord.phrase).all()
        return [mappers.map_word_with_details(w) for w in orm_words]

    def get_due(self, limit: int = 20, target_lang: Optional[str] = None) -> list[Word]:
        """Get words due for review (due_date <= now). No sorting - done in ReviewService."""
        now_ts = int(datetime.now(timezone.utc).timestamp())

        query = (
            self.db.session.query(ORMWord)
            .outerjoin(ORMWordStats)
            .filter((ORMWordStats.due_date <= now_ts) | (ORMWordStats.due_date.is_(None)))
        )

        if target_lang:
            lang = self.db.session.query(ORMLanguage).filter_by(code=target_lang).first()
            if lang:
                query = query.outerjoin(
                    ORMTranslation,
                    (ORMWord.id == ORMTranslation.word_id)
                    & (ORMTranslation.language_id == lang.id),
                ).filter(ORMTranslation.id.isnot(None))
            else:
                return []

        orm_words = query.limit(limit).all()

        return [mappers.map_word_with_details(w) for w in orm_words]

    def delete(self, phrase: str) -> None:
        """Delete a word."""
        word = self.db.session.query(ORMWord).filter_by(phrase=phrase.lower()).first()
        if word:
            self.db.session.delete(word)
            self.db.commit()

    def add_translation(self, word_id: int, translation: str, target_lang: str = "ru") -> None:
        """Add translation for a word."""
        lang = self.db.session.query(ORMLanguage).filter_by(code=target_lang).first()
        if not lang:
            return

        existing = (
            self.db.session.query(ORMTranslation)
            .filter_by(word_id=word_id, language_id=lang.id)
            .first()
        )

        if existing:
            existing.translation = translation
        else:
            trans = ORMTranslation(word_id=word_id, translation=translation, language_id=lang.id)
            self.db.session.add(trans)

        self.db.commit()

    def get_translation(self, word_id: int, target_lang: str = "ru") -> Optional[Translation]:
        """Get translation for a word as domain entity."""
        lang = self.db.session.query(ORMLanguage).filter_by(code=target_lang).first()
        if not lang:
            return None
        orm = (
            self.db.session.query(ORMTranslation)
            .filter_by(word_id=word_id, language_id=lang.id)
            .first()
        )
        if orm:
            return mappers.map_translation(orm)
        return None

    def update_word(self, word_id: int, phrase: str) -> None:
        """Update word phrase."""
        orm_word = self.db.session.query(ORMWord).filter_by(id=word_id).first()
        if orm_word:
            orm_word.phrase = phrase
            self.db.commit()

    def delete_by_id(self, word_id: int) -> None:
        """Delete a word by ID."""
        orm_word = self.db.session.query(ORMWord).filter_by(id=word_id).first()
        if orm_word:
            self.db.session.delete(orm_word)
            self.db.commit()

    def delete_translation(self, word_id: int, target_lang: str) -> None:
        """Delete translation for a specific language."""
        lang = self.db.session.query(ORMLanguage).filter_by(code=target_lang).first()
        if lang:
            orm = (
                self.db.session.query(ORMTranslation)
                .filter_by(word_id=word_id, language_id=lang.id)
                .first()
            )
            if orm:
                self.db.session.delete(orm)
                self.db.commit()


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
            return (
                self.db.session.query(func.count(func.distinct(ORMWordStats.word_id)))
                .join(ORMWord, ORMWordStats.word_id == ORMWord.id)
                .join(ORMTranslation, ORMWord.id == ORMTranslation.word_id)
                .filter(op)
                .scalar()
                or 0
            )

        short_interval = interval_count(ORMWordStats.interval_days <= 7)
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
