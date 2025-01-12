import requests
import os
import custom_logger
from dotenv import load_dotenv
import json
import time

load_dotenv()

FLARESOLVER_URL = os.getenv('FLARESOLVER_URL', 'http://localhost:8191/v1')
FLARE_HEADERS = {'Content-Type': 'application/json'}
FORCE_FLARESOLVER = os.getenv('FORCE_FLARESOLVER', '0') == '1'

logger = custom_logger.create_logger('GET HTML CONTENT')


def get_request(url: str,
                timeout: int = 20,
                retries: int = 3,
                time_between_retries: int = 1) -> requests.Response | None:
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError as e:
            logger.error(
                f'Connection error ({attempt + 1}/{retries}): {e}')
        except requests.exceptions.Timeout as e:
            logger.error(
                f'Request timed out ({attempt + 1}/{retries}): {e}')
        except requests.exceptions.HTTPError as e:
            logger.error(f'HTTP error ({attempt + 1}/{retries}): {e}')
        except requests.exceptions.InvalidSchema as e:
            logger.error(f'Invalid URL schema for "{url}": {e}')
            break  # Don't retry on invalid schema
        except requests.exceptions.RequestException as e:
            logger.error(f'Request failed ({attempt + 1}/{retries}): {e}')

        if attempt < retries - 1:
            time.sleep(time_between_retries)  # Wait before retrying
    return None


def get_request_flaresolver(url: str,
                            timeout: int = 20,
                            flaresolver_url: str = FLARESOLVER_URL,
                            retries: int = 3,
                            time_between_retries: int = 1) -> requests.Response | None:
    for attempt in range(retries):
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
            return response

        except requests.exceptions.ConnectionError as e:
            logger.error(f'Connection error ({
                         attempt + 1}/{retries}), check FlareSolver host: {flaresolver_url}: {e}')
        except requests.exceptions.Timeout as e:
            logger.error(
                f'Request timed out ({attempt + 1}/{retries}): {e}')
        except requests.exceptions.InvalidSchema as e:
            logger.error(f'Invalid FlareSolver URL schema "{
                         flaresolver_url}": {e}')
            break  # Don't retry on invalid schema
        except requests.exceptions.HTTPError as e:
            logger.error(f'HTTP error ({attempt + 1}/{retries}): {e}')
        except requests.exceptions.RequestException as e:
            logger.error(f'Request failed ({attempt + 1}/{retries}): {e}')
        except json.JSONDecodeError as e:
            logger.error(f'Invalid JSON response ({
                         attempt + 1}/{retries}): {e}')

        if attempt < retries - 1:
            time.sleep(time_between_retries)  # Wait before retrying
    return None


def get_html_content(url: str,
                     retries: int = 5,
                     flaresolver: bool = True,
                     flaresolver_url: str = FLARESOLVER_URL,
                     time_between_retries: int = 1,
                     force_flaresolver: bool = FORCE_FLARESOLVER) -> str | None:
    # First try with common HTTP request
    # If force_flaresolver is True, it will not try with common HTTP request
    # force_flarseolver can be defined in the environment variable FORCE_FLARESOLVER
    # or as a parameter
    if not force_flaresolver:
        response = get_request(
            url, timeout=20, retries=retries, time_between_retries=time_between_retries)
        if not response:
            logger.warning(f'Failed to get response from {
                           url} using common HTTP request')
        elif not response.ok:
            logger.warning(f'Response with errors from {
                           url} using common HTTP request')
        else:
            return response.text

    # If flaresolver is disabled, return None
    if not flaresolver:
        return

    # Try with Flaresolver
    logger.debug(f'Trying with Flaresolver for {url}')
    response = get_request_flaresolver(
        url, timeout=20, flaresolver_url=flaresolver_url, time_between_retries=time_between_retries)
    if not response:
        logger.warning(f'Failed to get response from {url} using FlareSolver')
        return
    if not response.ok:
        logger.error(f'Response with errors from {url} using FlareSolver')
        return

    response_json = response.json()
    if not 'solution' in response_json:
        return
    if not 'response' in response_json['solution']:
        return
    return response_json['solution']['response']
