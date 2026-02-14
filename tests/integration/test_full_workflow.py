import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.wiki_client import WikiFrequencyCounter
from utils.filters import filter_by_ignore_list, filter_by_percentile


def _make_mock_client(mock_get):
    """Create a mock httpx.AsyncClient with the given .get method."""
    client = MagicMock()
    client.get = mock_get
    client.aclose = AsyncMock()
    return client


class TestFullWorkflow:
    """Integration tests for complete workflows using real HTML."""

    @pytest.mark.asyncio
    async def test_complete_workflow_gyorzamoly_depth_1(self, gyorzamoly_html):
        """Test complete workflow with real Hungarian Wikipedia HTML."""
        wiki = WikiFrequencyCounter("Győrzámoly", 1)

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = gyorzamoly_html

        mock_get = AsyncMock(return_value=mock_response)
        mock_client = _make_mock_client(mock_get)

        with patch.object(wiki, '_open_client', new_callable=AsyncMock) as mock_open:
            mock_open.side_effect = lambda: setattr(wiki, '_client', mock_client)

            result = await wiki.run()

            # Verify we got real results
            assert len(result) > 50  # Should have many unique words

            # Verify specific Hungarian words from the article
            assert "győrzámoly" in result
            assert "község" in result
            assert "magyarország" in result

            # Verify frequency structure
            for word, stats in result.items():
                assert "count" in stats
                assert "percentage" in stats
                assert isinstance(stats["count"], int)
                assert isinstance(stats["percentage"], float)
                assert stats["count"] > 0
                assert 0 < stats["percentage"] <= 100

    @pytest.mark.asyncio
    async def test_complete_workflow_msci_depth_1(self, msci_html):
        """Test complete workflow with real English Wikipedia HTML."""
        wiki = WikiFrequencyCounter("MSCI", 1)

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = msci_html

        mock_get = AsyncMock(return_value=mock_response)
        mock_client = _make_mock_client(mock_get)

        with patch.object(wiki, '_open_client', new_callable=AsyncMock) as mock_open:
            mock_open.side_effect = lambda: setattr(wiki, '_client', mock_client)

            result = await wiki.run()

            # Verify we got real results
            assert len(result) > 50

            # Verify specific English words
            assert "msci" in result
            assert "morgan" in result
            assert "stanley" in result

    @pytest.mark.asyncio
    async def test_complete_workflow_with_filtering(self, gyorzamoly_html):
        """Test complete workflow with filtering."""
        wiki = WikiFrequencyCounter("Győrzámoly", 1)

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = gyorzamoly_html

        mock_get = AsyncMock(return_value=mock_response)
        mock_client = _make_mock_client(mock_get)

        with patch.object(wiki, '_open_client', new_callable=AsyncMock) as mock_open:
            mock_open.side_effect = lambda: setattr(wiki, '_client', mock_client)

            # Get base frequency
            result = await wiki.run()

            # Apply filters
            filtered = filter_by_ignore_list(result, ["a", "az", "és"])
            filtered = filter_by_percentile(filtered, 50)

            # Verify filtering worked
            assert "a" not in filtered
            assert "az" not in filtered
            assert "és" not in filtered
            assert len(filtered) <= len(result)

    @pytest.mark.asyncio
    async def test_depth_2_with_different_articles(self, gyorzamoly_html, msci_html):
        """Test depth 2 with different HTML for each article."""
        wiki = WikiFrequencyCounter("Győrzámoly", 2)

        call_count = 0

        async def mock_get_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            mock_response = AsyncMock()
            mock_response.status_code = 200

            # First call gets Hungarian HTML, rest get English HTML
            if call_count == 1:
                mock_response.text = gyorzamoly_html
            else:
                mock_response.text = msci_html

            return mock_response

        mock_get = AsyncMock(side_effect=mock_get_side_effect)
        mock_client = _make_mock_client(mock_get)

        with patch.object(wiki, '_open_client', new_callable=AsyncMock) as mock_open:
            mock_open.side_effect = lambda: setattr(wiki, '_client', mock_client)

            result = await wiki.run()

            # Should have fetched multiple articles
            assert call_count > 1

            # Should have combined words from multiple articles
            assert len(result) > 100

            # Should have words from both Hungarian and English articles
            assert "győrzámoly" in result  # From Hungarian article
