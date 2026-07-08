"""Settings repository."""

from domain.entities import Setting
from domain.repositories import AbstractSettingsRepository
from infrastructure import mappers
from infrastructure.models import Setting as ORMSetting
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
