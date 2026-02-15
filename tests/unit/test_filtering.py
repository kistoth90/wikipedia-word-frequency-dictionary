import pytest
from utils.filters import filter_by_ignore_list, filter_by_percentile


class TestFiltering:
    """Test filtering methods."""

    def test_filter_by_ignore_list_basic(self, sample_frequency_dict):
        """Test basic ignore list filtering."""
        ignore_list = ["is", "a", "the"]

        result = filter_by_ignore_list(sample_frequency_dict, ignore_list)

        assert "is" not in result
        assert "a" not in result
        assert "python" in result
        assert "programming" in result

    def test_filter_by_ignore_list_case_insensitive(self, sample_frequency_dict):
        """Test that ignore list is case-insensitive."""
        ignore_list = ["PYTHON", "Programming"]

        result = filter_by_ignore_list(sample_frequency_dict, ignore_list)

        assert "python" not in result
        assert "programming" not in result

    def test_filter_by_ignore_list_empty(self, sample_frequency_dict):
        """Test filtering with empty ignore list."""
        result = filter_by_ignore_list(sample_frequency_dict, [])

        assert len(result) == len(sample_frequency_dict)

    def test_filter_by_percentile_90(self, sample_frequency_dict):
        """Test percentile filtering at 90th percentile."""
        result = filter_by_percentile(sample_frequency_dict, 90)

        # Should keep only top 10% (highest frequency words)
        assert "python" in result  # 21.43%
        assert len(result) <= 2  # Top words only

    def test_filter_by_percentile_50(self, sample_frequency_dict):
        """Test percentile filtering at 50th percentile."""
        result = filter_by_percentile(sample_frequency_dict, 50)

        # Should keep top 50%
        assert len(result) >= len(sample_frequency_dict) // 2

    def test_filter_by_percentile_0(self, sample_frequency_dict):
        """Test percentile filtering at 0 (keep all)."""
        result = filter_by_percentile(sample_frequency_dict, 0)

        assert len(result) == len(sample_frequency_dict)

    def test_filter_by_percentile_100(self, sample_frequency_dict):
        """Test percentile filtering at 100 (keep only max)."""
        result = filter_by_percentile(sample_frequency_dict, 100)

        # Should keep only words at maximum percentage
        assert len(result) >= 1
        # All kept words should have the maximum percentage
        if result:
            max_pct = max(stats["percentage"] for stats in result.values())
            for stats in result.values():
                assert stats["percentage"] == max_pct

    def test_filter_by_percentile_empty_dict(self):
        """Test percentile filtering on empty dictionary."""
        result = filter_by_percentile({}, 50)

        assert len(result) == 0

    def test_combined_filtering(self, sample_frequency_dict):
        """Test combining ignore list and percentile filtering."""
        # First apply ignore list
        result = filter_by_ignore_list(sample_frequency_dict, ["is", "a"])

        # Then apply percentile
        result = filter_by_percentile(result, 50)

        # Should not contain ignored words
        assert "is" not in result
        assert "a" not in result

        # Should be filtered by percentile
        assert len(result) < len(sample_frequency_dict)
