"""Tests for domain entities."""

from domain.entities import Language, Stats, Word, WordStats


class TestWordEntity:
    """Tests for Word entity."""

    def test_word_defaults(self):
        """Test Word entity default values."""
        word = Word()
        assert word.id == 0
        assert word.phrase == ""

    def test_word_with_values(self):
        """Test Word entity with values."""
        word = Word(id=1, phrase="test", translation="тест")
        assert word.id == 1
        assert word.phrase == "test"


class TestLanguageEntity:
    """Tests for Language entity."""

    def test_language_defaults(self):
        """Test Language entity default values."""
        lang = Language()
        assert lang.id == 0
        assert lang.code == ""
        assert lang.name == ""

    def test_language_fields(self):
        """Test Language entity fields."""
        lang = Language(id=1, code="ru", name="Russian", abbreviation="RU")
        assert lang.code == "ru"
        assert lang.abbreviation == "RU"


class TestStatsEntity:
    """Tests for Stats entity."""

    def test_stats_defaults(self):
        """Test Stats entity default values."""
        stats = Stats()
        assert stats.total_words == 0
        assert stats.today_reviews == 0
        assert stats.streak == 0

    def test_stats_with_values(self):
        """Test Stats entity with values."""
        stats = Stats(total_words=100, today_reviews=10, streak=5)
        assert stats.total_words == 100
        assert stats.today_reviews == 10
        assert stats.streak == 5


class TestWordStatsEntity:
    """Tests for WordStats entity."""

    def test_word_stats_defaults(self):
        """Test WordStats entity default values."""
        stats = WordStats()
        assert stats.word_id == 0

    def test_word_stats_with_values(self):
        """Test WordStats entity with values."""
        stats = WordStats(id=1, word_id=1)
        assert stats.word_id == 1
