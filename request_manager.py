import requests
import os
import custom_logger
from dotenv import load_dotenv
import json
import time

load_dotenv()

FLARESOLVER_URL = os.getenv('FLARESOLVER_URL', 'http://localhost:8191/v1')
FLARE_HEADERS = {'Content-Type': 'application/json'}

logger = custom_logger.create_logger('GET HTML CONTENT')


def get_request(url: str, timeout: int = 20, max_retries: int = 3, time_between_retries: int = 1) -> requests.Response | None:
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError as e:
            logger.error(
                f'Connection error ({attempt + 1}/{max_retries}): {e}')
        except requests.exceptions.Timeout as e:
            logger.error(
                f'Request timed out ({attempt + 1}/{max_retries}): {e}')
        except requests.exceptions.HTTPError as e:
            logger.error(f'HTTP error ({attempt + 1}/{max_retries}): {e}')
        except requests.exceptions.InvalidSchema as e:
            logger.error(f'Invalid URL schema for "{url}": {e}')
            break  # Don't retry on invalid schema
        except requests.exceptions.RequestException as e:
            logger.error(f'Request failed ({attempt + 1}/{max_retries}): {e}')

        if attempt < max_retries - 1:
            time.sleep(time_between_retries)  # Wait before retrying
    return None


def get_request_flaresolver(url: str, timeout: int = 20, flaresolver_url: str = FLARESOLVER_URL, max_retries: int = 3, time_between_retries: int = 1) -> requests.Response | None:
    logger.debug(f'FLARESOLVER_URL: {flaresolver_url}')

    for attempt in range(max_retries):
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
                         attempt + 1}/{max_retries}), check FlareSolver host: {flaresolver_url}: {e}')
        except requests.exceptions.Timeout as e:
            logger.error(
                f'Request timed out ({attempt + 1}/{max_retries}): {e}')
        except requests.exceptions.InvalidSchema as e:
            logger.error(f'Invalid FlareSolver URL schema "{
                         flaresolver_url}": {e}')
            break  # Don't retry on invalid schema
        except requests.exceptions.HTTPError as e:
            logger.error(f'HTTP error ({attempt + 1}/{max_retries}): {e}')
        except requests.exceptions.RequestException as e:
            logger.error(f'Request failed ({attempt + 1}/{max_retries}): {e}')
        except json.JSONDecodeError as e:
            logger.error(f'Invalid JSON response ({
                         attempt + 1}/{max_retries}): {e}')

        if attempt < max_retries - 1:
            time.sleep(time_between_retries)  # Wait before retrying
    return None


def get_html_content(url: str, attempts: int = 5, flaresolver: bool = True, flaresolver_url: str = FLARESOLVER_URL, time_between_retries: int = 1):
    for _ in range(attempts):
        response = get_request(
            url, timeout=20, time_between_retries=time_between_retries)
        if not response:
            continue
        if not response.ok:
            logger.error(f'Response with errors from {url}')
            continue
        return response.text

    if not flaresolver:
        return
    logger.debug(f'Trying with Flaresolver for {url}')
    for _ in range(attempts):
        response = get_request_flaresolver(
            url, timeout=20, flaresolver_url=flaresolver_url, time_between_retries=time_between_retries)
        if not response:
            continue
        if not response.ok:
            logger.error(f'Response with errors from {url}')
            continue
        response_json = response.json()
        if not 'solution' in response_json:
            continue
        if not 'response' in response_json['solution']:
            continue
        return response_json['solution']['response']
