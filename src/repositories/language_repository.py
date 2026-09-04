"""Language repository."""

from domain.entities import Language
from domain.repositories import AbstractLanguageRepository
from infrastructure import mappers
from infrastructure.models import Language as ORMLanguage
from repositories.base import AbstractRepository


class LanguageRepository(AbstractLanguageRepository, AbstractRepository):
    """Repository for languages."""

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

        self.commit()
