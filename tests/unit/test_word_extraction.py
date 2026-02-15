import pytest
from src.wiki_client import WikiFrequencyCounter


class TestWordExtraction:
    """Test word extraction from HTML content using real Wikipedia HTML."""

    def test_extract_words_from_gyorzamoly(self, gyorzamoly_html):
        """Test word extraction from real Hungarian Wikipedia article."""
        wiki = WikiFrequencyCounter("Győrzámoly", 1)
        wiki.extract_words_from_html(gyorzamoly_html)

        # Should have extracted many words
        total_words = sum(wiki.word_counter.values())
        assert total_words > 100

        # Check for expected Hungarian words
        words_lower = list(wiki.word_counter.keys())
        assert "győrzámoly" in words_lower
        assert "község" in words_lower
        assert "magyarország" in words_lower

    def test_extract_words_from_msci(self, msci_html):
        """Test word extraction from real English Wikipedia article."""
        wiki = WikiFrequencyCounter("MSCI", 1)
        wiki.extract_words_from_html(msci_html)

        # Should have extracted many words
        total_words = sum(wiki.word_counter.values())
        assert total_words > 100

        # Check for expected English words
        words_lower = list(wiki.word_counter.keys())
        assert "msci" in words_lower
        assert "morgan" in words_lower
        assert "stanley" in words_lower

    def test_extract_words_empty_html(self):
        """Test extraction from empty HTML."""
        wiki = WikiFrequencyCounter("Test", 1)
        wiki.extract_words_from_html("<html></html>")

        assert len(wiki.word_counter) == 0

    def test_extract_words_no_content_div(self):
        """Test extraction when mw-content-text div is missing."""
        wiki = WikiFrequencyCounter("Test", 1)
        html = "<html><body><p>Some text</p></body></html>"
        wiki.extract_words_from_html(html)

        assert len(wiki.word_counter) == 0

    def test_extract_words_hungarian_characters(self):
        """Test extraction of Hungarian characters."""
        wiki = WikiFrequencyCounter("Test", 1)
        html = """
        <div id="mw-content-text">
            <p>Árvíztűrő tükörfúrógép</p>
        </div>
        """
        wiki.extract_words_from_html(html)

        assert len(wiki.word_counter) == 2
        assert "árvíztűrő" in wiki.word_counter
        assert "tükörfúrógép" in wiki.word_counter

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
