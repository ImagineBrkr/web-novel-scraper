import json
from typing import Optional

from pathlib import Path

from . import logger_manager
from .custom_processor.custom_processor import ProcessorRegistry
from .utils import FileOps, DecodeError, HTMLParseError, DecodeGuideError, ContentExtractionError, HostNotExistsError
from .utils import TitleInContentOption

from bs4 import BeautifulSoup

logger = logger_manager.create_logger('DECODE HTML')

XOR_SEPARATOR = "XOR"


class Decoder:
    host: str
    decode_guide_file: Path
    decode_guide: json
    request_config: dict

    def __init__(self,
                 host: str,
                 decode_guide_file: Path,
                 request_config: dict):
        self.decode_guide_file = decode_guide_file
        self.request_config = request_config
        self.set_host(host)

    def set_host(self, host: str) -> None:
        self.host = host
        try:
            self._set_decode_guide()
        except HostNotExistsError:
            raise

        host_request_config = self.get_request_config()
        if host_request_config is not None:
            self._set_request_config(host_request_config)

    def get_request_config(self) -> Optional[dict]:
        """
        Retrieves the request configuration for the current host.

        Returns:
            dict: Request configuration parameters for the current host.
        """

        request_config = self.decode_guide.get('request_config')
        if request_config:
            logger.debug(f'Host "{self.host}" has a custom request configuration on the Decode Guide file.')
            return request_config

        return None

    def is_index_inverted(self) -> bool:
        """
        Checks if the index order should be inverted for the current host.

        Returns:
            bool: True if the index should be processed in reverse order, False otherwise.
        """

        inverted = self.decode_guide.get('index', {}).get('inverted', False)
        return inverted

    def toc_main_url_process(self, toc_main_url: str) -> str:
        if self.decode_guide.get('toc_main_url_processor', False):
            logger.debug('Toc main URL has a custom processor flag, processing...')
            if ProcessorRegistry.has_processor(self.host, 'toc_main_url'):
                try:
                    toc_main_url = ProcessorRegistry.get_processor(self.host,
                                                                   'toc_main_url').process(toc_main_url)
                    toc_main_url = str(toc_main_url)
                    logger.debug(f'Processed URL: {toc_main_url}')
                except DecodeError:
                    logger.debug(f'Could not process URL {toc_main_url}')
                    raise
            else:
                logger.warning(f'Toc main url processor requested but not found for host {self.host}'
                               f', using "{toc_main_url}" as is')
        else:
            logger.debug(f'No processor configuration found for toc_main_url, using "{toc_main_url}" as is')
        return toc_main_url

    def title_in_content(self) -> TitleInContentOption:
        """
        Checks if the title should be included in the content for the current host.

        Returns:
            TitleInContentOption: Yes, Search for it or No
        """
        title_in_content = self.decode_guide.get('title_in_content', 'SEARCH')
        try:
            return TitleInContentOption[title_in_content]
        except KeyError:
            raise DecodeGuideError(
                f"Invalid value on decode guide file for 'title_in_content' option for host {self.host}: "
                f"{title_in_content}")

    def add_host_to_chapter(self) -> bool:
        """
        Checks if the host information should be added to chapter url.

        Returns:
            bool: True if host information should be included in chapter url, False otherwise.
        """
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

    def get_chapter_content(self, html: str, title_in_content: TitleInContentOption, chapter_title: str) -> str:
        """
         Extracts and processes chapter content from HTML.

         Args:
             html (str): The HTML content of the chapter
             title_in_content (TitleInContentOption): Whether to include the title in the content
             chapter_title (str): The chapter title to include if it needs to add title in the content

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

            if isinstance(chapter_content, list):
                logger.debug(f'Processing {len(chapter_content)} content paragraphs')
                full_chapter_content += '\n'.join(str(p) for p in chapter_content)

            logger.debug(f'Title in content option: {title_in_content}')
            if title_in_content == TitleInContentOption.YES:
                logger.debug('Adding chapter title to content...')
                full_chapter_content = f'<h4>{chapter_title}</h4>\n' + full_chapter_content
            elif title_in_content == TitleInContentOption.NO:
                logger.debug('Chapter title will not be added to content')
            elif title_in_content == TitleInContentOption.SEARCH:
                is_title_in_content = full_chapter_content.find(chapter_title) != -1
                if is_title_in_content:
                    logger.debug('Chapter title found in content, will not add it.')
                else:
                    logger.debug('Chapter title not found in content, adding it.')
                    full_chapter_content = f'<h4>{chapter_title}</h4>\n' + full_chapter_content

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
        logger.debug(f'Decoding HTML, Content Type: {content_type}...')
        if content_type not in self.decode_guide:
            msg = f'No decode rules found for {content_type} in guide {self.decode_guide_file}'
            logger.critical(msg)
            raise DecodeGuideError(msg)

        if ProcessorRegistry.has_processor(self.host, content_type):
            logger.debug(f'Using custom processor for {self.host}')
            return ProcessorRegistry.get_processor(self.host, content_type).process(html)

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

    def _set_request_config(self, request_config: dict) -> None:
        if self.request_config is None:
            self.request_config = request_config
            return None

        for key in ["force_flaresolver", "request_retries", "request_timeout", "request_time_between_retries"]:
            new_value = request_config.get(key)
            if new_value is None:
                continue

            if key == "force_flaresolver":
                self.request_config[key] = self.request_config.get(key) or new_value
            else:
                self.request_config[key] = max(
                    self.request_config.get(key, 0),
                    new_value
                )

    def _set_decode_guide(self) -> None:
        decode_guide = FileOps.read_json(self.decode_guide_file)
        self.decode_guide = self._get_element_by_key(decode_guide, 'host', self.host)
        if self.decode_guide is None:
            logger.debug(f'No decode guide found for host {self.host}')
            raise HostNotExistsError(f'No decode guide found for host {self.host}')

    @staticmethod
    def _find_elements(soup: BeautifulSoup, decoder: dict):
        selector = decoder.get('selector')
        elements = []
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
                    if value is not None:
                        selector += f'[{attr}="{value}"]'
                    else:
                        selector += f'[{attr}]'
            selectors = [selector]
        else:
            if XOR_SEPARATOR in selector:
                selectors = selector.split(XOR_SEPARATOR)
            else:
                selectors = [selector]

        logger.debug(f'Selectors: {selectors}')

        for selector in selectors:
            logger.debug(f'Searching using selector "{selector}"...')
            elements = soup.select(selector)
            if elements:
                logger.debug(f'{len(elements)} found using selector "{selector}"')
                break
            logger.debug(f'No elements found using selector "{selector}"')

        extract = decoder.get('extract')
        if extract:
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
                        logger.debug(f'Attribute "{attr_key}" not found. Ignoring...')
                        pass
                logger.debug(f'{len(elements)} elements found with attribute "{attr_key}"')
            if extract["type"] == "text":
                logger.debug('Extracting text from elements...')
                elements = [element.string for element in elements]

        if not elements:
            logger.debug('No elements found')
            return None

        # inverted = decoder.get('inverted')
        # if inverted:
        #     logger.debug('Inverted option activate')
        #     logger.debug('Inverting elements order...')
        #     elements = elements[::-1]

        if decoder.get('array'):
            logger.debug('Array option activated. Returning elements as a list')
            return elements
        logger.debug('Array option not activated. Returning only first element...')
        return elements[0]

    @staticmethod
    def _get_element_by_key(json_data, key: str, value: str) -> Optional[dict]:
        for item in json_data:
            if item[key] == value:
                return item
        return None
