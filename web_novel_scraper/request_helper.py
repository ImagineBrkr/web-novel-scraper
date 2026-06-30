import requests
import random
import time

from dotenv import load_dotenv
from urllib.parse import urlparse

from web_novel_scraper.logger_manager import create_logger
from web_novel_scraper.exceptions import (
    CommonGetRequestError,
    FlaresolverrConnectionError,
    FlaresolverrRequestError,
    InvalidURLError,
    ResponseIsEmptyError,
)

logger = create_logger(__name__)


load_dotenv()
_FLARE_HEADERS = {"Content-Type": "application/json"}


def _dict_to_cookie_list(cookies: dict) -> list:
    return [{"name": k, "value": v} for k, v in cookies.items()]


class RequestHelper:
    request_timeout: int
    time_between_retries: int
    retries_number: int
    time_between_requests: int
    request_cookies: dict
    use_flaresolverr: bool = False
    flaresolverr_url: str = None
    flaresolverr_session_id: str = None
    _last_request_time: float = None

    def __init__(
        self,
        request_timeout: int,
        time_between_retries: int,
        retries_number: int,
        cookies: dict,
        time_between_requests: int,
    ):
        self.request_timeout = request_timeout
        self.time_between_retries = time_between_retries
        self.retries_number = retries_number
        self.request_cookies = cookies
        self.time_between_requests = time_between_requests
        self._last_request_time = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._post_cleanup()
        return False

    # Only Enables it, a session won't be created until the first Request
    def enable_flaresolverr(self, flaresolverr_url: str) -> None:
        self.use_flaresolverr = True
        self.flaresolverr_url = flaresolverr_url

    def get_url_content(self, url: str) -> str:
        RequestHelper._validate_url(url=url)
        self._throttle_request()

        for attempt in range(self.retries_number):
            last_exception = None
            try:
                if self.use_flaresolverr:
                    response_content = self._get_url_flaresolverr_request(url=url)
                else:
                    response_content = self._get_url_common_request(url=url)
                break
            except (
                CommonGetRequestError,
                FlaresolverrConnectionError,
                FlaresolverrRequestError,
                ResponseIsEmptyError,
            ) as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")

                if attempt < self.retries_number - 1:
                    logger.debug(
                        f"Waiting {self.time_between_retries} seconds before retrying..."
                    )
                    time.sleep(self.time_between_retries)

        if last_exception is not None:
            raise last_exception

        logger.info(f"Succesfully received HTML Content from URL {url}.")
        self._last_request_time = time.monotonic()
        return response_content

    def _throttle_request(self) -> None:
        if self.time_between_requests <= 0:
            return
        if self._last_request_time is not None:
            elapsed = time.monotonic() - self._last_request_time
            remaining = self.time_between_requests - elapsed
            if remaining > 0:
                logger.debug(
                    f"Waiting {remaining:.2f} seconds before making the next request..."
                )
                time.sleep(remaining)

    # This method will actually create the Session of FlareSolverr if it's activated
    def _initialize_flaresolverr(self) -> None:
        if not self.use_flaresolverr:
            return

        if self.flaresolverr_session_id is not None:
            return

        RequestHelper._validate_url(url=self.flaresolverr_url)

        flaresolverr_session_id = chr(int(random.uniform(97, 122)))
        logger.debug(
            f'Requests will use Flaresolverr on URL "{self.flaresolverr_url}", session "{flaresolverr_session_id}".'
        )
        try:
            requests.post(
                f"{self.flaresolverr_url}/v1",
                headers=_FLARE_HEADERS,
                json={
                    "cmd": "sessions.create",
                    "session": flaresolverr_session_id,
                },
                timeout=self.request_timeout,
            )
            self.flaresolverr_session_id = flaresolverr_session_id
        except requests.exceptions.ConnectionError:
            raise FlaresolverrConnectionError(
                f'Could not connect to FlareSolverr on URL "{self.flaresolverr_url}" and session "{flaresolverr_session_id}" was not created.'
            )

    def _post_cleanup(self) -> None:
        if self.flaresolverr_session_id is None:
            return

        logger.debug(
            f'Deleting FlareSolverr Session "{self.flaresolverr_session_id}" using URL "{self.flaresolverr_url}".'
        )
        try:
            requests.post(
                f"{self.flaresolverr_url}/v1",
                headers=_FLARE_HEADERS,
                json={
                    "cmd": "sessions.destroy",
                    "session": self.flaresolverr_session_id,
                },
                timeout=self.request_timeout,
            )
        except requests.exceptions.ConnectionError:
            logger.warning(
                f'Could not connect to FlareSolverr on URL "{self.flaresolverr_url}", Chromium process may still exists and has to be manually deleted.'
            )

    @staticmethod
    def _validate_url(url: str) -> str:
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            raise InvalidURLError(f"URL is invalid: {url}")

    def _get_url_common_request(self, url: str) -> str:
        logger.debug(f'Attempting common get Request for URL "{url}".')
        try:
            response = requests.get(
                url, timeout=self.request_timeout, cookies=self.request_cookies
            )
            response.raise_for_status()
        except requests.exceptions.InvalidSchema as e:
            raise InvalidURLError(f'Invalid Schema for URL "{url}": {str(e)}')
        except requests.exceptions.RequestException as e:
            raise CommonGetRequestError(f'Request Failed for URL "{url}": {str(e)} ')

        if response.status_code != 200:
            raise CommonGetRequestError(
                f'Request Failed for URL "{url}", Status Code is {response.status_code}.'
            )

        response_content = response.text
        if response_content == "":
            raise ResponseIsEmptyError(f'Request for URL "{url}" returned no content.')

        logger.debug(f'Received response with status 200 from URL "{url}"')
        return response_content

    def _get_url_flaresolverr_request(self, url: str) -> str:
        self._initialize_flaresolverr()
        logger.debug(f'Attempting Flaresolverr Request for URL "{url}"')
        try:
            response = requests.post(
                f"{self.flaresolverr_url}/v1",
                headers=_FLARE_HEADERS,
                json={
                    "cmd": "request.get",
                    "session": self.flaresolverr_session_id,
                    "url": url,
                    "maxTimeout": self.request_timeout * 1000,
                    "cookies": _dict_to_cookie_list(self.request_cookies)
                    if self.request_cookies
                    else [],
                },
                timeout=self.request_timeout,
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise FlaresolverrConnectionError(
                f'Could not connect to FlareSolverr on URL "{self.flaresolverr_url}"'
            )
        except requests.exceptions.RequestException as e:
            raise FlaresolverrRequestError(
                f'Request Failed for URL "{url}" using FlareSolverr: {str(e)} '
            )

        try:
            response_json = response.json()
        except requests.exceptions.JSONDecodeError as e:
            raise FlaresolverrRequestError(
                f'Invalid FlareSolver response for "{url}": {str(e)}'
            )

        response_content = response_json.get("solution", {}).get("response")
        if response_content is None or response_content == "":
            raise ResponseIsEmptyError(
                f'Request for URL "{url}" using Flaresolverr returned no content.'
            )

        logger.debug(
            f'Received response with status 200 from URL "{url}" using Flaresolverr.'
        )
        return response_content
