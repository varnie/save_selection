"""Unit tests for WordManagementService."""


import pytest


class TestWordManagementService:
    """Tests for WordManagementService."""

    def test_add_word_success(self, word_service):
        """Test adding a new word successfully."""
        word = word_service.add_word("hello", translation="привет")
        assert word.phrase == "hello"
        assert word.translation == "привет"

    def test_add_word_duplicate_adds_translation(self, word_service):
        """Test adding duplicate word adds translation."""
        word_service.add_word("hello", translation="привет")

        # Add another translation to existing word
        word = word_service.add_word("hello", translation="хай")
        assert word.phrase == "hello"
        assert word.translation == "хай"

    def test_add_word_empty_raises_value_error(self, word_service):
        """Test that empty phrase raises ValueError."""
        with pytest.raises(ValueError, match="Phrase cannot be empty"):
            word_service.add_word("")

    def test_add_word_whitespace_raises(self, word_service):
        """Test that whitespace-only phrase raises ValueError."""
        with pytest.raises(ValueError, match="Phrase cannot be empty"):
            word_service.add_word("   ")

    def test_add_word_auto_translate(self, word_service):
        """Test auto-translate using mock service."""
        word = word_service.add_word("hello", auto_translate=True)
        assert word.phrase == "hello"

    def test_get_words_returns_all(self, word_service):
        """Test getting all words."""
        word_service.add_word("word1", translation="слово1")
        word_service.add_word("word2", translation="слово2")

        words = word_service.get_words()
        assert len(words) >= 2

    def test_get_words_with_search(self, word_service):
        """Test getting words with search filter."""
        word_service.add_word("apple", translation="яблоко")
        word_service.add_word("banana", translation="банан")

        words = word_service.get_words(search="apple")
        assert len(words) >= 1
        assert words[0].phrase == "apple"

    def test_delete_word(self, word_service):
        """Test deleting a word."""
        word_service.add_word("todelete", translation="удалить")
        word_service.delete_word("todelete")

        words = word_service.get_words(search="todelete")
        assert len(words) == 0

    def test_delete_word_by_id(self, word_service):
        """Test deleting word by ID."""
        word = word_service.add_word("byid", translation="по id")
        word_service.delete_word_by_id(word.id)

        words = word_service.get_words(search="byid")
        assert len(words) == 0

    def test_update_word(self, word_service):
        """Test updating word."""
        word = word_service.add_word("old", translation="старый")
        word_service.update_word(word.id, "new", translation="новый")

        updated = word_service.get_word("new")
        assert updated is not None
        assert updated.translation == "новый"

    def test_get_translation(self, word_service):
        """Test getting translation."""
        word = word_service.add_word("test", translation="тест")
        translation = word_service.get_translation(word.id)
        assert translation == "тест"

    def test_get_language_abbreviation(self, word_service):
        """Test getting language abbreviation."""
        abbrev = word_service.get_language_abbreviation("ru")
        assert abbrev == "RU"
