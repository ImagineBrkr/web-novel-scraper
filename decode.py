import os
import json
from pathlib import Path

import custom_logger

from bs4 import BeautifulSoup

logger = custom_logger.create_logger('DECODE HTML')

CURRENT_DIR = Path(__file__).resolve().parent

DECODE_GUIDE_FILE = os.getenv('DECODE_GUIDE_FILE', f'{CURRENT_DIR}/decode_guide.json')

try:
    with open(DECODE_GUIDE_FILE, 'r', encoding='UTF-8') as f:
        DECODE_GUIDE = json.load(f)
except FileNotFoundError:
    logger.error(f"File {DECODE_GUIDE_FILE} not found.")
    raise
except PermissionError:
    logger.error(f"Permission error {DECODE_GUIDE_FILE}.")
    raise
except json.JSONDecodeError:
    logger.error(f"Json Decode error {DECODE_GUIDE_FILE}.")
    raise
except Exception as e:
    logger.error(f"Error {DECODE_GUIDE_FILE}: {e}")
    raise

class Decoder:
    host: str
    decode_guide: json

    def __init__(self, host: str):
        self.host = host
        self.decode_guide = self._get_element_by_key(DECODE_GUIDE, 'host', host)

    def decode_html(self, html: str, content_type: str):
        if not content_type in self.decode_guide:
            logger.error(f'{content_type} key does not exists on decode guide {DECODE_GUIDE_FILE} for host {self.host}')
            return
        soup = BeautifulSoup(html, 'html.parser')
        decoder = self.decode_guide[content_type]
        elements = self._find_elements(soup, decoder)
        if not elements:
            logger.warning(f'{content_type} not found on html using {DECODE_GUIDE_FILE} for host {self.host}')
        return elements

    def has_pagination(self, host: str = None):
        if host:
            decode_guide = self._get_element_by_key(DECODE_GUIDE, 'host', host)
            return decode_guide['has_pagination']

        return self.decode_guide['has_pagination']

    def _find_elements(self, soup: BeautifulSoup, decoder: dict):
        selector = decoder.get('selector')
        if selector is None:
            selector = ''
            element = decoder.get('element')
            _id = decoder.get('id')
            _class = decoder.get('class')
            attributes = decoder.get('attributes')

            if element:
                selector += element
            if _id:
                selector += f'#{_id}'
            if _class:
                selector += f'.{_class}'
            if attributes:
                for attr, value in attributes.items():
                    selector += f'[{attr}="{value}"]' if value else f'[{attr}]'

        elements = soup.select(selector) if selector else []

        return elements if decoder['array'] else elements[0] if elements else None

    def _get_element_by_key(self, json_data, key, value):
        for item in json_data:
            if item[key] == value:
                return item
        return json_data[0]