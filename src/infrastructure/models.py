#!/usr/bin/env python3
"""Domain models - SQLAlchemy ORM classes."""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship


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
