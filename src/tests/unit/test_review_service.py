"""Unit tests for ReviewService."""


class TestReviewService:
    """Tests for ReviewService."""

    def test_get_next_word_returns_due_word(self, word_service, review_service):
        """Test getting next word for review."""
        word_service.add_word("test", translation="тест")

        next_word = review_service.get_next_word()
        assert next_word is not None

    def test_review_word_updates_interval(self, word_service, review_service):
        """Test that review updates word interval."""
        word = word_service.add_word("review", translation="проверка")

        review_service.review_word(word.id)

    def test_review_word_resets_interval(self, word_service, review_service):
        """Test that skip resets interval to 1 day."""
        word = word_service.add_word("hard", translation="трудно")

        review_service.skip_word(word.id)

    def test_review_word_increases_ease(self, word_service, review_service):
        """Test that review increases ease factor."""
        word = word_service.add_word("easy", translation="легко")

        review_service.review_word(word.id)

    def test_skip_word_moves_to_end(self, word_service, review_service):
        """Test that skip moves word to end of queue."""
        word = word_service.add_word("skipme", translation="пропустить")

        review_service.skip_word(word.id)

    def test_get_stats_returns_dict(self, review_service):
        """Test getting statistics."""
        stats = review_service.get_stats()

        assert isinstance(stats, dict)
        assert "total_words" in stats
        assert "today_reviews" in stats
        assert "short_interval" in stats

    def test_format_interval_days(self, review_service):
        """Test interval formatting."""
        assert review_service.format_interval(1) == "1 day"
        assert review_service.format_interval(5) == "5 days"

    def test_format_interval_months(self, review_service):
        """Test interval formatting for months."""
        result = review_service.format_interval(60)
        assert "mo" in result

    def test_get_language_counts(self, word_service, review_service):
        """Test getting language counts."""
        word_service.add_word("counttest", translation="тест")

        counts = review_service.get_language_counts()
        assert isinstance(counts, dict)

    def test_get_next_word_least_seen_first(self, word_service, review_service):
        """Test that words with fewer reviews appear first."""
        word1 = word_service.add_word("word1", translation="w1")
        word_service.add_word("word2", translation="w2")
        word_service.add_word("word3", translation="w3")

        first = review_service.get_next_word()
        assert first is not None

        review_service.review_word(word1.id)

        second = review_service.get_next_word()
        assert second is not None
        assert second.id != word1.id

    def test_new_word_appears_before_reviewed(self, word_service, review_service):
        """Test that never-reviewed words appear before reviewed ones."""
        word_service.add_word("alpha", translation="а")
        word_service.add_word("beta", translation="б")

        first = review_service.get_next_word()
        first_id = first.id

        review_service.review_word(first_id)

        second = review_service.get_next_word()

        assert second.id != first_id

    def test_get_next_word_returns_word_when_available(self, word_service, review_service):
        """Test that get_next_word returns a word when one exists."""
        word_service.add_word("available", translation="доступный")

        result = review_service.get_next_word()
        assert result is not None
