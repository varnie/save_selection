"""Word repository - handles word CRUD operations."""

from typing import Optional

from sqlalchemy.orm import contains_eager, joinedload

from domain.entities import Translation, Word
from domain.repositories import AbstractWordRepository
from infrastructure import mappers
from infrastructure.models import Language as ORMLanguage
from infrastructure.models import Translation as ORMTranslation
from infrastructure.models import Word as ORMWord
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
        self,
        search: Optional[str] = None,
        target_lang: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> list[Word]:
        """Get all words with stats."""
        lang = None
        if target_lang:
            lang = self.db.session.query(ORMLanguage).filter_by(code=target_lang).first()
            if not lang:
                return []

        query = self.db.session.query(ORMWord).options(joinedload(ORMWord.stats))

        if lang:
            query = query.join(
                ORMTranslation,
                (ORMTranslation.word_id == ORMWord.id) & (ORMTranslation.language_id == lang.id),
            ).options(
                contains_eager(ORMWord.translations)
            )
        else:
            query = query.options(
                joinedload(ORMWord.translations).joinedload(ORMTranslation.language)
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

        query = query.distinct().order_by(ORMWord.phrase)
        if limit is not None:
            query = query.limit(limit).offset(offset)
        orm_words = query.all()
        return [mappers.map_word_with_details(w) for w in orm_words]

    def get_for_review(self, limit: int = 20, target_lang: Optional[str] = None) -> list[Word]:
        """Get words ordered by least recently seen first (oldest review first)."""
        query = (
            self.db.session.query(ORMWord)
            .outerjoin(ORMWordStats)
            .options(joinedload(ORMWord.stats))
        )

        if target_lang:
            lang = self.db.session.query(ORMLanguage).filter_by(code=target_lang).first()
            if lang:
                query = (
                    query.join(
                        ORMTranslation,
                        (ORMWord.id == ORMTranslation.word_id)
                        & (ORMTranslation.language_id == lang.id),
                    )
                    .join(ORMTranslation.language)
                    .options(
                        contains_eager(ORMWord.translations).contains_eager(ORMTranslation.language)
                    )
                )
            else:
                return []
        else:
            query = query.options(
                joinedload(ORMWord.translations).joinedload(ORMTranslation.language)
            )

        orm_words = query.order_by(ORMWordStats.last_reviewed.asc().nullsfirst()).limit(limit).all()
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
