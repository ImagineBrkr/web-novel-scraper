import json
from typing import Optional

from pathlib import Path

from . import logger_manager
from .custom_processor.custom_processor import ProcessorRegistry
from .utils import FileOps, DecodeError, ValidationError, HTMLParseError, DecodeGuideError, ContentExtractionError

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
    decode_guide_file: Path
    decode_guide: json
    request_config: dict

    def __init__(self, host: str, decode_guide_file: Path):
        self.decode_guide_file = decode_guide_file
        self.set_host(host)

    def set_host(self, host: str) -> None:
        self.host = host
        try:
            self._set_decode_guide()
        except ValidationError:
            raise

        host_request_config = self.get_request_config()
        self.request_config = DEFAULT_REQUEST_CONFIG | host_request_config

    def get_request_config(self) -> dict:
        """
        Retrieves the request configuration for the current host.

        Returns:
            dict: Request configuration parameters for the current host.
                Returns DEFAULT_REQUEST_CONFIG if no custom configuration exists.
        """

        request_config = self.decode_guide.get('request_config')
        if request_config:
            logger.debug(f'Host "{self.host}" has a custom request configuration on the Decode Guide file.')
            return request_config

        return DEFAULT_REQUEST_CONFIG

    def is_index_inverted(self) -> bool:
        """
        Checks if the index order should be inverted for the current host.

        Returns:
            bool: True if the index should be processed in reverse order, False otherwise.
        """

        logger.debug('Checking if index should be inverted...')
        return self.decode_guide.get('index', {}).get('inverted', False)

    def toc_main_url_process(self, toc_main_url: str) -> str:
        if self.decode_guide.get('toc_main_url_processor', False):
            logger.debug('Toc main URL has a custom processor flag, processing...')
            try:
                toc_main_url = ProcessorRegistry.get_processor(self.host, 'toc_main_url').process(toc_main_url)
                toc_main_url = str(toc_main_url)
                logger.debug(f'Processed URL: {toc_main_url}')
            except DecodeError:
                logger.debug(f'Could not process URL {toc_main_url}')
                raise
        else:
            logger.debug(f'No processor configuration found for toc_main_url, using "{toc_main_url}" as is')
        return toc_main_url

    def save_title_to_content(self) -> bool:
        """
        Checks if the title should be included in the content for the current host.

        Returns:
            bool: True if the title should be saved with the content, False otherwise.
        """
        logger.debug('Checking if title should be saved to content...')
        try:
            return self.decode_guide.get('save_title_to_content', False)
        except DecodeError:
            raise

    def add_host_to_chapter(self) -> bool:
        """
        Checks if the host information should be added to chapter url.

        Returns:
            bool: True if host information should be included in chapter url, False otherwise.
        """
        logger.debug('Checking if host should be added to chapter url...')
        return self.decode_guide.get('add_host_to_chapter', False)

    def get_chapter_urls(self, html: str) -> list[str]:
        """
        Extracts chapter URLs from the table of contents HTML.

        Args:
            html (str): The HTML content of the table of contents

        Returns:
            list[str]: List of chapter URLs found in the HTML

        Raises:
            ContentExtractionError: If chapter URLs cannot be extracted.
            HTMLParseError: If HTML parsing fails.
        """
        try:
            logger.debug('Obtaining chapter URLs...')
            chapter_urls = self.decode_html(html, 'index')

            if chapter_urls is None:
                msg = f"Failed to obtain chapter URLs for {self.host}"
                logger.error(msg)
                raise ContentExtractionError(msg)

            if isinstance(chapter_urls, str):
                logger.warning('Expected List of URLs but got String, converting to single-item list')
                chapter_urls = [chapter_urls]

            return chapter_urls
        except DecodeError:
            raise
        except Exception as e:
            msg = f"Error extracting chapter URLs: {e}"
            logger.error(msg)
            raise ContentExtractionError(msg) from e

    def get_toc_next_page_url(self, html: str) -> Optional[str]:
        """
        Extracts the URL for the next page of the table of contents.

        Args:
            html (str): The HTML content of the current TOC page

        Returns:
            Optional[str]: URL of the next page if it exists, None otherwise

        Raises:
            HTMLParseError: If HTML parsing fails
            ContentExtractionError: If URL extraction fails
        """

        logger.debug('Obtaining toc next page URL...')
        try:
            toc_next_page_url = self.decode_html(html, 'next_page')
            if toc_next_page_url is None:
                logger.debug('No next page URL found, assuming last page...')
                return None
            return toc_next_page_url
        except DecodeError:
            raise

    def get_chapter_title(self, html: str) -> Optional[str]:
        """
        Extracts the chapter title from HTML content.

        Args:
            html (str): The HTML content of the chapter

        Returns:
            Optional[str]: The extracted title, or None if not found

        Raises:
            HTMLParseError: If HTML parsing fails
        """

        try:
            logger.debug('Obtaining chapter title...')
            chapter_title = self.decode_html(html, 'title')

            if chapter_title is None:
                logger.debug('No chapter title found')
                return None

            return str(chapter_title).strip()
        except DecodeError as e:
            logger.warning(f"Error when trying to extract chapter title: {e}")
            return None
        except Exception as e:
            msg = f"Error extracting chapter title: {e}"
            logger.error(msg)
            raise HTMLParseError(msg) from e

    def get_chapter_content(self, html: str, save_title_to_content: bool, chapter_title: str) -> str:
        """
         Extracts and processes chapter content from HTML.

         Args:
             html (str): The HTML content of the chapter
             save_title_to_content (bool): Whether to include the title in the content
             chapter_title (str): The chapter title to include if save_title_to_content is True

         Returns:
             str: The processed chapter content with HTML formatting

         Raises:
             ContentExtractionError: If content cannot be extracted,
             HTMLParseError: If HTML parsing fails
         """
        try:
            logger.debug('Obtaining chapter content...')
            full_chapter_content = ""
            chapter_content = self.decode_html(html, 'content')

            if chapter_content is None:
                msg = 'No content found in chapter'
                logger.error(msg)
                raise ContentExtractionError(msg)

            if save_title_to_content:
                logger.debug('Adding chapter title to content...')
                full_chapter_content += f'<h4>{chapter_title}</h4>'

            if isinstance(chapter_content, list):
                logger.debug(f'Processing {len(chapter_content)} content paragraphs')
                full_chapter_content += '\n'.join(str(p) for p in chapter_content)
            else:
                logger.debug('Processing single content block')
                full_chapter_content += str(chapter_content)

            return full_chapter_content
        except DecodeError:
            raise
        except Exception as e:
            msg = f"Error extracting chapter content: {e}"
            logger.error(msg)
            raise ContentExtractionError(msg) from e

    def has_pagination(self) -> bool:
        """
        Checks if the current host's content uses pagination.

        Returns:
            bool: True if the host uses pagination, False otherwise.
        """
        logger.debug('Checking if index has pagination...')
        return self.decode_guide.get('has_pagination', False)

    def clean_html(self, html: str, hard_clean: bool = False):
        tags_for_soft_clean = ['script', 'style', 'link',
                               'form', 'meta', 'hr', 'noscript', 'button']
        tags_for_hard_clean = ['header', 'footer', 'nav', 'aside', 'iframe', 'object', 'embed', 'svg', 'canvas', 'map',
                               'area',
                               'audio', 'video', 'track', 'source', 'applet', 'frame', 'frameset', 'noframes',
                               'noembed', 'blink', 'marquee']

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

    def decode_html(self, html: str, content_type: str) -> str | list[str] | None:
        logger.debug(f'Decoding HTML...')
        logger.debug(f'Content type: {content_type}')
        logger.debug(f'Decode guide: {self.decode_guide_file}')
        logger.debug(f'Host: {self.host}')
        if content_type not in self.decode_guide:
            msg = f'No decode rules found for {content_type} in guide {self.decode_guide_file}'
            logger.critical(msg)
            raise DecodeGuideError(msg)

        if ProcessorRegistry.has_processor(self.host, content_type):
            logger.debug(f'Using custom processor for {self.host}')
            return ProcessorRegistry.get_processor(self.host, content_type).process(html)

        logger.debug('Parsing HTML...')
        try:
            soup = BeautifulSoup(html, 'html.parser')
        except Exception as e:
            logger.error(f'Error parsing HTML with BeautifulSoup: {e}')
            raise HTMLParseError(f'Error parsing HTML with BeautifulSoup: {e}')

        decoder = self.decode_guide.get(content_type)
        if decoder is None:
            logger.error(f'No decode rules found for {content_type} in guide {self.decode_guide_file}')
            raise DecodeGuideError(f'No decode rules found for {content_type} in guide {self.decode_guide_file}')
        elements = self._find_elements(soup, decoder)
        if not elements:
            logger.debug(f'No {content_type} found in HTML')
            return None

        # Investigate this conditional
        if content_type == 'title' and isinstance(elements, list):
            logger.debug('Joining multiple title elements')
            return ' '.join(elements)
        return elements

    def _set_decode_guide(self) -> None:
        decode_guide = FileOps.read_json(self.decode_guide_file)
        self.decode_guide = self._get_element_by_key(decode_guide, 'host', self.host)
        if self.decode_guide is None:
            logger.error(f'No decode guide found for host {self.host}')
            raise ValidationError(f'No decode guide found for host {self.host}')

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

        # inverted = decoder.get('inverted')
        # if inverted:
        #     logger.debug('Inverted option activate')
        #     logger.debug('Inverting elements order...')
        #     elements = elements[::-1]

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
