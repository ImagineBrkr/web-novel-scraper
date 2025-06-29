import pytest
from unittest.mock import Mock, patch
from web_novel_scraper.request_manager import get_html_content, ValidationError, NetworkError
from urllib.parse import urlparse
import json


@pytest.fixture
def mock_http_response():
    """Create a mock HTTP response."""
    mock = Mock()
    mock.ok = True
    mock.text = "<html><body>Test content</body></html>"
    return mock


@pytest.fixture
def mock_flaresolver_response():
    """Create a mock FlareSolver response."""
    mock = Mock()
    mock.ok = True
    mock.json.return_value = {
        "solution": {
            "response": "<html><body>FlareSolver content</body></html>"
        }
    }
    return mock


def test_invalid_url():
    """Test that invalid URLs raise ValidationError."""
    invalid_urls = [
        "",
        "not-a-url",
        "http://",
        None
    ]

    for url in invalid_urls:
        with pytest.raises(ValidationError):
            get_html_content(url)


@patch('web_novel_scraper.request_manager._get_request')
def test_successful_http_request(mock_get, mock_http_response):
    """Test successful HTTP request without FlareSolver."""
    url = "https://example.com"
    mock_get.return_value = mock_http_response

    result = get_html_content(url, force_flaresolver=False)

    assert result == mock_http_response.text
    mock_get.assert_called_once()


@patch('web_novel_scraper.request_manager._get_request')
@patch('web_novel_scraper.request_manager._get_request_flaresolver')
def test_fallback_to_flaresolver(mock_flare, mock_get,
                                 mock_http_response, mock_flaresolver_response):
    """Test fallback to FlareSolver when HTTP request fails."""
    url = "https://example.com"
    mock_http_response.ok = False
    mock_get.return_value = mock_http_response
    mock_flare.return_value = mock_flaresolver_response

    result = get_html_content(url)

    assert result == mock_flaresolver_response.json()['solution']['response']
    mock_get.assert_called_once()
    mock_flare.assert_called_once()


@patch('web_novel_scraper.request_manager._get_request_flaresolver')
def test_force_flaresolver(mock_flare,  mock_flaresolver_response):
    """Test forced FlareSolver usage."""
    url = "https://example.com"
    mock_flare.return_value = mock_flaresolver_response

    result = get_html_content(url, force_flaresolver=True)

    assert result == mock_flaresolver_response.json()['solution']['response']
    mock_flare.assert_called_once()


@patch('web_novel_scraper.request_manager._get_request')
@patch('web_novel_scraper.request_manager._get_request_flaresolver')
def test_all_requests_fail(mock_flare, mock_get):
    """Test that NetworkError is raised when all requests fail."""
    url = "https://example.com"

    mock_response = Mock()
    mock_response.ok = False
    mock_get.return_value = mock_response
    mock_flare.return_value = mock_response

    with pytest.raises(NetworkError):
        get_html_content(url)


@patch('web_novel_scraper.request_manager._get_request_flaresolver')
def test_invalid_flaresolver_response(mock_flare):
    """Test handling of invalid FlareSolver JSON response."""
    url = "https://example.com"
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    mock_flare.return_value = mock_response

    with pytest.raises(NetworkError):
        get_html_content(url, force_flaresolver=True)


@patch('web_novel_scraper.request_manager._get_request_flaresolver')
def test_empty_flaresolver_solution(mock_flare):
    """Test handling of FlareSolver response without solution."""
    url = "https://example.com"
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {"solution": {}}  # No response field
    mock_flare.return_value = mock_response

    with pytest.raises(NetworkError):
        get_html_content(url, force_flaresolver=True)
