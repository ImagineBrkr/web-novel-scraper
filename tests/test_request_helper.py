import pytest
import requests
from unittest.mock import Mock, patch

from web_novel_scraper.request_helper import RequestHelper
from web_novel_scraper.exceptions import (
    CommonGetRequestError,
    FlaresolverrConnectionError,
    FlaresolverrRequestError,
    InvalidURLError,
    ResponseIsEmptyError,
)


@pytest.fixture
def helper():
    return RequestHelper(
        request_timeout=30,
        time_between_retries=0,
        retries_number=3,
        cookies={"cookie1": "value1"},
    )


class TestValidateUrl:
    def test_valid_url(self):
        RequestHelper._validate_url("https://example.com")

    def test_invalid_url(self):
        with pytest.raises(InvalidURLError):
            RequestHelper._validate_url("not-a-url")


class TestCommonRequests:
    @patch("web_novel_scraper.request_helper.requests.get")
    def test_common_request_success(self, mock_get, helper):
        response = Mock()
        response.status_code = 200
        response.text = "<html>hello</html>"
        response.raise_for_status.return_value = None

        mock_get.return_value = response

        result = helper.get_url_content("https://example.com")

        assert result == "<html>hello</html>"
        mock_get.assert_called_once()

    @patch("web_novel_scraper.request_helper.requests.get")
    def test_common_request_empty_response(self, mock_get, helper):
        response = Mock()
        response.status_code = 200
        response.text = ""
        response.raise_for_status.return_value = None

        mock_get.return_value = response

        with pytest.raises(ResponseIsEmptyError):
            helper.get_url_content("https://example.com")

    @patch("web_novel_scraper.request_helper.requests.get")
    def test_common_request_http_error(self, mock_get, helper):
        mock_get.side_effect = requests.exceptions.HTTPError("404")

        with pytest.raises(CommonGetRequestError):
            helper.get_url_content("https://example.com")

    @patch("web_novel_scraper.request_helper.requests.get")
    def test_common_request_invalid_schema(self, mock_get, helper):
        mock_get.side_effect = requests.exceptions.InvalidSchema(
            "No connection adapters"
        )

        with pytest.raises(InvalidURLError):
            helper.get_url_content("https://example.com")

    @patch("web_novel_scraper.request_helper.requests.get")
    def test_common_request_retries_until_success(self, mock_get, helper):
        success_response = Mock()
        success_response.status_code = 200
        success_response.text = "success"
        success_response.raise_for_status.return_value = None

        mock_get.side_effect = [
            requests.exceptions.ConnectionError(),
            success_response,
        ]

        result = helper.get_url_content("https://example.com")

        assert result == "success"
        assert mock_get.call_count == 2

    @patch("web_novel_scraper.request_helper.requests.get")
    def test_common_request_all_retries_fail(self, mock_get, helper):
        mock_get.side_effect = requests.exceptions.ConnectionError()

        with pytest.raises(CommonGetRequestError):
            helper.get_url_content("https://example.com")

        assert mock_get.call_count == helper.retries_number


class TestFlareSolverr:
    def test_enable_flaresolverr(self, helper):
        helper.enable_flaresolverr("http://localhost:8191")

        assert helper.use_flaresolverr is True
        assert helper.flaresolverr_url == "http://localhost:8191"
        assert helper.flaresolverr_session_id is None

    @patch("web_novel_scraper.request_helper.requests.post")
    def test_initialize_flaresolverr(self, mock_post, helper):
        helper.enable_flaresolverr("http://localhost:8191")

        helper._initialize_flaresolverr()

        assert helper.flaresolverr_session_id is not None

        mock_post.assert_called_once()

    @patch("web_novel_scraper.request_helper.requests.post")
    def test_initialize_flaresolverr_only_once(self, mock_post, helper):
        helper.enable_flaresolverr("http://localhost:8191")

        helper._initialize_flaresolverr()
        session_id = helper.flaresolverr_session_id

        helper._initialize_flaresolverr()

        assert helper.flaresolverr_session_id == session_id
        assert mock_post.call_count == 1

    @patch("web_novel_scraper.request_helper.requests.post")
    def test_initialize_flaresolverr_connection_error(self, mock_post, helper):
        helper.enable_flaresolverr("http://localhost:8191")

        mock_post.side_effect = requests.exceptions.ConnectionError()

        with pytest.raises(FlaresolverrConnectionError):
            helper._initialize_flaresolverr()

    @patch("web_novel_scraper.request_helper.requests.post")
    def test_flaresolverr_request_success(self, mock_post, helper):
        helper.enable_flaresolverr("http://localhost:8191")

        create_response = Mock()
        create_response.raise_for_status.return_value = None

        request_response = Mock()
        request_response.raise_for_status.return_value = None
        request_response.json.return_value = {
            "solution": {"response": "<html>content</html>"}
        }

        mock_post.side_effect = [
            create_response,
            request_response,
        ]

        result = helper.get_url_content("https://example.com")

        assert result == "<html>content</html>"
        assert helper.flaresolverr_session_id is not None

    @patch("web_novel_scraper.request_helper.requests.post")
    def test_flaresolverr_invalid_json(self, mock_post, helper):
        helper.retries_number = 1
        helper.enable_flaresolverr("http://localhost:8191")

        create_response = Mock()
        create_response.raise_for_status.return_value = None

        request_response = Mock()
        request_response.raise_for_status.return_value = None
        request_response.json.side_effect = requests.exceptions.JSONDecodeError(
            "invalid json", "test", 1
        )

        mock_post.side_effect = [
            create_response,
            request_response,
        ]

        with pytest.raises(FlaresolverrRequestError):
            helper.get_url_content("https://example.com")

    @patch("web_novel_scraper.request_helper.requests.post")
    def test_flaresolverr_empty_response(self, mock_post, helper):
        helper.retries_number = 1
        helper.enable_flaresolverr("http://localhost:8191")

        create_response = Mock()
        create_response.raise_for_status.return_value = None

        request_response = Mock()
        request_response.raise_for_status.return_value = None
        request_response.json.return_value = {"solution": {"response": ""}}

        mock_post.side_effect = [
            create_response,
            request_response,
        ]

        with pytest.raises(ResponseIsEmptyError):
            helper.get_url_content("https://example.com")

    @patch("web_novel_scraper.request_helper.requests.post")
    def test_post_cleanup_destroys_session(self, mock_post, helper):
        helper.enable_flaresolverr("http://localhost:8191")
        helper.flaresolverr_session_id = "abc"

        helper._post_cleanup()

        mock_post.assert_called_once()

    @patch("web_novel_scraper.request_helper.requests.post")
    def test_post_cleanup_without_session(self, mock_post, helper):
        helper._post_cleanup()

        mock_post.assert_not_called()


class TestContextManager:
    @patch.object(RequestHelper, "_post_cleanup")
    def test_context_manager_calls_cleanup(self, mock_cleanup):
        with RequestHelper(
            request_timeout=30,
            time_between_retries=0,
            retries_number=1,
            cookies={},
        ):
            pass

        mock_cleanup.assert_called_once()
