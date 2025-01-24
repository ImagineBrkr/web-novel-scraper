import requests
import os
from . import logger_manager
from dotenv import load_dotenv
import json
import time

load_dotenv()

FLARESOLVER_URL = os.getenv('SCRAPER_FLARESOLVER_URL', 'http://localhost:8191/v1')
FLARE_HEADERS = {'Content-Type': 'application/json'}
FORCE_FLARESOLVER = os.getenv('FORCE_FLARESOLVER', '0') == '1'

logger = logger_manager.create_logger('GET HTML CONTENT')

def get_request(url: str,
                timeout: int = 20,
                retries: int = 3,
                time_between_retries: int = 1) -> requests.Response | None:
    logger.debug(f'Starting get_request for {url} with timeout={timeout}, retries={retries}, time_between_retries={time_between_retries}')
    for attempt in range(retries):
        logger.debug(f'Attempt {attempt + 1} for {url}')
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            logger.debug(f'Successful response for {url} on attempt {attempt + 1}')
            return response
        except requests.exceptions.ConnectionError as e:
            logger.error(f'Connection error ({attempt + 1}/{retries}): {e}')
        except requests.exceptions.Timeout as e:
            logger.error(f'Request timed out ({attempt + 1}/{retries}): {e}')
        except requests.exceptions.HTTPError as e:
            logger.error(f'HTTP error ({attempt + 1}/{retries}): {e}')
        except requests.exceptions.InvalidSchema as e:
            logger.error(f'Invalid URL schema for "{url}": {e}')
            break  # Don't retry on invalid schema
        except requests.exceptions.RequestException as e:
            logger.error(f'Request failed ({attempt + 1}/{retries}): {e}')

        if attempt < retries - 1:
            logger.debug(f'Waiting {time_between_retries} seconds before retrying')
            time.sleep(time_between_retries)  # Wait before retrying
    logger.debug(f'Failed to get a successful response for {url} after {retries} attempts')
    return None


def get_request_flaresolver(url: str,
                            timeout: int = 20,
                            flaresolver_url: str = FLARESOLVER_URL,
                            retries: int = 3,
                            time_between_retries: int = 1) -> requests.Response | None:
    logger.debug(f'Starting get_request_flaresolver for {url} with timeout={timeout}, retries={retries}, time_between_retries={time_between_retries}')
    for attempt in range(retries):
        logger.debug(f'Attempt {attempt + 1} for {url} using FlareSolver')
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
            logger.debug(f'Successful response for {url} on attempt {attempt + 1} using FlareSolver')
            return response

        except requests.exceptions.ConnectionError as e:
            logger.error(f'Connection error ({attempt + 1}/{retries}), check FlareSolver host: {flaresolver_url}: {e}')
        except requests.exceptions.Timeout as e:
            logger.error(f'Request timed out ({attempt + 1}/{retries}): {e}')
        except requests.exceptions.InvalidSchema as e:
            logger.error(f'Invalid FlareSolver URL schema "{flaresolver_url}": {e}')
            break  # Don't retry on invalid schema
        except requests.exceptions.HTTPError as e:
            logger.error(f'HTTP error ({attempt + 1}/{retries}): {e}')
        except requests.exceptions.RequestException as e:
            logger.error(f'Request failed ({attempt + 1}/{retries}): {e}')
        except json.JSONDecodeError as e:
            logger.error(f'Invalid JSON response ({attempt + 1}/{retries}): {e}')

        if attempt < retries - 1:
            logger.debug(f'Waiting {time_between_retries} seconds before retrying')
            time.sleep(time_between_retries)  # Wait before retrying
    logger.debug(f'Failed to get a successful response for {url} using FlareSolver after {retries} attempts')
    return None


def get_html_content(url: str,
                     retries: int = 5,
                     flaresolver: bool = True,
                     flaresolver_url: str = FLARESOLVER_URL,
                     time_between_retries: int = 1,
                     force_flaresolver: bool = FORCE_FLARESOLVER) -> str | None:
    logger.debug(f'Starting get_html_content for {url} with retries={retries}, flaresolver={flaresolver}, flaresolver_url={flaresolver_url}, time_between_retries={time_between_retries}, force_flaresolver={force_flaresolver}')
    # First try with common HTTP request
    if not force_flaresolver:
        response = get_request(
            url, timeout=20, retries=retries, time_between_retries=time_between_retries)
        if not response:
            logger.warning(f'Failed to get response from {url} using common HTTP request')
        elif not response.ok:
            logger.warning(f'Response with errors from {url} using common HTTP request')
        else:
            logger.debug(f'Successfully retrieved HTML content from {url} using common HTTP request')
            return response.text

    # If flaresolver is disabled, return None
    if not flaresolver:
        logger.debug(f'Flaresolver is disabled, returning None for {url}')
        return None

    # Try with Flaresolver
    logger.debug(f'Trying with Flaresolver for {url}')
    response = get_request_flaresolver(
        url, timeout=20, flaresolver_url=flaresolver_url, time_between_retries=time_between_retries)
    if not response:
        logger.critical(f'Failed to get response from {url} using FlareSolver')
        return None
    if not response.ok:
        logger.critical(f'Response with errors from {url} using FlareSolver')
        return None

    response_json = response.json()
    if 'solution' not in response_json:
        logger.critical(f'No solution found in FlareSolver response for {url}')
        return None
    if 'response' not in response_json['solution']:
        logger.critical(f'No response found in FlareSolver solution for {url}')
        return None
    logger.debug(f'Successfully retrieved HTML content from {url} using FlareSolver')
    return response_json['solution']['response']
