"""WOTD repository - handles Word of the Day history."""

from datetime import datetime, timezone

from domain.entities import WOTDHistory as WOTDHistoryEntity
from domain.repositories import AbstractWOTDRepository
from infrastructure import mappers
from infrastructure.models import WOTDHistory as ORMWOTDHistory
from repositories.base import AbstractDatabase


class WOTDRepository(AbstractWOTDRepository):
    """Repository for Word of the Day."""

    def __init__(self, db: AbstractDatabase):
        self.db = db

    def mark_shown(self, word: str, level: str) -> None:
        """Record a word as shown for today (UTC)."""
        today = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d")
        orm = ORMWOTDHistory(word=word, level=level, shown_date=today)
        self.db.session.add(orm)
        self.db.commit()

    def get_today(self) -> WOTDHistoryEntity | None:
        """Get today's WOTD if shown, or None (UTC)."""
        today = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d")
        orm = self.db.session.query(ORMWOTDHistory).filter_by(shown_date=today).first()
        if orm:
            return mappers.map_wotd_history(orm)
        return None
