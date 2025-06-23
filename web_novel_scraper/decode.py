import json
from typing import Optional

from . import logger_manager
from .custom_processor.custom_processor import ProcessorRegistry
from .utils import FileOps

from bs4 import BeautifulSoup

logger = logger_manager.create_logger('DECODE HTML')

XOR_SEPARATOR = "XOR"

DEFAULT_REQUEST_CONFIG = {
    "force_flaresolver": False,
    "request_retries": 3,
    "request_timeout": 20,
    "request_time_between_retries": 3
}

class Decoder:
    host: str
    decode_guide_file: str
    decode_guide: json
    request_config: dict

    def __init__(self, host: str, decode_guide_file: str):
        self.decode_guide_file = decode_guide_file
        self.set_host(host)

    def set_host(self, host: str) -> None:
        self.host = host
        self._set_decode_guide()
        host_request_config = self.get_request_config()
        self.request_config = DEFAULT_REQUEST_CONFIG | host_request_config

    def get_request_config(self) -> dict:
        request_config = self.decode_guide.get('request_config')
        if request_config:
            logger.debug(f'Host "{self.host}" has a custom request configuration on the Decode Guide file.')
            return request_config

        return DEFAULT_REQUEST_CONFIG

    def is_index_inverted(self) -> bool:
        return self.decode_guide.get('index', {}).get('inverted', False)

    def save_title_to_content(self) -> bool:
        return self.decode_guide.get('save_title_to_content', False)

    def add_host_to_chapter(self) -> bool:
        return self.decode_guide.get('add_host_to_chapter', False)

    def get_chapter_urls(self, html: str) -> list[str]:
        logger.debug('Obtaining chapter URLs...')
        chapter_urls = self.decode_html(html, 'index')

        if chapter_urls is None:
            logger.critical(f"Failed to obtain chapter URLs for {self.host}")
            raise ValueError(f"Failed to obtain chapter URLs for {self.host}")

        if isinstance(chapter_urls, str):
            logger.warning('When obtaining chapter urls, obtained a String but expected a List')
            logger.warning('Check decode config')
            chapter_urls = [chapter_urls]

        return chapter_urls

    def get_toc_next_page_url(self, html: str) -> Optional[str]:
        logger.debug('Obtaining toc next page URL...')
        toc_next_page_url = self.decode_html(html, 'next_page')
        if toc_next_page_url is None:
            logger.debug('No next page URL found, assuming last page...')
            return None
        return toc_next_page_url

    def get_chapter_title(self, html: str) -> Optional[str]:
        logger.debug('Obtaining chapter title...')
        chapter_title = self.decode_html(html, 'title')
        if chapter_title is None:
            logger.debug(f'No chapter_title found.')
        return chapter_title

    def get_chapter_content(self, html: str, save_title_to_content: bool, chapter_title: str) -> str:
        logger.debug('Obtaining chapter content...')
        full_chapter_content = ""
        chapter_content = self.decode_html(html, 'content')

        if chapter_content is None:
            logger.critical('No content found on chapter')
            raise ValueError('No content found on chapter')

        if save_title_to_content:
            logger.debug('Saving chapter title to content...')
            full_chapter_content += f'<h4>{chapter_title}</h4>'

        if isinstance(chapter_content, list):
            logger.debug(f'{len(chapter_content)} paragraphs found in chapter')
            logger.debug('Converting list of paragraphs to a single string')
            for paragraph in chapter_content:
                full_chapter_content += str(paragraph)
        else:
            logger.debug('Chapter content is not a list, no conversion made')
            full_chapter_content += str(chapter_content)
        return full_chapter_content

    def decode_html(self, html: str, content_type: str) -> str | list[str] | None:
        logger.debug(f'Decoding HTML...')
        logger.debug(f'Content type: {content_type}')
        logger.debug(f'Decode guide: {self.decode_guide_file}')
        logger.debug(f'Host: {self.host}')
        if not content_type in self.decode_guide:
            logger.critical(f'{content_type} key does not exists on decode guide {self.decode_guide_file}'
                            f'for host {self.host}')
            raise ValueError(f'{content_type} key does not exists on decode guide {self.decode_guide_file}'
                            f'for host {self.host}')

        if ProcessorRegistry.has_processor(self.host, content_type):
            logger.debug(f'Host {self.host} will use a custom processor')
            processor = ProcessorRegistry.get_processor(self.host, content_type)
            return processor.process(html)

        logger.debug('Starting HTML parsing...')
        try:
            soup = BeautifulSoup(html, 'html.parser')
        except Exception as e:
            logger.critical(f'Error parsing HTML with BeautifulSoup: {e}')
            raise ValueError(f'Error parsing HTML with BeautifulSoup: {e}')

        decoder = self.decode_guide[content_type]
        elements = self._find_elements(soup, decoder)
        if not elements:
            logger.debug(f'{content_type} not found on html using {self.decode_guide_file} '
                           f'for host {self.host}')

        # Investigate this conditional
        if content_type == 'title' and isinstance(elements, list):
            logger.debug('Joining titles...')
            return ' '.join(elements)
        return elements

    def has_pagination(self) -> bool:
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

    def _set_decode_guide(self) -> None:
        decode_guide = FileOps.read_json(self.decode_guide_file)
        self.decode_guide = self._get_element_by_key(decode_guide, 'host', self.host)
        if self.decode_guide is None:
            logger.critical(f'No decode guide found for host {self.host}')
            raise ValueError(f'No decode guide found for host {self.host}')

    @staticmethod
    def _find_elements(soup: BeautifulSoup, decoder: dict):
        logger.debug('Finding elements...')
        selector = decoder.get('selector')
        elements = []
        if selector is None:
            selector = ''
            element = decoder.get('element')
            _id = decoder.get('id')
            _class = decoder.get('class')
            attributes = decoder.get('attributes')

            if element:
                logger.debug(f'Using element "{element}"')
                selector += element
            if _id:
                logger.debug(f'Using id "{_id}"')
                selector += f'#{_id}'
            if _class:
                logger.debug(f'Using class "{_class}"')
                selector += f'.{_class}'
            if attributes:
                for attr, value in attributes.items():
                    logger.debug(f'Using attribute "{attr}"')
                    if value is not None:
                        logger.debug(f'With value "{value}"')
                        selector += f'[{attr}="{value}"]'
                    else:
                        selector += f'[{attr}]'
            selectors = [selector]
        else:
            logger.debug(f'Using selector "{selector}"')
            if XOR_SEPARATOR in selector:
                logger.debug(f'Found XOR_OPERATOR "{XOR_SEPARATOR}" in selector')
                logger.debug('Splitting selectors...')
                selectors = selector.split(XOR_SEPARATOR)
            else:
                selectors = [selector]

        for selector in selectors:
            logger.debug(f'Searching using selector "{selector}"...')
            elements = soup.select(selector)
            if elements:
                logger.debug(f'{len(elements)} found using selector "{selector}"')
                break
            logger.debug(f'No elements found using selector "{selector}"')

        extract = decoder.get('extract')
        if extract:
            logger.debug(f'Extracting from elements...')
            if extract["type"] == "attr":
                attr_key = extract["key"]
                logger.debug(f'Extracting value from attribute "{attr_key}"...')
                elements_aux = elements
                elements = []
                for element in elements_aux:
                    try:
                        attr = element[attr_key]
                        if attr:
                            elements.append(attr)
                    except KeyError:
                        logger.debug(f'Attribute "{attr_key}" not found')
                        logger.debug('Ignoring...')
                        pass
                logger.debug(f'{len(elements)} elements found using attribute "{attr_key}"')
            if extract["type"] == "text":
                logger.debug('Extracting text from elements...')
                elements = [element.string for element in elements]

        if not elements:
            logger.debug('No elements found, returning "None"')
            return None

        inverted = decoder.get('inverted')
        if inverted:
            logger.debug('Inverted option activate')
            logger.debug('Inverting elements order...')
            elements = elements[::-1]

        if decoder.get('array'):
            logger.debug('Array option activated')
            logger.debug('Returning elements a list')
            return elements
        logger.debug('Array option not activated')
        logger.debug('Returning only first element...')
        return elements[0]

    @staticmethod
    def _get_element_by_key(json_data, key: str, value: str) -> Optional[dict]:
        for item in json_data:
            if item[key] == value:
                return item
        return None
