"""Settings and WOTD repositories."""

from datetime import datetime, timezone

from domain.entities import Language, Setting
from domain.entities import WOTDHistory as WOTDHistoryEntity
from domain.repositories import (
    AbstractLanguageRepository,
    AbstractSettingsRepository,
    AbstractWOTDRepository,
)
from infrastructure import mappers
from infrastructure.models import (
    Language as ORMLanguage,
)
from infrastructure.models import (
    Setting as ORMSetting,
)
from infrastructure.models import (
    WOTDHistory as ORMWOTDHistory,
)
from repositories.base import AbstractDatabase


class SettingsRepository(AbstractSettingsRepository):
    """Repository for settings."""

    def __init__(self, db: AbstractDatabase):
        self.db = db

    def get(self, key: str, default: str | None = None) -> Setting | None:
        """Get a setting value as domain entity."""
        orm = self.db.session.query(ORMSetting).filter_by(key=key).first()
        if orm:
            return mappers.map_setting(orm)
        return None

    def get_all(self) -> dict[str, str]:
        """Get all settings as a flat dict."""
        rows = self.db.session.query(ORMSetting).all()
        return {row.key: row.value for row in rows}

    def set(self, key: str, value: str) -> None:
        """Set a setting value."""
        setting = self.db.session.query(ORMSetting).filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = ORMSetting(key=key, value=value)
            self.db.session.add(setting)
        self.db.commit()


class LanguageRepository(AbstractLanguageRepository):
    """Repository for languages."""

    def __init__(self, db: AbstractDatabase):
        self.db = db

    def get_by_code(self, code: str) -> Language | None:
        """Get language by code."""
        orm = self.db.session.query(ORMLanguage).filter_by(code=code).first()
        if orm:
            return mappers.map_language(orm)
        return None

    def get_all(self) -> list[Language]:
        """Get all languages."""
        orms = self.db.session.query(ORMLanguage).order_by(ORMLanguage.name).all()
        return [mappers.map_language(o) for o in orms]

    def init_defaults(self) -> None:
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

        existing_codes = {lang.code for lang in self.db.session.query(ORMLanguage.code).all()}

        for code, name, abbrev in default_languages:
            if code not in existing_codes:
                lang = ORMLanguage(code=code, name=name, abbreviation=abbrev)
                self.db.session.add(lang)

        self.db.commit()


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
