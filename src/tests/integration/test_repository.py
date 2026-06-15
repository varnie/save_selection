"""Integration tests for repository."""


class TestWordRepositoryIntegration:
    """Integration tests for WordRepository."""

    def test_word_crud_full_cycle(self, word_repo):
        """Test full CRUD cycle."""
        # Create
        word = word_repo.add("testword")
        assert word.phrase == "testword"

        # Read
        found = word_repo.get_by_phrase("testword")
        assert found is not None
        assert found.phrase == "testword"

        # Update
        word_repo.update_word(word.id, "updatedword")
        updated = word_repo.get_by_phrase("updatedword")
        assert updated is not None

        # Delete
        word_repo.delete_by_id(word.id)
        deleted = word_repo.get_by_phrase("updatedword")
        assert deleted is None

    def test_delete_translation(self, word_repo):
        """Test deleting translation."""
        word = word_repo.add("todelete")
        word_repo.add_translation(word.id, "удалить", "ru")

        word_repo.delete_translation(word.id, "ru")

        translation = word_repo.get_translation(word.id, "ru")
        assert translation is None

    def test_stats_recording(self, word_repo, stats_repo):
        """Test recording review stats."""
        word = word_repo.add("statstest")

        stats_repo.update_word_stats(word.id, interval_days=5, ease_factor=2.5)
        record = stats_repo.get_word_stats(word.id)

        assert record is not None
        assert record.interval_days == 5
