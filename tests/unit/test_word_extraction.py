from src.wiki_client import WikiFrequencyCounter


class TestWordExtraction:
    """Test word extraction from HTML content using real Wikipedia HTML."""

    def test_calculate_frequency(self):
        """Test frequency calculation."""
        from collections import Counter

        wiki = WikiFrequencyCounter("Test", 1)
        wiki.word_counter = Counter(["python", "is", "great", "python", "is", "python"])

        result = wiki.calculate_frequency()

        assert result["python"]["count"] == 3
        assert result["is"]["count"] == 2
        assert result["great"]["count"] == 1
        assert abs(result["python"]["percentage"] - 50.0) < 0.1
        assert abs(result["is"]["percentage"] - 33.33) < 0.1

    def test_calculate_frequency_empty(self):
        """Test frequency calculation with no words."""
        from collections import Counter

        wiki = WikiFrequencyCounter("Test", 1)
        wiki.word_counter = Counter()

        result = wiki.calculate_frequency()

        assert result == {}
