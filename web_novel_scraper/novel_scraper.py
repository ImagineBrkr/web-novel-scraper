from dataclasses import dataclass, field, replace

from dataclasses_json import dataclass_json, Undefined, config
from ebooklib import epub
from typing import Optional
from pathlib import Path

from . import logger_manager
from .decode import Decoder
from .file_manager import FileManager
from . import utils
from .request_manager import get_html_content
from .config_manager import ScraperConfig
from .models import ScraperBehavior, Metadata, Chapter
from .utils import _always, ScraperError, FileManagerError, NetworkError, ValidationError, DecodeError

logger = logger_manager.create_logger('NOVEL SCRAPPING')


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Novel:
    """
    A class representing a web novel with its metadata and content.

    This class handles all operations related to scraping, storing, and managing web novels,
    including their chapters, table of contents, and metadata.

    Attributes:
        title (str): The title of the novel.
        host (Optional[str]): The host domain where the novel is located.
        toc_main_url (Optional[str]): The main URL for the table of contents.
        chapters (list[Chapter]): List of chapters in the novel.
        chapters_url_list (list[str]): List of URLs for all chapters.
        metadata (Metadata): Novel metadata like author, language, etc.
        scraper_behavior (ScraperBehavior): Configuration for scraping behavior.
        file_manager (FileManager): Handles file operations for the novel.
        decoder (Decoder): Handles HTML decoding and parsing.
        config (ScraperConfig): General scraper configuration.
    """

    title: str
    host: Optional[str] = None
    toc_main_url: Optional[str] = None
    chapters: list[Chapter] = field(default_factory=list)
    chapters_url_list: list[str] = field(default_factory=list)
    metadata: Metadata = field(default_factory=Metadata)
    scraper_behavior: ScraperBehavior = field(default_factory=ScraperBehavior)

    file_manager: FileManager = field(default=None,
                                      repr=False,
                                      compare=False,
                                      metadata=config(exclude=_always))
    decoder: Decoder = field(default=None,
                             repr=False,
                             compare=False,
                             metadata=config(exclude=_always))
    config: ScraperConfig = field(default=None,
                                  repr=False,
                                  compare=False,
                                  metadata=config(exclude=_always))

    def __post_init__(self):
        """
        Validates the novel instance after initialization.

        Raises:
            ValidationError: If the title is empty or neither host nor toc_main_url is provided.
        """

        if not self.title:
            raise ValidationError("title can't be empty")
        if not (self.host or self.toc_main_url):
            raise ValidationError('You must provide "host" or "toc_main_url"')

    def __str__(self):
        """
        Returns a string representation of the novel with its main attributes.

        Returns:
            str: A formatted string containing the novel's main information.
        """

        toc_info = self.toc_main_url if self.toc_main_url else "TOC added manually"
        attributes = [
            f"Title: {self.title}",
            f"Author: {self.metadata.author}",
            f"Language: {self.metadata.language}",
            f"Description: {self.metadata.description}",
            f"Tags: {', '.join(self.metadata.tags)}",
            f"TOC Info: {toc_info}",
            f"Host: {self.host}"
        ]
        attributes_str = '\n'.join(attributes)
        return (f"Novel Info: \n"
                f"{attributes_str}")

    @classmethod
    def load(cls, title: str, cfg: ScraperConfig, novel_base_dir: Path = None) -> 'Novel':
        """
        Loads a novel from stored JSON data.

        Args:
            title (str): Title of the novel to load.
            cfg (ScraperConfig): Scraper configuration.
            novel_base_dir (Path, optional): Base directory for the novel data.

        Returns:
            Novel: A new Novel instance loaded from stored data.

        Raises:
            ValidationError: If the novel with the given title is not found.
        """

        fm = FileManager(title, cfg.base_novels_dir, novel_base_dir, read_only=True)
        novel_data = fm.load_novel_data()
        if novel_data is None:
            logger.debug(f'Novel "{title}" was not found.')
            raise ValidationError(f'Novel "{title}" was not found.')
        try:
            novel = cls.from_dict(novel_data)
        except KeyError as e:
            msg= f'Error when loading novel with title "{title}". KeyError, check if the main.json is valid'
            logger.error(msg, exc_info=e)
            raise ValidationError(msg)
        novel.set_config(cfg=cfg, novel_base_dir=novel_base_dir)
        return novel

    @classmethod
    def new(cls, title: str, cfg: ScraperConfig, host: str = None, toc_html: str = None,
            toc_main_url: str = None) -> 'Novel':
        """Creates a new Novel instance.

        Args:
            title: Title of the novel (required)
            cfg: Scraper configuration (required)
            host: Host URL for the novel content (optional)
            toc_html: HTML content for the table of contents (optional)
            toc_main_url: URL for the table of contents (optional)

        Note:
            - Either toc_html or toc_main_url must be provided
            - If toc_main_url is provided, host will be extracted from it if not explicitly provided
            - If toc_html is provided, host must be explicitly provided

        Returns:
            Novel: A new Novel instance

        Raises:
            ValidationError: If the title is empty, or if neither toc_html nor toc_main_url is provided
        """
        if not title:
            raise ValidationError("Title cannot be empty")

        if not (toc_html or toc_main_url):
            raise ValidationError("Either toc_html or toc_main_url must be provided")

        if toc_html and not host:
            raise ValidationError("When providing toc_html, host must be explicitly provided")

        novel = cls(title=title, host=host, toc_main_url=toc_main_url)
        # If toc_main_url is provided and the host isn't, extract host from URL
        if toc_main_url and not host:
            host = utils.obtain_host(toc_main_url)
            novel.host = host

        # If toc_html is provided, add it to the novel
        if toc_html:
            novel.add_toc_html(toc_html, host)

        return novel

    # NOVEL PARAMETERS MANAGEMENT

    def set_config(self,
                   cfg: ScraperConfig,
                   novel_base_dir: str | None = None) -> None:
        """
        Configures the novel with the provided scraper configuration and base directory.

        Sets up the file manager and decoder for the novel based on the provided configuration.

        Args:
            cfg (ScraperConfig): The scraper configuration to use.
            novel_base_dir (str | None, optional): Base directory for the novel files.
                If None, it uses the default directory from configuration.

        Raises:
            FileManagerError: If there's an error when reading the config or decoding guide files.
        """

        try:
            self.config = cfg
            self.file_manager = FileManager(title=self.title,
                                            base_novels_dir=self.config.base_novels_dir,
                                            novel_base_dir=novel_base_dir)
            self.decoder = Decoder(self.host, self.config.decode_guide_file)
        except FileManagerError as e:
            logger.error("Could not set configuration. File Manager Error", exc_info=e)
            raise

    def set_scraper_behavior(self, **kwargs) -> None:
        """
        Updates the scraper behavior configuration with the provided parameters.

        Args:
            **kwargs: Keyword arguments for updating scraper behavior settings.
                Can include any valid ScraperBehavior attributes.
        """

        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        self.scraper_behavior = replace(self.scraper_behavior, **filtered_kwargs)
        logger.info(f'Scraper behavior updated')

    def set_metadata(self, **kwargs) -> None:
        """
        Updates the novel's metadata with the provided parameters.

        Args:
            **kwargs: Keyword arguments for updating metadata.
                Can include any valid Metadata attributes like author, language, etc.
        """
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        self.metadata = replace(self.metadata, **filtered_kwargs)
        logger.info(f'Metadata updated')

    def add_tag(self, tag: str) -> None:
        """
        Adds a new tag to the novel's metadata if it doesn't already exist.

        Args:
            tag (str): The tag to add to the novel's metadata.
        """

        if tag not in self.metadata.tags:
            self.metadata = replace(
                self.metadata, tags=(*self.metadata.tags, tag)
            )
            logger.info('Tag %s added to metadata', tag)
        else:
            logger.debug("Tag %s already present in %s", tag, self.title)

    def remove_tag(self, tag: str) -> None:
        """
        Removes a tag from the novel's metadata if it exists.

        Args:
            tag (str): The tag to remove from the novel's metadata.
        """

        if tag in self.metadata.tags:
            self.metadata = replace(self.metadata,
                                    tags=tuple(t for t in self.metadata.tags if t != tag))
            logger.info('Tag %s removed from metadata', tag)
        else:
            logger.debug("Tag %s not present in %s", tag, self.title)

    def set_cover_image(self, cover_image_path: str) -> None:
        """
        Sets or updates the novel's cover image.

        Args:
            cover_image_path (str): Path to the cover image file.

        Raises:
            FileManagerError: If there's an error when saving the cover image.
        """

        try:
            self.file_manager.save_novel_cover(cover_image_path)
            logger.info('Cover image updated')
        except FileManagerError as e:
            logger.error("Could not update cover. File Manager Error", exc_info=e)
            raise

    def set_host(self, host: str) -> None:
        """
        Sets or updates the novel's host URL and modifies the decoder.

        Args:
            host (str): The host URL for the novel.

        Raises:
            DecodeError: If there's an error when setting up the decoder with the new host.
        """

        self.host = host
        try:
            self.decoder.set_host(host)
            logger.info(f'Host updated to "{self.host}"')
        except ValidationError as e:
            logger.error("Could not set host. Decode Error", exc_info=e)
            raise

    def save_novel(self) -> None:
        """
        Saves the current state of the novel to disk.

        Persists all novel data including metadata, chapters, and configuration
        to the novel's JSON file.

        Raises:
            FileManagerError: If there's an error when saving the novel data.
        """

        try:
            self.file_manager.save_novel_data(self.to_dict())
            logger.info(f'Novel data saved to disk on file "{self.file_manager.novel_json_file}".')
        except FileManagerError as e:
            logger.error("Could not save novel. File Manager Error", exc_info=e)
            raise

    # TABLE OF CONTENTS MANAGEMENT

    def set_toc_main_url(self, toc_main_url: str, update_host: bool = True) -> None:
        """
        Sets the main URL for the table of contents and optionally updates the host.

        Deletes any existing TOC files as they will be refreshed from the new URL.
        If update_host is True, extracts and updates the host from the new URL.

        Args:
            toc_main_url: Main URL for the table of contents
            update_host: Whether to update the host based on the URL (default: True)

        Raises:
            ValidationError: If host extraction fails
            FileManagerError: If TOC deletion fails
        """

        self.toc_main_url = toc_main_url
        logger.info(f'Main URL updated to "{self.toc_main_url}", TOCs already requested will be deleted.')
        try:
            self.file_manager.delete_toc()
        except FileManagerError as e:
            logger.error("Could not delete TOCs. File Manager Error", exc_info=e)
            raise

        if update_host:
            new_host = utils.obtain_host(self.toc_main_url)
            logger.debug(f'Update Host flag present, new host is "{new_host}".')
            self.set_host(new_host)

    def add_toc_html(self, html: str, host: str = None) -> None:
        """
        Adds HTML content as a table of contents fragment.

        This method is mutually exclusive with using toc_main_url - if a main URL exists,
        it will be cleared. Host must be provided either directly or from a previous configuration.

        Args:
            html: HTML content to add as TOC fragment
            host: Optional host to set for this content

        Raises:
            ValidationError: If no host is provided when required
            FileManagerError: If saving TOC content fails
        """

        if self.toc_main_url:
            logger.debug(f'TOC main URL is exclusive with manual TOC files, TOC main URL will be deleted.')
            self.delete_toc()
            self.toc_main_url = None

        if host:
            self.set_host(host)
        else:
            if self.host is None:
                logger.error(f'When using TOC files instead of URLs, host must be provided.')
                raise ValidationError('Host must be provided when using TOC files instead of URLs.')
        self.file_manager.add_toc(html)
        logger.info('New TOC file added to disk.')

    def delete_toc(self):
        """
        Deletes all table of contents files and resets chapter data.

        Clears:
        - All TOC files from disk
        - Chapter list
        - Chapter URL list

        Raises:
            FileManagerError: If deletion of TOC files fails
        """

        self.file_manager.delete_toc()
        self.chapters = []
        self.chapters_url_list = []
        logger.info('TOC files deleted from disk.')

    def sync_toc(self, reload_files: bool = True) -> None:
        """
        Synchronizes the table of contents with stored/remote content.

        Process:
        1. Checks if TOC content exists (stored or retrievable)
        2. Optionally reloads TOC files from remote if needed
        3. Extracts chapter URLs from TOC content
        4. Creates/updates chapters based on URLs

        Args:
            reload_files: Whether to force reload of TOC files from remote (default: True)

        Raises:
            ScraperError: If no TOC content is available
            FileManagerError: If file operations fail
            DecodeError: If TOC parsing fails
            NetworkError: If remote content retrieval fails
            ValidationError: If chapter creation fails
        """

        all_tocs_content = self.file_manager.get_all_toc()

        # If there is no toc_main_url and no manually added toc, there is no way to sync toc
        toc_not_exists = not all_tocs_content and self.toc_main_url is None
        if toc_not_exists:
            logger.critical(
                'There is no toc html and no toc url set, unable to get toc.')
            raise ScraperError('There is no toc html and no toc url set, unable to get toc.')

        # Will reload files if:
        # Reload_files is True (requested by user) AND there is a toc_main_url present.
        # OR
        # There is a toc_main_url present, but no toc files are saved in the disk.
        reload_files = ((reload_files or
                         all_tocs_content is None) or
                        self.toc_main_url is not None)
        if reload_files:
            logger.debug('Reloading TOC files.')
            try:
                self._request_toc_files()
            except FileManagerError as e:
                logger.error("Could not request TOC files. File Manager Error", exc_info=e)
                raise
            except DecodeError as e:
                logger.error("Could not request TOC files. Decoder Error", exc_info=e)
                raise
            except NetworkError as e:
                logger.error("Could not request TOC files. Network Error", exc_info=e)
                raise

        try:
            self._load_or_request_chapter_urls_from_toc()
        except DecodeError as e:
            logger.error("Could not get chapter urls from TOC files. Decoder Error", exc_info=e)
            raise
        except FileManagerError as e:
            logger.error("Could not get chapter urls from TOC files. File Manager Error", exc_info=e)
            raise

        try:
            self._create_chapters_from_toc()
        except ValidationError as e:
            logger.error("Could not create chapters from TOC files. Validation Error", exc_info=e)
            raise
        logger.info('TOC synced with files, Chapters created from Table of Contents.')

    def show_toc(self) -> Optional[str]:
        """
        Generates a human-readable representation of the Table Of Contents.

        Returns:
            Optional[str]: Formatted string showing chapter numbers and URLs, None if no chapters_urls found
        """

        if not self.chapters_url_list:
            logger.warning('No chapters in TOC')
            return None
        toc_str = 'Table Of Contents:'
        for i, chapter_url in enumerate(self.chapters_url_list):
            toc_str += f'\nChapter {i + 1}: {chapter_url}'
        return toc_str

    # CHAPTERS MANAGEMENT

    def get_chapter(self, chapter_index: Optional[int] = None, chapter_url: Optional[str] = None) -> Optional[Chapter]:
        """
        Retrieves a chapter either by its index in the chapter list or by its URL.

        Args:
            chapter_index (Optional[int]): The index of the chapter in the chapter list
            chapter_url (Optional[str]): The URL of the chapter to retrieve

        Returns:
            Optional[Chapter]: The requested chapter if found, None otherwise

        Raises:
            ValidationError: If neither index nor url is provided, or if both are provided
            IndexError: If the provided index is out of range
        """
        if not utils.check_exclusive_params(chapter_index, chapter_url):
            raise ValidationError("Exactly one of 'chapter_index' or 'chapter_url' must be provided")

        if chapter_url is not None:
            chapter_index = self._find_chapter_index_by_url(chapter_url)

        if chapter_index is not None:
            if chapter_index < 0:
                raise ValueError("Index must be positive")
            try:
                return self.chapters[chapter_index]
            except IndexError:
                logger.warning(f"No chapter found at index {chapter_index}")
                return None
        logger.warning(f"No chapter found with url {chapter_url}")
        return None

    def show_chapters(self) -> str:
        """
        Generates a text representation of all novel chapters.

        Returns:
            str: Formatted string containing the list of chapters with their information:
                - Chapter number
                - Title (if available)
                - URL
                - HTML filename (if available)

        Note:
            Output format is:
            Chapters List:
            Chapter 1:
              Title: [title or message]
              URL: [url]
              Filename: [filename or message]
            ...
        """

        chapter_list = "Chapters List:\n"
        for i, chapter in enumerate(self.chapters):
            chapter_list += f"Chapter {i + 1}:\n"
            chapter_list += f"  Title: {chapter.chapter_title if chapter.chapter_title else 'Title not yet scrapped'}\n"
            chapter_list += f"  URL: {chapter.chapter_url}\n"
            chapter_list += f"  Filename: {chapter.chapter_html_filename if chapter.chapter_html_filename else 'File not yet requested'}\n"
        return chapter_list

    def scrap_chapter(self, chapter: Chapter, reload_file: bool = False) -> Chapter:
        """
        Processes and decodes a specific chapter of the novel.

        This method handles the complete scraping process for an individual chapter,
        including HTML loading or requesting and content decoding.

        Args:
            chapter (Chapter): Chapter object to process
            reload_file (bool, optional): If True, forces a new download of the chapter
                even if it already exists locally. Defaults to False.

        Returns:
            Chapter: The updated Chapter object with decoded content

        Raises:
            ValidationError: If there are issues with the values of the provided Chapter object
            DecodeError: If there are issues during content decoding
            NetworkError: If there are issues during HTML request
            FileManagerError: If there are issues during file operations
        """

        logger.debug('Scraping Chapter...')
        if chapter.chapter_url is None:
            logger.error('Chapter trying to be scrapped does not have a URL')
            raise ValidationError('Chapter trying to be scrapped does not have a URL')

        logger.debug(f'Using chapter url: {chapter.chapter_url}')

        if reload_file:
            logger.debug('Reload file Flag present, HTML will be requested...')

        try:
            chapter = self._load_or_request_chapter(chapter,
                                                    reload_file=reload_file)
        except ValidationError as e:
            logger.error(f'Could get chapter for URL "{chapter.chapter_url}" HTML content. Validation Error',
                         exc_info=e)
            raise
        except FileManagerError as e:
            logger.error(f'Could get chapter for URL "{chapter.chapter_url}" HTML content. File Manager Error',
                         exc_info=e)
            raise
        except NetworkError as e:
            logger.error(f'Could get chapter for URL "{chapter.chapter_url}" HTML content. Network Error', exc_info=e)
            raise

        if not chapter.chapter_html:
            logger.error(f'Could not get HTML content for chapter with URL "{chapter.chapter_url}"')
            raise ScraperError(f'Could not get HTML content for chapter with URL "{chapter.chapter_url}"')

        # We get the chapter title and content
        # We pass an index so we can autogenerate a Title
        save_title_to_content = (self.scraper_behavior.save_title_to_content or
                                 self.decoder.save_title_to_content())
        try:
            chapter = self._decode_chapter(chapter=chapter,
                                           save_title_to_content=save_title_to_content)
        except DecodeError as e:
            logger.error(f'Could not decode HTML title and content for chapter with URL "{chapter.chapter_url}"',
                         exc_info=e)
            raise
        except ValidationError as e:
            logger.error(f'Could not decode HTML title and content for chapter with URL "{chapter.chapter_url}"',
                         exc_info=e)
            raise

        logger.info(f'Chapter scrapped from link: {chapter.chapter_url}')
        return chapter

    def request_all_chapters(self,
                             sync_toc: bool = True,
                             reload_files: bool = False,
                             clean_chapters: bool = False) -> None:
        """
        Requests and processes all chapters of the novel.

        This method performs scraping of all available chapters in the novel,
        handling the loading and decoding of each one.

        Args:
            sync_toc (bool, optional): If True, syncs the table of contents
            reload_files (bool, optional): If True, forces a new download of all
                chapters, even if they already exist locally. Defaults to False.
            clean_chapters (bool, optional): If True, cleans the HTML content of the files

        Raises:
            FileManagerError: If there are issues during file operations
            DecodeError: If there are issues during content decoding
            ValidationError: If there are issues during content decoding

        Note:
            - Process is performed sequentially for each chapter
            - Errors in individual chapters don't stop the complete process
            - Progress is logged through the logging system
        """

        logger.debug('Requesting all chapters...')
        if sync_toc:
            logger.debug('Sync TOC flag present, syncing TOC...')
            try:
                self.sync_toc(reload_files=False)
            except ScraperError:
                logger.warning('Error when trying to sync TOC, continuing without syncing...')

        if len(self.chapters_url_list) == 0:
            logger.warning('No chapters in TOC, returning without requesting any...')
            return None

        # We request the HTML files of all the chapters
        # The chapter will be requested again if:
        # 1. Reload files flag is True (Requested by user)
        # 2. Chapter doesn't have a chapter_html_filename, or the HTML file does not exist
        chapters_obtained = 0
        total_chapters = len(self.chapters)
        for i in range(len(self.chapters)):
            request_chapter = reload_files
            if self.chapters[i].chapter_html_filename is None:
                logger.debug(f'No HTML file name for chapter {i + 1} of {total_chapters}, requesting...')
                request_chapter = True
            else:
                chapter_file_exists = self.file_manager.chapter_file_exists(chapter_filename=self.chapters[i].chapter_html_filename)
                if not chapter_file_exists:
                    logger.debug(f'File for chapter {i + 1} of {total_chapters} does not exist, requesting...')
                    request_chapter = True

            if request_chapter:
                logger.info(f'Requesting chapter {i + 1} of {total_chapters}')
                try:
                    self.chapters[i] = self._load_or_request_chapter(chapter=self.chapters[i],
                                                                     reload_file=reload_files)
                except FileManagerError:
                    logger.warning(f'Error requesting chapter {i + 1} with url {self.chapters[i].chapter_url}, Skipping...')
                    continue
                except ValidationError:
                    logger.warning(f'Error validating chapter {i + 1} with url {self.chapters[i].chapter_url}, Skipping...')
                    continue
                except NetworkError:
                    logger.warning(f'Error requesting chapter {i + 1} with url {self.chapters[i].chapter_url}, Skipping...')
                    continue

                if not self.chapters[i].chapter_html:
                    logger.warning(f'Error requesting chapter {i + 1} with url {self.chapters[i].chapter_url}')
                    continue

                if clean_chapters:
                    self._clean_chapter(self.chapters[i].chapter_html_filename)
                try:
                    self.save_novel()
                except FileManagerError:
                    logger.warning(f'Error when trying to save novel data, Skipping...')
            else:
                logger.debug(f'Chapter {i + 1} of {total_chapters} already requested, skipping...')
            chapters_obtained += 1
        logger.info(f'Successfully requested {chapters_obtained} of {total_chapters} chapters.')
        return None

    # EPUB CREATION

    def save_novel_to_epub(self,
                           sync_toc: bool = False,
                           start_chapter: int = 1,
                           end_chapter: int = None,
                           chapters_by_book: int = 100) -> None:
        logger.debug('Saving novel to epub...')
        if sync_toc:
            logger.debug('Sync TOC flag present, syncing TOC...')
            try:
                self.sync_toc(reload_files=False)
            except ScraperError:
                logger.warning('Error when trying to sync TOC, continuing without syncing...')

        if start_chapter < 1:
            logger.error('Start chapter is invalid.')
            raise ValidationError('Start chapter is invalid.')

        if start_chapter > len(self.chapters):
            logger.error(f'The start chapter is bigger than the number of chapters saved ({len(self.chapters)})')
            raise ValidationError(
                f'The start chapter is bigger than the number of chapters saved ({len(self.chapters)})')

        if not end_chapter:
            end_chapter = len(self.chapters)
        elif end_chapter > len(self.chapters):
            end_chapter = len(self.chapters)
            logger.info(f'The end chapter is bigger than the number of chapters, '
                        f'automatically setting it to {end_chapter}.')

        idx = 1
        start = start_chapter
        while start <= end_chapter:
            end = min(start + chapters_by_book - 1,
                      end_chapter)
            result = self._save_chapters_to_epub(start_chapter=start,
                                                 end_chapter=end,
                                                 collection_idx=idx)
            if not result:
                logger.critical(f'Error with saving novel to epub, with start chapter: '
                                f'{start_chapter} and end chapter: {end_chapter}')
            start = start + chapters_by_book
            idx = idx + 1

    ## UTILS

    def clean_files(self, clean_chapters: bool = True, clean_toc: bool = True, hard_clean: bool = False) -> None:
        hard_clean = hard_clean or self.scraper_behavior.hard_clean
        if clean_chapters:
            for chapter in self.chapters:
                if chapter.chapter_html_filename:
                    self._clean_chapter(
                        chapter.chapter_html_filename, hard_clean)
        if clean_toc:
            self._clean_toc(hard_clean)

    def show_novel_dir(self) -> str:
        return str(self.file_manager.novel_base_dir)

    ## PRIVATE HELPERS

    def _clean_chapter(self, chapter_html_filename: str, hard_clean: bool = False) -> None:
        hard_clean = hard_clean or self.scraper_behavior.hard_clean
        chapter_html = self.file_manager.load_chapter_html(
            chapter_html_filename)
        if not chapter_html:
            logger.warning(f'No content found on file {chapter_html_filename}')
            return
        chapter_html = self.decoder.clean_html(
            chapter_html, hard_clean=hard_clean)
        self.file_manager.save_chapter_html(
            chapter_html_filename, chapter_html)

    def _clean_toc(self, hard_clean: bool = False) -> None:
        hard_clean = hard_clean or self.scraper_behavior.hard_clean
        tocs_content = self.file_manager.get_all_toc()
        for i, toc in enumerate(tocs_content):
            toc = self.decoder.clean_html(toc, hard_clean=hard_clean)
            self.file_manager.update_toc(idx=i,
                                         html=toc)

    def _request_html_content(self, url: str) -> Optional[str]:
        """
        Performs an HTTP request to retrieve HTML content from a URL.

        Args:
            url (str): The URL of the webpage to request

        Returns:
            Optional[str]: The HTML content of the webpage if the request is successful,
                          None otherwise

        Note:
            This method uses the decoder configuration and scraper behavior
            to handle HTTP requests, including retries and timeouts.
        """

        request_config = self.decoder.request_config
        force_flaresolver = request_config.get('force_flaresolver') or self.scraper_behavior.force_flaresolver
        html_content = get_html_content(url,
                                        retries=request_config.get('request_retries'),
                                        timeout=request_config.get('request_timeout'),
                                        time_between_retries=request_config.get('request_time_between_retries'),
                                        force_flaresolver=force_flaresolver)
        return html_content

    def _load_or_request_chapter(self,
                                 chapter: Chapter,
                                 reload_file: bool = False) -> Chapter:
        """
        Loads or requests a chapter's HTML content from a local file or a URL.

        This method first attempts to load the chapter content from a local file.
        If not possible or if reload is requested, it fetches the content from the web.

        Args:
            chapter (Chapter): Chapter object containing chapter information.
            reload_file (bool, optional): If True, forces a new web request
                regardless of local file existence. Defaults to False.

        Returns:
            Chapter: The Chapter object updated with HTML content.

        Raises:
            FileManagerError: If there's an error loading or saving the chapter file.
            ValidationError: If there's a validation error when requesting the chapter.
            NetworkError: If there's a network error when requesting the chapter.

        Note:
            - If the file doesn't exist locally, a web request will be made.
            - If the file exists but is empty, a web request will be made.
            - File saving errors are logged as warnings but don't stop execution.
        """

        # Generate a filename if needed
        if not chapter.chapter_html_filename:
            logger.debug('Generating a filename for the chapter')
            chapter.chapter_html_filename = utils.generate_file_name_from_url(
                chapter.chapter_url)

        # The HTML will be requested again if:
        # 1. "Reload file" flag is True (requested by user)
        # 2. Chapter file does not exist
        # 3. The Chapter file does exist, but there is no content
        reload_file = reload_file or not self.file_manager.chapter_file_exists(chapter.chapter_html_filename)
        # Try loading from the disk first
        if not reload_file:
            try:
                logger.debug(f'Loading chapter HTML from file: "{chapter.chapter_html_filename}"')
                chapter.chapter_html = self.file_manager.load_chapter_html(chapter.chapter_html_filename)
            except FileManagerError as e:
                logger.error(f'Error when trying to load chapter {chapter.chapter_title} from file', exc_info=e)
                raise
            if chapter.chapter_html is not None:
                return chapter

        # Fetch fresh content
        try:
            logger.debug(f'Requesting chapter HTML from URL: "{chapter.chapter_url}"')
            chapter.chapter_html = self._request_html_content(chapter.chapter_url)
        except ValidationError:
            logger.error(
                f'Error when trying to request chapter {chapter.chapter_title} from url: {chapter.chapter_url}')
            raise
        except NetworkError:
            logger.error(
                f'Error when trying to request chapter {chapter.chapter_title} from url: {chapter.chapter_url}')
            raise

        # If the requests failed, we will let the higher methods decide if they throw an error.
        if not chapter.chapter_html:
            logger.error(f'No content found on link {chapter.chapter_url}')
            return chapter

        # Save content
        try:
            logger.info(f'Saving chapter HTML to file: "{chapter.chapter_html_filename}"')
            self.file_manager.save_chapter_html(chapter.chapter_html_filename,
                                                chapter.chapter_html)
        except FileManagerError as e:
            # We can pass this error and try again later
            logger.warning(f'Error when trying to save chapter {chapter.chapter_title} to file', exc_info=e)

        return chapter

    def _request_toc_files(self):
        """
        Requests and stores all table of contents (TOC) files from the novel's website.

        This method handles both paginated and non-paginated TOCs:
        - For non-paginated TOCs: Downloads and stores a single TOC file
        - For paginated TOCs: Iteratively downloads all TOC pages until no next page is found

        The method first clears any existing TOC files before downloading new ones.

        Raises:
            NetworkError: If there's an error during the HTTP request
            ValidationError: If no content is found at the TOC URL
            DecodeError: If there's an error parsing the next page URL

        Note:
            This is an internal method that uses the decoder configuration to determine
            pagination behavior and to parse TOC content.
        """

        def _get_toc(toc_url: str, get_next_page: bool) -> str | None:
            # Some TOCs next page links have incomplete URLS (e.g., /page/2)
            if utils.check_incomplete_url(toc_url):
                toc_url = self.toc_main_url + toc_url
                logger.debug(f'Toc link is incomplete, trying with toc link: "{toc_url}"')

            # Fetch fresh content
            logger.debug(f'Requesting TOC from link: "{toc_url}"')
            try:
                toc_content = self._request_html_content(toc_url)
            except NetworkError as E:
                logger.error(f'Error with network, error: {E}')
                raise

            if not toc_content:
                logger.error(f'No content found on link "{toc_url}"')
                raise ValidationError(f'No content found on link "{toc_url}"')

            logger.debug('Saving new TOC file to disk.')
            self.file_manager.add_toc(toc_content)

            if get_next_page:
                try:
                    logger.debug(f'Parsing next page from link: {toc_url}')
                    next_page = self.decoder.get_toc_next_page_url(toc_content)
                except DecodeError:
                    raise
                return next_page
            return None

        self.file_manager.delete_toc()
        has_pagination = self.decoder.has_pagination()
        try:
            toc_main_url = self.decoder.toc_main_url_process(self.toc_main_url)
        except DecodeError:
            logger.debug('Error when trying to preprocess toc main url')
            raise
        if not has_pagination:
            logger.debug('TOC does not have pagination, requesting only one file.')
            _get_toc(toc_main_url, get_next_page=False)
        else:
            logger.debug('TOC has pagination, requesting all files.')
            next_page_url = toc_main_url
            while next_page_url:
                next_page_url = _get_toc(next_page_url, get_next_page=True)

    def _load_or_request_chapter_urls_from_toc(self) -> None:
        """
        Extracts and processes chapter URLs from the table of contents.

        Raises:
            DecodeError: If fails to decode chapter URLs from TOC content
        """
        # Get configuration
        is_inverted = self.decoder.is_index_inverted()
        add_host_to_chapter = self.scraper_behavior.auto_add_host or self.decoder.add_host_to_chapter()

        # Get all TOC content at once
        try:
            all_tocs = self.file_manager.get_all_toc()
        except FileManagerError:
            logger.error('Error when trying to load TOC files from disk.')
            raise

        # Extract URLs from all TOC fragments
        self.chapters_url_list = []
        for toc_content in all_tocs:
            try:
                urls = self.decoder.get_chapter_urls(toc_content)
                self.chapters_url_list.extend(urls)
            except DecodeError as e:
                logger.error('Failed to decode chapter URLs from TOC content', exc_info=e)
                raise

        # Handle inversion if needed
        if is_inverted:
            logger.debug('Inverting chapter URLs order')
            self.chapters_url_list.reverse()

            # Add host if needed
        if add_host_to_chapter:
            logger.debug('Adding host to chapter URLs')
            self.chapters_url_list = [f'https://{self.host}{url}' for url in self.chapters_url_list]

            # Remove duplicates while preserving order
            # self.chapters_url_list = utils.delete_duplicates(self.chapters_url_list)

        logger.info(f'Successfully extracted {len(self.chapters_url_list)} unique chapter URLs')

    def _create_chapters_from_toc(self):
        """
        Synchronizes existing chapters with the table of contents (TOC) URL list.

        This method performs the following operations:
        1. Removes chapters whose URLs are no longer in the TOC
        2. Adds new chapters for URLs found in the TOC
        3. Reorders chapters according to the TOC sequence

        Raises:
            ValidationError: If there's an error when creating a new chapter

        Note:
            This is an internal method used to maintain consistency
            between chapters and the table of contents.
        """

        existing_urls = {chapter.chapter_url for chapter in self.chapters}
        toc_urls_set = set(self.chapters_url_list)

        # Find chapters to remove and new chapters to add
        urls_to_remove = existing_urls - toc_urls_set
        urls_to_add = toc_urls_set - existing_urls

        if urls_to_remove:
            logger.info(f'Removing {len(urls_to_remove)} chapters not found in TOC')
            self.chapters = [ch for ch in self.chapters if ch.chapter_url not in urls_to_remove]

        if urls_to_add:
            logger.info(f'Adding {len(urls_to_add)} new chapters from TOC')
            for url in self.chapters_url_list:
                if url in urls_to_add:
                    try:
                        new_chapter = Chapter(chapter_url=url)
                        self.chapters.append(new_chapter)
                    except ValidationError as e:
                        logger.error(f'Failed to create chapter for URL {url}: {e}')
                        raise

        # Reorder according to TOC
        logger.debug('Reordering chapters according to TOC')
        self.chapters.sort(
            key=lambda x: self.chapters_url_list.index(x.chapter_url))

        logger.info(f'Chapter synchronization complete. Total chapters: {len(self.chapters)}')

    def _add_or_update_chapter_data(self, chapter: Chapter, save_in_file: bool = True) -> None:

        # Check if the chapter exists
        chapter_idx = self._find_chapter_index_by_url(chapter.chapter_url)
        if chapter_idx is None:
            # If no existing chapter, we append it
            self.chapters.append(chapter)
        else:
            if chapter.chapter_title:
                self.chapters[chapter_idx].chapter_title = chapter.chapter_title
            if chapter.chapter_html_filename:
                self.chapters[chapter_idx].chapter_html_filename = chapter.chapter_html_filename

        if save_in_file:
            self.save_novel()

    def _find_chapter_index_by_url(self, chapter_url: str) -> Optional[int]:
        """
        Find the chapter index by its URL in the chapter list.

        Args:
            chapter_url: URL of the chapter to find

        Returns:
            Optional[int]: Index of the chapter if found, None otherwise

        Note:
            Uses next() for efficient iteration - stops as soon as a match is found
        """
        try:
            return next(i for i, ch in enumerate(self.chapters)
                        if ch.chapter_url == chapter_url)
        except StopIteration:
            return None

    def _decode_chapter(self,
                        chapter: Chapter,
                        save_title_to_content: bool = False) -> Chapter:
        """
        Decodes a chapter's HTML content to extract title and content.

        This method processes the HTML content of a chapter to extract its title and content.
        If no title is found, it auto-generates one using the chapter's index in the URL list.

        Args:
            chapter (Chapter): Chapter object containing the HTML content to decode.
            save_title_to_content (bool, optional): Whether to include the title in the
                chapter content. Defaults to False.

        Returns:
            Chapter: The updated Chapter object with decoded title and content.

        Raises:
            ScraperError: If the chapter's HTML content is None.
            DecodeError: If there's an error decoding the chapter's title or content.

        Note:
            - If no title is found, it will be auto-generated as "{novel_title} Chapter {index}".
            - The chapter's HTML must be loaded before calling this method.
        """

        logger.debug(f'Decoding chapter with URL {chapter.chapter_url}...')
        if chapter.chapter_html is None:
            logger.error(f'Chapter HTML not found for chapter with URL "{chapter.chapter_url}"')
            raise ScraperError(f'Chapter HTML not found for chapter with URL "{chapter.chapter_url}"')

        logger.debug('Obtaining chapter title...')
        try:
            chapter_title = self.decoder.get_chapter_title(chapter.chapter_html)
        except DecodeError as e:
            logger.error(f'Failed to decode chapter title from HTML content: {e}')
            raise

        if chapter_title is None:
            logger.debug('No chapter title found, trying to autogenerate one...')
            try:
                chapter_idx = self.chapters_url_list.index(chapter.chapter_url)
            except ValueError:
                chapter_idx = ""

            chapter_title = f'{self.title} Chapter {chapter_idx}'

        chapter.chapter_title = chapter_title
        logger.info(f'Chapter title: "{chapter_title}"')

        logger.debug('Obtaining chapter content...')
        try:
            chapter.chapter_content = self.decoder.get_chapter_content(chapter.chapter_html,
                                                                       save_title_to_content,
                                                                       chapter.chapter_title)
        except DecodeError:
            logger.error(f'Failed to decode chapter content for chapter with URL "{chapter.chapter_url}"')
            raise

        logger.debug('Chapter title and content successfully decoded from HTML')
        return chapter

    def _create_epub_book(self, book_title: str = None, calibre_collection: dict = None) -> epub.EpubBook:
        book = epub.EpubBook()
        if not book_title:
            book_title = self.title
        book.set_title(book_title)
        book.set_language(self.metadata.language)
        book.add_metadata('DC', 'description', self.metadata.description)
        book.add_metadata('DC', 'subject', 'Novela Web')
        book.add_metadata('DC', 'subject', 'Scrapped')
        if self.metadata.tags:
            for tag in self.metadata.tags:
                book.add_metadata('DC', 'subject', tag)

        if self.metadata.author:
            book.add_author(self.metadata.author)

        date_metadata = ''
        if self.metadata.start_date:
            date_metadata += self.metadata.start_date
        # Calibre specification doesn't use end_date.
        # For now, we use a custom metadata
        # https://idpf.org/epub/31/spec/epub-packages.html#sec-opf-dcdate
        # if self.metadata.end_date:
        #     date_metadata += f'/{self.metadata.end_date}'
        if self.metadata.end_date:
            book.add_metadata('OPF', 'meta', self.metadata.end_date, {
                'name': 'end_date', 'content': self.metadata.end_date})
        if date_metadata:
            logger.debug(f'Using date_metadata {date_metadata}')
            book.add_metadata('DC', 'date', date_metadata)

        # Collections with calibre
        if calibre_collection:
            book.add_metadata('OPF', 'meta', '', {
                'name': 'calibre:series', 'content': calibre_collection["title"]})
            book.add_metadata('OPF', 'meta', '', {
                'name': 'calibre:series_index', 'content': calibre_collection["idx"]})

        cover_image_content = self.file_manager.load_novel_cover()
        if cover_image_content:
            book.set_cover('cover.jpg', cover_image_content)
            book.spine += ['cover']

        book.spine.append('nav')
        return book

    def _add_chapter_to_epub_book(self, chapter: Chapter, book: epub.EpubBook):
        chapter = self.scrap_chapter(chapter)
        if chapter is None:
            logger.warning('Error reading chapter')
            return None
        self._add_or_update_chapter_data(
            chapter=chapter, save_in_file=False)
        file_name = utils.generate_epub_file_name_from_title(
            chapter.chapter_title)

        chapter_epub = epub.EpubHtml(
            title=chapter.chapter_title, file_name=file_name)
        chapter_epub.set_content(chapter.chapter_content)
        book.add_item(chapter_epub)
        link = epub.Link(file_name, chapter.chapter_title,
                         file_name.rstrip('.xhtml'))
        toc = book.toc
        toc.append(link)
        book.toc = toc
        book.spine.append(chapter_epub)
        return book

    def _save_chapters_to_epub(self,
                               start_chapter: int,
                               end_chapter: int = None,
                               collection_idx: int = None):
        if start_chapter > len(self.chapters):
            logger.error('start_chapter out of range')
            return None
        # If end_chapter is not set, we set it to idx_start + chapters_num - 1
        if not end_chapter:
            end_chapter = len(self.chapters)
        # If end_chapter is out of range, we set it to the last chapter
        if end_chapter > len(self.chapters):
            end_chapter = len(self.chapters)

        # We use a slice so every chapter starting from idx_start and before idx_end
        idx_start = start_chapter - 1
        idx_end = end_chapter
        # We create the epub book
        book_title = f'{self.title} Chapters {start_chapter} - {end_chapter}'
        calibre_collection = None
        # If collection_idx is set, we create a Calibre collection
        if collection_idx:
            calibre_collection = {'title': self.title,
                                  'idx': str(collection_idx)}
        book = self._create_epub_book(book_title, calibre_collection)

        for chapter in self.chapters[idx_start:idx_end]:
            book = self._add_chapter_to_epub_book(chapter=chapter,
                                                  book=book)
            if book is None:
                logger.critical(
                    f'Error saving epub {book_title}, could not decode chapter {chapter} using host {self.host}')
                return False

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        try:
            self.file_manager.save_book(book, f'{book_title}.epub')
        except FileManagerError:
            logger.error(f'Error saving epub {book_title}')
            raise
        self.save_novel()
        return True
