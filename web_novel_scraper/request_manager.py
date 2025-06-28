import requests
import os
import json
import time
from typing import Optional

from dotenv import load_dotenv
from urllib.parse import urlparse

from .logger_manager import create_logger
from .utils import ValidationError, NetworkError

load_dotenv()

FLARESOLVER_URL = os.getenv('SCRAPER_FLARESOLVER_URL', 'http://localhost:8191/v1')
FLARE_HEADERS = {'Content-Type': 'application/json'}
FORCE_FLARESOLVER = os.getenv('FORCE_FLARESOLVER', '0') == '1'

logger = create_logger('GET HTML CONTENT')


def _get_request(url: str,
                 timeout: int,
                 retries: int,
                 time_between_retries: int) -> Optional[requests.Response]:
    logger.debug(
        f'Starting get_request for "{url}" with timeout={timeout}, '
        f'retries={retries}, '
        f'time_between_retries={time_between_retries}')
    for attempt in range(retries):
        logger.debug(f'Attempt {attempt + 1} for "{url}"')
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            logger.debug(f'Successful response for "{url}" on attempt {attempt + 1}')
            return response
        except requests.exceptions.ConnectionError as e:
            logger.debug(f'Connection error ({attempt + 1}/{retries}): {e}')
        except requests.exceptions.Timeout as e:
            logger.debug(f'Request timed out ({attempt + 1}/{retries}): {e}')
        except requests.exceptions.HTTPError as e:
            logger.debug(f'HTTP error ({attempt + 1}/{retries}): {e}')
        except requests.exceptions.InvalidSchema as e:
            logger.debug(f'Invalid URL schema for "{url}": {e}')
        except requests.exceptions.RequestException as e:
            logger.debug(f'Request failed ({attempt + 1}/{retries}): {e}')

        if attempt < retries - 1:
            logger.debug(f'Waiting {time_between_retries} seconds before retrying')
            time.sleep(time_between_retries)  # Wait before retrying
    logger.debug(f'Failed to get a successful response for "{url}" after {retries} attempts using common HTTP Request')
    return None


def _get_request_flaresolver(url: str,
                             timeout: int,
                             retries: int,
                             time_between_retries: int,
                             flaresolver_url: str) -> Optional[requests.Response]:
    logger.debug(
        f'Starting get_request_flaresolver for "{url}" with timeout={timeout}, '
        f'retries={retries}, '
        f'time_between_retries={time_between_retries}')
    for attempt in range(retries):
        logger.debug(f'Attempt {attempt + 1} for "{url}" using FlareSolver')
        try:
            response = requests.post(
                flaresolver_url,
                headers=FLARE_HEADERS,
                json={
                    'cmd': 'request.get',
                    'url': url,
                    'maxTimeout': timeout * 1000
                },
                timeout=timeout
            )
            response.raise_for_status()
            logger.debug(f'Successful response for "{url}" on attempt {attempt + 1} using FlareSolver')
            return response

        except requests.exceptions.ConnectionError as e:
            logger.warning(f'Connection error with flaresolver (URL: "{flaresolver_url}"): {e}')
            logger.warning(f'If the url is incorrect, set the env variable "FLARESOLVER_URL" to the correct value')
            logger.warning('If FlareSolver is not installed in your machine, consider installing it.')
            break # Don't retry on Connection Error
        except requests.exceptions.Timeout as e:
            logger.debug(f'Request timed out ({attempt + 1}/{retries}): {e}')
        except requests.exceptions.InvalidSchema as e:
            logger.debug(f'Invalid FlareSolver URL schema "{flaresolver_url}": {e}')
            break  # Don't retry on invalid schema
        except requests.exceptions.HTTPError as e:
            logger.debug(f'HTTP error ({attempt + 1}/{retries}): {e}')
        except requests.exceptions.RequestException as e:
            logger.debug(f'Request failed ({attempt + 1}/{retries}): {e}')
        except json.JSONDecodeError as e:
            logger.debug(f'Invalid JSON response ({attempt + 1}/{retries}): {e}')

        if attempt < retries - 1:
            logger.debug(f'Waiting {time_between_retries} seconds before retrying')
            time.sleep(time_between_retries)  # Wait before retrying

    logger.debug(f'Failed to get a successful response for "{url}" using FlareSolver after {retries} attempts')
    return None


def get_html_content(url: str,
                     retries: int = 3,
                     timeout: int = 20,
                     time_between_retries: int = 3,
                     flaresolver_url: str = FLARESOLVER_URL,
                     force_flaresolver: bool = FORCE_FLARESOLVER) -> Optional[str]:
    """
    Retrieves HTML content from a URL with support for anti-bot protection bypass.

    Implements a two-step strategy:
    1. Attempts a standard HTTP request first (unless force_flaresolver is True)
    2. Falls back to FlareSolver if the standard request fails

    Args:
        url (str): The URL to fetch content from
        retries (int, optional): Number of retry attempts for failed requests. Defaults to 3.
        timeout (int, optional): Timeout in seconds for each request. Defaults to 20.
        time_between_retries (int, optional): Delay in seconds between retries. Defaults to 3.
        flaresolver_url (str, optional): URL of the FlareSolver service.
            Defaults to FLARESOLVER_URL env variable.
        force_flaresolver (bool, optional): If True, skips standard HTTP request and uses
            FlareSolver directly. Defaults to FORCE_FLARESOLVER env variable.

    Returns:
        Optional[str]: The HTML content if successful, None otherwise

    Raises:
        ValidationError: If the provided URL is invalid
        NetworkError: If all attempts to fetch content fail
    """

    parsed_url = urlparse(url)
    if not all([parsed_url.scheme, parsed_url.netloc]):
        raise ValidationError(f"Invalid URL format: {url}")


    logger.debug(
        f'Requesting HTML Content for "{url}" with '
        f'retries: "{retries}", '
        f'timeout: "{timeout}", '
        f'time between retries: "{time_between_retries}"')
    if force_flaresolver:
        logger.debug('Will directly try with FlareSolver')

    # First try with common HTTP request
    if not force_flaresolver:
        response = _get_request(url,
                                timeout=timeout,
                                retries=retries,
                                time_between_retries=time_between_retries)
        if response and response.ok:
            logger.debug(f'Successfully retrieved HTML content from "{url}" using common HTTP request')
            return response.text

    # Try with Flaresolver
    logger.debug(f'Trying with Flaresolver for "{url}"')
    response = _get_request_flaresolver(url,
                                timeout=timeout,
                                retries=retries,
                                time_between_retries=time_between_retries,
                                flaresolver_url=flaresolver_url)
    if not response or not response.ok:
        logger.debug(f'Failed all attempts to get HTML content from "{url}')
        raise NetworkError(f'Failed all attempts to get HTML content from "{url}"')

    try:
        response_json = response.json()
        response_content = response_json.get('solution', {}).get('response')
        if not response_content:
            raise NetworkError(f'No solution response for "{url}"')

        return response_content
    except json.JSONDecodeError as e:
        logger.error(f'Failed to decode FlareSolver response: {e}')
        raise NetworkError(f'Invalid FlareSolver response for "{url}"')
