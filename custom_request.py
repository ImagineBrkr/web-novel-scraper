import requests
import os
import custom_logger
from dotenv import load_dotenv

load_dotenv()

FLARESOLVER_URL = os.getenv('FLARESOLVER_URL', 'http://localhost:8191/v1')
FLARE_HEADERS = {'Content-Type': 'application/json'}

logger = custom_logger.create_logger('GET HTML CONTENT')


def get_request(url: str, timeout: int = 20):
    try:
        response = requests.get(url, timeout=timeout)
        return response
    except requests.exceptions.ConnectionError as e:
        logger.error(f'Connection error {e}')
    except requests.exceptions.InvalidSchema:
        logger.error(f'Check protocol of "{url}"')


def get_request_flaresolver(url: str, timeout: int = 20, flaresolver_url: str = FLARESOLVER_URL):
    logger.debug(f'FLARESOLVER_URL: {flaresolver_url}')
    try:
        response = requests.post(flaresolver_url, headers=FLARE_HEADERS, json={
            'cmd': 'request.get', 'url': url, 'maxTimeout': timeout*1000},
            timeout=timeout)
        return response
    except requests.exceptions.ConnectionError:
        logger.error(f'Connection error, check FlareSolver host: {
                     flaresolver_url}')
    except requests.exceptions.InvalidSchema:
        logger.error(f'Check FlareSolver host "{flaresolver_url}"')


def get_html_content(url: str, attempts: int = 5, flaresolver: bool = True, flaresolver_url: str = FLARESOLVER_URL):
    for _ in range(attempts):
        response = get_request(url, timeout=20)
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
            url, timeout=20, flaresolver_url=flaresolver_url)
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
