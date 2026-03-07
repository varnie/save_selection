#!/usr/bin/env python3
"""Database module for vocab app using SQLAlchemy."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy import func, and_
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session, scoped_session


def _utc_timestamp() -> int:
    """Get current UTC timestamp."""
    return int(datetime.now(timezone.utc).timestamp())


Base = declarative_base()


class Language(Base):
    __tablename__ = 'languages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    abbreviation = Column(String, nullable=False)

    translations = relationship("Translation", back_populates="language")


class Word(Base):
    __tablename__ = 'words'

    id = Column(Integer, primary_key=True, autoincrement=True)
    phrase = Column(String, unique=True, nullable=False)
    created_at = Column(Integer, nullable=False, default=_utc_timestamp)

    translations = relationship("Translation", back_populates="word", cascade="all, delete-orphan")
    stats = relationship("WordStats", back_populates="word", uselist=False, cascade="all, delete-orphan")
    history = relationship("History", back_populates="word", cascade="all, delete-orphan")


class Translation(Base):
    __tablename__ = 'translations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    word_id = Column(Integer, ForeignKey('words.id', ondelete='CASCADE'), nullable=False)
    translation = Column(String, nullable=False)
    language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)
    created_at = Column(Integer, nullable=False, default=_utc_timestamp)

    word = relationship("Word", back_populates="translations")
    language = relationship("Language", back_populates="translations")

    __table_args__ = (UniqueConstraint('word_id', 'language_id', name='_word_lang_uc'),)


class WordStats(Base):
    __tablename__ = 'word_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    word_id = Column(Integer, ForeignKey('words.id', ondelete='CASCADE'), nullable=False, unique=True)
    interval_days = Column(Integer, nullable=False, default=1)
    due_date = Column(Integer, nullable=False, default=_utc_timestamp)
    ease_factor = Column(Float, nullable=False, default=2.5)
    last_reviewed = Column(Integer, nullable=True)

    word = relationship("Word", back_populates="stats")


class History(Base):
    __tablename__ = 'history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    word_id = Column(Integer, ForeignKey('words.id', ondelete='CASCADE'), nullable=False)
    reviewed_at = Column(Integer, nullable=False, default=_utc_timestamp)

    word = relationship("Word", back_populates="history")


class WOTDHistory(Base):
    __tablename__ = 'wotd_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String, nullable=False)
    level = Column(String, nullable=False)
    shown_date = Column(String, nullable=False)  # YYYY-MM-DD format
    created_at = Column(Integer, nullable=False, default=_utc_timestamp)


class Setting(Base):
    __tablename__ = 'settings'

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.ScopedSession = scoped_session(session_factory)

    @property
    def session(self) -> Session:
        return self.ScopedSession()

    def remove_session(self):
        """Remove scoped session (call after thread completes)."""
        self.ScopedSession.remove()

    def connect(self):
        """Connect to database and create schema."""
        Base.metadata.create_all(self.engine)

    def _commit(self):
        """Commit with rollback on error."""
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def close(self):
        """Close connection."""
        self.ScopedSession.remove()

    def init_schema(self):
        """Initialize database schema (alias for connect)."""
        self.connect()
        self.init_languages()

    def init_languages(self):
        """Initialize languages table with default data."""
        default_languages = [
            ("en", "English", "EN"),
            ("ru", "Russian", "RU"),
            ("es", "Spanish", "ES"),
            ("fr", "French", "FR"),
            ("de", "German", "DE"),
            ("it", "Italian", "IT"),
            ("pt", "Portuguese", "PT"),
            ("ja", "Japanese", "JA"),
            ("zh", "Chinese", "ZH"),
            ("ko", "Korean", "KO"),
        ]

        # Get all existing codes in one query
        existing_codes = {lang.code for lang in self.session.query(Language.code).all()}

        for code, name, abbrev in default_languages:
            if code not in existing_codes:
                lang = Language(code=code, name=name, abbreviation=abbrev)
                self.session.add(lang)

        self._commit()

    def get_language_by_code(self, code: str) -> Optional[Language]:
        """Get language by code."""
        return self.session.query(Language).filter_by(code=code).first()

    def get_all_languages(self) -> list:
        """Get all languages."""
        return self.session.query(Language).order_by(Language.name).all()

    def add_word(self, phrase: str) -> int:
        """Add a word, return its ID."""
        phrase = phrase.lower()
        word = self.session.query(Word).filter_by(phrase=phrase).first()
        if word:
            return word.id

        word = Word(phrase=phrase)
        self.session.add(word)
        self._commit()
        return word.id

    def get_word_by_phrase(self, phrase: str) -> Optional[dict]:
        """Get word by phrase."""
        word = self.session.query(Word).filter_by(phrase=phrase.lower()).first()
        if not word:
            return None

        result = {
            "id": word.id,
            "phrase": word.phrase,
            "created_at": word.created_at
        }

        if word.stats:
            result["interval_days"] = word.stats.interval_days
            result["due_date"] = word.stats.due_date
            result["ease_factor"] = word.stats.ease_factor

        translations = word.translations
        if translations:
            result["translation"] = translations[0].translation

        return result

    def word_exists(self, phrase: str) -> bool:
        """Check if word exists."""
        return self.get_word_by_phrase(phrase) is not None

    def add_translation(self, word_id: int, translation: str, target_lang: str = "ru"):
        """Add translation for a word."""
        lang = self.get_language_by_code(target_lang)
        if not lang:
            return

        existing = self.session.query(Translation).filter_by(
            word_id=word_id, language_id=lang.id
        ).first()

        if existing:
            existing.translation = translation
        else:
            trans = Translation(word_id=word_id, translation=translation, language_id=lang.id)
            self.session.add(trans)

        self._commit()

    def get_translation(self, word_id: int, target_lang: str = "ru") -> Optional[str]:
        """Get translation for a word."""
        lang = self.get_language_by_code(target_lang)
        if not lang:
            return None
        trans = self.session.query(Translation).filter_by(
            word_id=word_id, language_id=lang.id
        ).first()
        return trans.translation if trans else None

    def update_word_stats(self, word_id: int, interval_days: int, due_date: int, ease_factor: float):
        """Update word stats."""
        stats = self.session.query(WordStats).filter_by(word_id=word_id).first()

        if stats:
            stats.interval_days = interval_days
            stats.due_date = due_date
            stats.ease_factor = ease_factor
            stats.last_reviewed = int(datetime.now(timezone.utc).timestamp())
        else:
            stats = WordStats(
                word_id=word_id,
                interval_days=interval_days,
                due_date=due_date,
                ease_factor=ease_factor,
                last_reviewed=int(datetime.now(timezone.utc).timestamp())
            )
            self.session.add(stats)

        self._commit()

    def get_word_stats(self, word_id: int) -> Optional[dict]:
        """Get stats for a word."""
        stats = self.session.query(WordStats).filter_by(word_id=word_id).first()
        if not stats:
            return None
        return {
            "id": stats.id,
            "word_id": stats.word_id,
            "interval_days": stats.interval_days,
            "due_date": stats.due_date,
            "ease_factor": stats.ease_factor,
            "last_reviewed": stats.last_reviewed
        }

    def get_due_words(self, limit: int = 20, target_lang: str = None) -> list:
        """Get words that are due for review, filtered and sorted in SQL."""
        now = int(datetime.now(timezone.utc).timestamp())

        query = self.session.query(Word).outerjoin(WordStats)

        if target_lang:
            lang = self.get_language_by_code(target_lang)
            if lang:
                query = query.outerjoin(
                    Translation, (Word.id == Translation.word_id) & (Translation.language_id == lang.id)
                ).filter(Translation.id != None)
            else:
                return []

        words = query.order_by(
            func.coalesce(WordStats.due_date, 0).asc(),
            func.coalesce(WordStats.interval_days, 1).asc()
        ).limit(limit).all()

        results = []
        for word in words:
            result = {
                "id": word.id,
                "phrase": word.phrase,
                "created_at": word.created_at,
                "interval_days": word.stats.interval_days if word.stats else 1,
                "due_date": word.stats.due_date if word.stats else now,
                "ease_factor": word.stats.ease_factor if word.stats else 2.5,
                "urgency": 100
            }
            results.append(result)

        return results

    def get_all_words(self, search: str = None, target_lang: str = None) -> list:
        """Get all words with stats, optionally filtered by search term and language."""
        lang = None
        if target_lang:
            lang = self.get_language_by_code(target_lang)
            if not lang:
                return []

        # Build the main query
        if lang:
            # When filtering by language, use INNER join to only get words with that translation
            query = self.session.query(
                Word,
                Translation.translation.label('target'),
            ).outerjoin(WordStats, WordStats.word_id == Word.id).join(
                Translation, (Translation.word_id == Word.id) & (Translation.language_id == lang.id)
            )
        else:
            # When not filtering, get first translation with language code
            first_trans = self.session.query(
                Translation.word_id,
                Translation.translation,
                Language.code.label('lang_code'),
            ).join(Language, Language.id == Translation.language_id).subquery()

            query = self.session.query(
                Word,
                func.coalesce(first_trans.c.translation, '').label('target'),
                func.coalesce(first_trans.c.lang_code, '').label('target_lang_code'),
            ).outerjoin(WordStats, WordStats.word_id == Word.id).outerjoin(
                first_trans, first_trans.c.word_id == Word.id
            )

        if search:
            search_term = f"%{search}%"
            if lang:
                query = query.filter(
                    (Word.phrase.ilike(search_term)) |
                    (Translation.translation.ilike(search_term))
                )
            else:
                query = query.filter(Word.phrase.ilike(search_term))

        # Use distinct to avoid duplicates
        rows = query.distinct(Word.id).order_by(Word.phrase).all()

        results = []
        for row in rows:
            word = row[0]
            target = row[1]

            # Get target_lang - from parameter if filtering, else from query
            if lang:
                target_lang_code = target_lang
            else:
                target_lang_code = row[2] if len(row) > 2 else ""

            result = {
                "id": word.id,
                "phrase": word.phrase,
                "created_at": word.created_at,
                "interval_days": word.stats.interval_days if word.stats else 1,
                "due_date": word.stats.due_date if word.stats else None,
                "ease_factor": word.stats.ease_factor if word.stats else 2.5,
                "source": word.phrase,
                "source_lang": "en",
                "target": target or "",
                "target_lang": target_lang_code or "",
            }
            results.append(result)

        return results

    def delete_word(self, phrase: str):
        """Delete a word."""
        word = self.session.query(Word).filter_by(phrase=phrase.lower()).first()
        if word:
            self.session.delete(word)
            self._commit()

    def record_review(self, word_id: int):
        """Record a review in history."""
        history = History(word_id=word_id)
        self.session.add(history)
        self._commit()

    def get_stats(self) -> dict:
        """Get overall statistics."""

        # Use UTC for today
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        today_start = int(datetime(now.year, now.month, now.day).timestamp())

        total = self.session.query(func.count(Word.id)).scalar() or 0

        today_words = self.session.query(func.count(Word.id)).filter(
            Word.created_at >= today_start
        ).scalar() or 0

        today_reviews = self.session.query(func.count(History.id)).filter(
            History.reviewed_at >= today_start
        ).scalar() or 0

        total_reviews = self.session.query(func.count(History.id)).scalar() or 0

        due_count = self.session.query(func.count(WordStats.id)).filter(
            (WordStats.due_date <= now) | (WordStats.due_date.is_(None))
        ).scalar() or 0

        short_interval = self.session.query(func.count(WordStats.id)).filter(
            WordStats.interval_days <= 7
        ).scalar() or 0

        long_interval = self.session.query(func.count(WordStats.id)).filter(
            WordStats.interval_days > 7
        ).scalar() or 0

        # Streak calculation
        today_date = datetime.now(timezone.utc).date()
        rows = self.session.query(
            func.date(History.reviewed_at, 'unixepoch').label('day')
        ).distinct().order_by(
            func.date(History.reviewed_at, 'unixepoch').desc()
        ).all()

        streak = 0
        if rows:
            review_dates = {row[0] for row in rows}
            check_date = today_date
            while check_date.strftime("%Y-%m-%d") in review_dates:
                streak += 1
                check_date -= timedelta(days=1)

        return {
            "total_words": total,
            "today_words": today_words,
            "today_reviews": today_reviews,
            "total_reviews": total_reviews,
            "due_count": due_count,
            "short_interval": short_interval,
            "long_interval": long_interval,
            "streak": streak,
        }

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get a setting value."""
        setting = self.session.query(Setting).filter_by(key=key).first()
        return setting.value if setting else default

    def set_setting(self, key: str, value: str):
        """Set a setting value."""
        setting = self.session.query(Setting).filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            self.session.add(setting)
        self._commit()

    def export_csv(self, filepath: str):
        """Export words to CSV."""
        import csv
        words = self.get_all_words()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["source", "target", "source language", "target language"])
            for word in words:
                writer.writerow([
                    word.get("source", ""),
                    word.get("target", ""),
                    word.get("source_lang", "en"),
                    word.get("target_lang", ""),
                ])

    def get_language_counts(self) -> dict:
        """Get word count per language."""
        from sqlalchemy import func
        # Count distinct words per language, only for words that exist
        results = self.session.query(
            Language.code,
            Language.name,
            func.count(func.distinct(Translation.word_id)).label('count')
        ).join(
            Translation, Translation.language_id == Language.id
        ).join(
            Word, Word.id == Translation.word_id
        ).group_by(Language.id).all()

        return {row.code: (row.name, row.count) for row in results}

    def mark_wotd_shown(self, word: str, level: str):
        """Record a word as shown for today (UTC)."""
        today = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d")
        entry = WOTDHistory(word=word, level=level, shown_date=today)
        self.session.add(entry)
        self._commit()

    def get_wotd_today(self) -> Optional[dict]:
        """Get today's WOTD if shown, or None (UTC)."""
        today = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d")
        entry = self.session.query(WOTDHistory).filter_by(shown_date=today).first()
        if entry:
            return {
                "word": entry.word,
                "level": entry.level,
                "shown_date": entry.shown_date
            }
        return None
