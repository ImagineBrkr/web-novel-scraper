import os
import json
from pathlib import Path

from . import logger_manager

from bs4 import BeautifulSoup

logger = logger_manager.create_logger('DECODE HTML')

CURRENT_DIR = Path(__file__).resolve().parent

DECODE_GUIDE_FILE = os.getenv('DECODE_GUIDE_FILE', f'{
                              CURRENT_DIR}/decode_guide/decode_guide.json')

XOR_SEPARATOR = "XOR"

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
        self.decode_guide = self._get_element_by_key(
            DECODE_GUIDE, 'host', host)

    def decode_html(self, html: str, content_type: str):
        if not content_type in self.decode_guide:
            logger.error(f'{content_type} key does not exists on decode guide {
                         DECODE_GUIDE_FILE} for host {self.host}')
            return
        soup = BeautifulSoup(html, 'html.parser')
        decoder = self.decode_guide[content_type]
        elements = self._find_elements(soup, decoder)
        if not elements:
            logger.warning(f'{content_type} not found on html using {
                           DECODE_GUIDE_FILE} for host {self.host}')
        return elements

    def has_pagination(self, host: str = None):
        if host:
            decode_guide = self._get_element_by_key(DECODE_GUIDE, 'host', host)
            return decode_guide['has_pagination']

        return self.decode_guide['has_pagination']

    def clean_html(self, html: str, hard_clean: bool = False):
        tags_for_soft_clean = ['script', 'style', 'link',
                               'form', 'meta', 'hr', 'noscript', 'button']
        tags_for_hard_clean = ['header', 'footer', 'nav', 'aside', 'iframe', 'object', 'embed', 'svg', 'canvas', 'map', 'area',
                               'audio', 'video', 'track', 'source', 'applet', 'frame', 'frameset', 'noframes', 'noembed', 'blink', 'marquee']

        tags_for_custom_clean = []
        if 'clean' in self.decode_guide:
            tags_for_custom_clean = self.decode_guide['clean']

        tags_for_clean = tags_for_soft_clean + tags_for_custom_clean
        if hard_clean:
            tags_for_clean += tags_for_hard_clean

        soup = BeautifulSoup(html, 'html.parser')
        for unwanted_tags in soup(tags_for_clean):
            unwanted_tags.decompose()

        return "\n".join([line.strip() for line in str(soup).splitlines() if line.strip()])

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
            selectors = [selector]
        else:
            if XOR_SEPARATOR in selector:
                selectors = selector.split(XOR_SEPARATOR)
            else:
                selectors = [selector]

        for selector in selectors:
            logger.debug(f'Attempt using selector {selector}')
            elements = soup.select(selector)
            if elements:
                logger.debug(f'{len(elements)} found using selector {selector}')
                break

        extract = decoder.get('extract')
        if extract:
            if extract["type"] == "attr":
                attr_key = extract["key"]
                elements_aux = elements
                elements = []
                for element in elements_aux:
                    try:
                        attr = element[attr_key]
                        if attr:
                            elements.append(attr)
                    except KeyError:
                        pass
            if extract["type"] == "text":
                elements = [element.string for element in elements]
        inverted = decoder.get('inverted')
        if inverted:
            elements = elements[::-1]
        return elements if decoder.get('array') else elements[0] if elements else None

    def _get_element_by_key(self, json_data, key, value):
        for item in json_data:
            if item[key] == value:
                return item
        logger.warning('Host not found, using default decoder.')
        return json_data[0]
