import pytest
from fastapi import status
from unittest.mock import patch, AsyncMock


class TestEndpoints:
    """Test API endpoints."""
    
    def test_word_frequency_endpoint_success(self, test_client, sample_frequency_dict):
        """Test /word-frequency endpoint with valid parameters."""
        with patch('src.wiki_client.WikiFrequencyCounter.run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = sample_frequency_dict
            
            response = test_client.get("/word-frequency?article=Python&depth=1")
            
            assert response.status_code == status.HTTP_200_OK
            assert "python" in response.json()
    
    def test_word_frequency_endpoint_missing_params(self, test_client):
        """Test /word-frequency endpoint with missing parameters."""
        response = test_client.get("/word-frequency")
        
        assert response.status_code == 422  # Validation error
    
    def test_word_frequency_endpoint_invalid_depth(self, test_client):
        """Test /word-frequency endpoint with invalid depth."""
        response = test_client.get("/word-frequency?article=Python&depth=0")
        
        assert response.status_code == 422
    
    def test_word_frequency_endpoint_rejects_url(self, test_client):
        """Test that endpoint rejects full URLs."""
        response = test_client.get(
            "/word-frequency?article=https://hu.wikipedia.org/wiki/Python&depth=1"
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "URL" in response.json()["detail"]["message"]
    
    def test_keywords_endpoint_success(self, test_client, sample_frequency_dict):
        """Test /keywords endpoint with valid parameters."""
        with patch('src.wiki_client.WikiFrequencyCounter.run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = sample_frequency_dict
            
            payload = {
                "article": "Python",
                "depth": 1,
                "ignore_list": ["is", "a"],
                "percentile": 50
            }
            
            response = test_client.post("/keywords", json=payload)
            
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert "is" not in result
            assert "a" not in result
    
    def test_keywords_endpoint_empty_ignore_list(self, test_client, sample_frequency_dict):
        """Test /keywords endpoint with empty ignore list."""
        with patch('src.wiki_client.WikiFrequencyCounter.run', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = sample_frequency_dict
            
            payload = {
                "article": "Python",
                "depth": 1,
                "ignore_list": [],
                "percentile": 0
            }
            
            response = test_client.post("/keywords", json=payload)
            
            assert response.status_code == status.HTTP_200_OK
    
    def test_keywords_endpoint_invalid_percentile(self, test_client):
        """Test /keywords endpoint with invalid percentile."""
        payload = {
            "article": "Python",
            "depth": 1,
            "ignore_list": [],
            "percentile": 150  # Invalid
        }
        
        response = test_client.post("/keywords", json=payload)
        
        assert response.status_code == 422
    
    def test_keywords_endpoint_rejects_url(self, test_client):
        """Test that /keywords endpoint rejects full URLs."""
        payload = {
            "article": "https://hu.wikipedia.org/wiki/Python",
            "depth": 1,
            "ignore_list": [],
            "percentile": 50
        }
        
        response = test_client.post("/keywords", json=payload)
        
        assert response.status_code == 422
        assert "URL" in str(response.json())
