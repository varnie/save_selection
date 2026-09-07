"""WOTD repository - handles Word of the Day history."""

from sqlalchemy.exc import IntegrityError

from domain.entities import WOTDHistory as WOTDHistoryEntity
from domain.repositories import AbstractWOTDRepository
from domain.time_utils import today_str
from infrastructure import mappers
from infrastructure.models import WOTDHistory as ORMWOTDHistory
from repositories.base import AbstractRepository


class WOTDRepository(AbstractWOTDRepository, AbstractRepository):
    """Repository for Word of the Day."""

    def mark_shown(self, word: str, level: str) -> None:
        """Record a word as shown for today (UTC).

        Idempotent: if another instance already recorded today (unique
        shown_date), the duplicate insert is rolled back and ignored.
        """
        today = today_str()
        orm = ORMWOTDHistory(word=word, level=level, shown_date=today)
        self.db.session.add(orm)
        try:
            self.commit()
        except IntegrityError:
            self.rollback()

    def get_today(self) -> WOTDHistoryEntity | None:
        """Get today's WOTD if shown, or None (UTC)."""
        today = today_str()
        orm = self.db.session.query(ORMWOTDHistory).filter_by(shown_date=today).first()
        if orm:
            return mappers.map_wotd_history(orm)
        return None
