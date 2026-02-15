import pytest
from pathlib import Path
from unittest.mock import Mock
from fastapi.testclient import TestClient
from main import app

TEST_FILE_PATH = Path(__file__).parent / "sites"


@pytest.fixture
def test_client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def gyorzamoly_html():
    filepath = TEST_FILE_PATH / "Győrzámoly – Wikipédia.html"
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def msci_html():
    filepath = TEST_FILE_PATH / "MSCI - Wikipedia.html"
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def mock_httpx_response():
    def _create_response(status_code=200, text=""):
        response = Mock()
        response.status_code = status_code
        response.text = text
        return response

    return _create_response


@pytest.fixture
def sample_frequency_dict():
    return {
        "python": {"count": 3, "percentage": 21.43},
        "programming": {"count": 2, "percentage": 14.29},
        "is": {"count": 2, "percentage": 14.29},
        "a": {"count": 1, "percentage": 7.14},
        "language": {"count": 1, "percentage": 7.14},
        "widely": {"count": 1, "percentage": 7.14},
        "used": {"count": 1, "percentage": 7.14},
        "many": {"count": 1, "percentage": 7.14},
        "developers": {"count": 1, "percentage": 7.14},
        "love": {"count": 1, "percentage": 7.14},
    }
