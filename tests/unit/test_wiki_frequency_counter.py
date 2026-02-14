import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.wiki_client import WikiFrequencyCounter


def _make_mock_client(mock_get):
    """Create a mock httpx.AsyncClient with the given .get method."""
    client = MagicMock()
    client.get = mock_get
    client.aclose = AsyncMock()
    return client


class TestWikiFrequencyCounter:
    """Test WikiFrequencyCounter class with mocked HTTP but real HTML processing."""

    @pytest.mark.asyncio
    async def test_get_article_source_success(self, gyorzamoly_html):
        """Test successful article fetching."""
        wiki = WikiFrequencyCounter("Győrzámoly", 1)

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = gyorzamoly_html

        mock_get = AsyncMock(return_value=mock_response)
        wiki._client = _make_mock_client(mock_get)

        result = await wiki.get_article_source("Győrzámoly")

        assert result == gyorzamoly_html
        mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_article_source_404(self):
        """Test handling of 404 errors."""
        wiki = WikiFrequencyCounter("NonExistent", 1)

        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.text = ""

        mock_get = AsyncMock(return_value=mock_response)
        wiki._client = _make_mock_client(mock_get)

        result = await wiki.get_article_source("NonExistent")

        # Should return None for 404
        assert result is None

    @pytest.mark.asyncio
    async def test_run_depth_1_with_real_html(self, gyorzamoly_html):
        """Test run with depth 1 using real HTML fixture."""
        wiki = WikiFrequencyCounter("Győrzámoly", 1)

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = gyorzamoly_html

        mock_get = AsyncMock(return_value=mock_response)
        mock_client = _make_mock_client(mock_get)

        with patch.object(wiki, '_open_client', new_callable=AsyncMock) as mock_open:
            mock_open.side_effect = lambda: setattr(wiki, '_client', mock_client)

            result = await wiki.run()

            # Verify result structure
            assert isinstance(result, dict)
            assert len(result) > 0

            # Verify actual words from the article
            assert "győrzámoly" in result
            assert "község" in result

            # Verify frequency calculation
            for word, stats in result.items():
                assert "count" in stats
                assert "percentage" in stats
                assert stats["count"] > 0
                assert 0 < stats["percentage"] <= 100

            # Should only fetch one article at depth 1
            assert mock_get.call_count == 1

    @pytest.mark.asyncio
    async def test_run_depth_2_with_real_html(self, gyorzamoly_html):
        """Test run with depth 2 using real HTML."""
        wiki = WikiFrequencyCounter("Győrzámoly", 2)

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = gyorzamoly_html

        mock_get = AsyncMock(return_value=mock_response)
        mock_client = _make_mock_client(mock_get)

        with patch.object(wiki, '_open_client', new_callable=AsyncMock) as mock_open:
            mock_open.side_effect = lambda: setattr(wiki, '_client', mock_client)

            result = await wiki.run()

            # Should have fetched multiple articles
            assert mock_get.call_count > 1

            # Should have results
            assert isinstance(result, dict)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_run_avoids_duplicate_articles(self, gyorzamoly_html):
        """Test that run doesn't process the same article twice."""
        wiki = WikiFrequencyCounter("Győrzámoly", 3)

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = gyorzamoly_html

        mock_get = AsyncMock(return_value=mock_response)
        mock_client = _make_mock_client(mock_get)

        with patch.object(wiki, '_open_client', new_callable=AsyncMock) as mock_open:
            mock_open.side_effect = lambda: setattr(wiki, '_client', mock_client)

            await wiki.run()

            # Get all called URLs
            called_urls = [str(call[0][0]) for call in mock_get.call_args_list]

            # Count unique articles (extract article name from URL)
            called_articles = [url.split("/wiki/")[-1] for url in called_urls]

            # Should not have duplicates
            assert len(called_articles) == len(set(called_articles))

    @pytest.mark.asyncio
    async def test_run_handles_fetch_errors_gracefully(self):
        """Test that run continues when some articles fail to fetch."""
        wiki = WikiFrequencyCounter("Test", 2)

        call_count = 0

        async def mock_get_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            mock_response = AsyncMock()
            if call_count == 1:
                # First article succeeds
                mock_response.status_code = 200
                mock_response.text = """
                <div id="mw-content-text">
                    <p>Test article with words</p>
                    <a href="/wiki/Link1">Link1</a>
                </div>
                """
            else:
                # Subsequent articles fail
                mock_response.status_code = 404
                mock_response.text = ""

            return mock_response

        mock_get = AsyncMock(side_effect=mock_get_side_effect)
        mock_client = _make_mock_client(mock_get)

        with patch.object(wiki, '_open_client', new_callable=AsyncMock) as mock_open:
            mock_open.side_effect = lambda: setattr(wiki, '_client', mock_client)

            result = await wiki.run()

            # Should still return results from successful article
            assert isinstance(result, dict)
            assert "test" in result or "article" in result
