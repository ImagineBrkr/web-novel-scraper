from dataclasses import dataclass, field, replace

from dataclasses_json import dataclass_json, Undefined, config
from typing import Optional
from pathlib import Path

from web_novel_scraper import logger_manager
from web_novel_scraper.io_helpers.novel_base_dir_helper import NovelBaseDirHelper
from web_novel_scraper.io_helpers.novel_data_helper import NovelDataHelper
from web_novel_scraper.decode import Decoder
from web_novel_scraper import utils
from web_novel_scraper.request_helper import RequestHelper
from web_novel_scraper.config import (
    get_active_scraper_config,
    set_active_scraper_config,
)
from web_novel_scraper.models import ScraperBehavior, Metadata, Chapter
from web_novel_scraper.utils import (
    _always,
    TitleInContentOption,
)
from web_novel_scraper.exceptions import (
    RequestError,
    ScraperError,
    ValidationError,
    DecodeError,
    DecodeGuideError,
    NovelBaseDirError,
    LoadNovelDataError,
    NovelDataNotFoundError,
    NovelNotFoundError,
    NovelDataError,
    ChapterFileNotFoundError,
    ChapterFileIsEmptyError,
)


logger = logger_manager.create_logger(__name__)


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
        toc_main_url (str): The main URL for the table of contents.
        chapters (list[Chapter]): List of chapters in the novel.
        chapters_url_list (list[str]): List of URLs for all chapters.
        metadata (Metadata): Novel metadata like author, language, etc.
        scraper_behavior (ScraperBehavior): Configuration for scraping behavior.
        decoder (Decoder): Handles HTML decoding and parsing.
        config (ScraperConfig): General scraper configuration.
    """

    title: str
    toc_main_url: str
    host: Optional[str] = None
    chapters: list[Chapter] = field(default_factory=list)
    chapters_url_list: list[str] = field(default_factory=list)
    metadata: Metadata = field(default_factory=Metadata)
    scraper_behavior: ScraperBehavior = field(default_factory=ScraperBehavior)

    novel_data_helper: Optional[NovelDataHelper] = field(
        default=None, repr=False, compare=False, metadata=config(exclude=_always)
    )
    decoder: Optional[Decoder] = field(
        default=None, repr=False, compare=False, metadata=config(exclude=_always)
    )

    def __post_init__(self):
        """
        Validates the novel instance after initialization.

        Raises:
            ValidationError: If the title is empty or toc_main_url is not provided.
        """

        if not self.title:
            raise ValidationError("title can't be empty")
        if not self.toc_main_url:
            raise ValidationError('You must provide a "toc_main_url"')

    def __str__(self):
        """
        Returns a string representation of the novel with its main attributes.

        Returns:
            str: A formatted string containing the novel's main information.
        """

        attributes = [
            f"Title: {self.title}",
            f"Author: {self.metadata.author}",
            f"Language: {self.metadata.language}",
            f"Description: {self.metadata.description}",
            f"Tags: {', '.join(self.metadata.tags)}",
            f"TOC Main URL: {self.toc_main_url}",
            f"Host: {self.host}",
        ]
        attributes_str = "\n".join(attributes)
        return f"Novel Info: \n{attributes_str}"

    @classmethod
    def load(
        cls,
        title: str,
        novel_base_dir: Path = None,
    ) -> "Novel":

        scraper_config = get_active_scraper_config()

        if novel_base_dir is None:
            try:
                novel_base_dir = NovelBaseDirHelper.get_novel_base_dir_from_meta(
                    title=title,
                    base_novels_dir=scraper_config.config_options["base_novels_dir"],
                )
            except NovelBaseDirError as e:
                logger.debug("Traceback:", exc_info=True)
                raise ScraperError(e) from e

            if novel_base_dir is None:
                raise NovelNotFoundError(
                    f"Novel with Title {title} not found on base_novels_dir {scraper_config.config_options['base_novels_dir']}"
                )

        try:
            novel_data = NovelDataHelper.load_novel_data(novel_base_dir)

        except NovelDataNotFoundError:
            logger.debug(f"Novel Data File not found on {novel_base_dir}")
            raise NovelNotFoundError(f"Novel data not found on {novel_base_dir}")

        except LoadNovelDataError as e:
            logger.debug("Traceback:", exc_info=True)
            raise ScraperError(e) from e

        try:
            novel = cls.from_dict(novel_data)
        except KeyError as e:
            logger.debug("Traceback: ", exc_info=True)
            raise ScraperError(
                f"Invalid Novel Data on Novel Data File {novel_base_dir}."
            ) from e

        scraper_config.set_host(host=novel.host)
        set_active_scraper_config(scraper_config)

        novel.novel_data_helper = NovelDataHelper(novel_base_dir=novel_base_dir)

        try:
            novel.decoder = Decoder(novel.host)

        except DecodeGuideError as e:
            logger.debug("Traceback: ", exc_info=True)
            raise ScraperError(e) from e

        return novel

    @classmethod
    def new(
        cls,
        title: str,
        toc_main_url: str,
        host: str = None,
        novel_base_dir: str = None,
    ) -> "Novel":

        scraper_config = get_active_scraper_config()

        novel = cls(title=title, host=host, toc_main_url=toc_main_url)

        # If toc_main_url is provided and the host isn't, extract host from URL
        if toc_main_url and not host:
            host = utils.obtain_host(toc_main_url)
            novel.host = host
        scraper_config.set_host(host=novel.host)
        set_active_scraper_config(scraper_config)
        try:
            Decoder(host=novel.host)
        except DecodeGuideError as e:
            logger.debug("Traceback:", exc_info=True)
            raise ScraperError(e) from e

        if novel_base_dir is None:
            try:
                novel_base_dir = NovelBaseDirHelper.get_novel_base_dir_from_meta(
                    title=title,
                    base_novels_dir=scraper_config.config_options["base_novels_dir"],
                )
            except NovelBaseDirError as e:
                logger.debug("Traceback:", exc_info=True)
                raise ScraperError(e) from e

        if novel_base_dir is None:
            novel_base_dir = NovelBaseDirHelper.generate_novel_base_dir(
                novel.title, scraper_config.config_options["base_novels_dir"]
            )
            NovelBaseDirHelper.save_novel_dir_to_meta(
                novel.title,
                novel_base_dir,
                scraper_config.config_options["base_novels_dir"],
            )

        try:
            novel.novel_data_helper = NovelDataHelper(novel_base_dir=novel_base_dir)
        except NovelBaseDirError as e:
            logger.debug("Traceback:", exc_info=True)
            raise ScraperError(e) from e

        return novel

    # NOVEL PARAMETERS MANAGEMENT

    def save_novel(self) -> None:

        try:
            self.novel_data_helper.save_novel_data(self.to_dict())
        except NovelDataError as e:
            logger.error("Traceback", exc_info=e)
            raise ScraperError(e) from e

    def set_scraper_behavior(self, **kwargs) -> None:
        """
        Updates the scraper behavior configuration with the provided parameters.

        Args:
            **kwargs: Keyword arguments for updating scraper behavior settings.
                Can include any valid ScraperBehavior attributes.
        """

        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        if "title_in_content" in filtered_kwargs:
            try:
                filtered_kwargs["title_in_content"] = TitleInContentOption[
                    filtered_kwargs["title_in_content"]
                ]
            except KeyError:
                raise ValidationError(
                    f"Invalid value for 'title_in_content' option: {filtered_kwargs['title_in_content']}"
                )
        self.scraper_behavior = replace(self.scraper_behavior, **filtered_kwargs)
        logger.info("Scraper behavior updated")

    def set_metadata(self, **kwargs) -> None:
        """
        Updates the novel's metadata with the provided parameters.

        Args:
            **kwargs: Keyword arguments for updating metadata.
                Can include any valid Metadata attributes like author, language, etc.
        """
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        self.metadata = replace(self.metadata, **filtered_kwargs)
        logger.info("Metadata updated")

    def add_tag(self, tag: str) -> None:
        """
        Adds a new tag to the novel's metadata if it doesn't already exist.

        Args:
            tag (str): The tag to add to the novel's metadata.
        """

        if tag not in self.metadata.tags:
            self.metadata = replace(self.metadata, tags=(*self.metadata.tags, tag))
            logger.info("Tag %s added to metadata", tag)
        else:
            logger.debug("Tag %s already present in %s", tag, self.title)

    def remove_tag(self, tag: str) -> None:
        """
        Removes a tag from the novel's metadata if it exists.

        Args:
            tag (str): The tag to remove from the novel's metadata.
        """

        if tag in self.metadata.tags:
            self.metadata = replace(
                self.metadata, tags=tuple(t for t in self.metadata.tags if t != tag)
            )
            logger.info("Tag %s removed from metadata", tag)
        else:
            logger.debug("Tag %s not present in %s", tag, self.title)

    def set_cover_image(self, cover_image_path: str) -> None:
        """
        Sets or updates the novel's cover image.

        Args:
            cover_image_path (str): Path to the cover image file.
        """

        try:
            self.novel_data_helper.save_novel_cover(cover_image_path)
            logger.info("Cover image updated")
        except NovelDataError as e:
            logger.debug("Traceback: ", exc_info=True)
            raise ScraperError(e) from e

    def set_host(self, host: str) -> None:
        """
        Sets or updates the novel's host URL and modifies the decoder.

        Args:
            host (str): The host URL for the novel.

        """

        self.host = host
        try:
            self.decoder.set_host(host)
            logger.info(f'Host updated to "{self.host}"')
        except DecodeGuideError as e:
            logger.debug("Traceback: ", exc_info=True)
            raise ScraperError(e) from e

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
        """

        self.toc_main_url = toc_main_url
        logger.info(
            f'Main URL updated to "{self.toc_main_url}", TOCs already requested will be deleted.'
        )
        self.delete_toc()

        if update_host:
            new_host = utils.obtain_host(self.toc_main_url)
            logger.debug(f'Update Host flag present, new host is "{new_host}".')
            self.set_host(new_host)

    def delete_toc(self):
        """
        Deletes all table of contents files and resets chapter data.

        Clears:
        - All TOC files from disk
        - Chapter list
        - Chapter URL list
        """

        try:
            self.novel_data_helper.delete_all_toc_fragments()
        except NovelDataError as e:
            logger.debug("Traceback", exc_info=True)
            raise ScraperError(e) from e
        self.chapters = []
        self.chapters_url_list = []
        logger.info("TOC files deleted from disk.")

    def sync_toc(self, reload_files: bool = True) -> None:
        """
        Synchronizes the table of contents with stored/remote content.

        Process:
        1. Checks if TOC content exists (stored or retrievable)
        2. Optionally reloads TOC files from remote if needed
        3. Extracts chapter URLs from TOC content
        4. Creates/updates chapters based on URLs

        Args:
            reload_files: Whether to avoid reload of TOC files from remote (default: True)

        Raises:
            ScraperError: If no TOC content is available
            DecodeError: If TOC parsing fails
            NetworkError: If remote content retrieval fails
            ValidationError: If chapter creation fails
        """

        all_tocs_content = self.novel_data_helper.get_all_toc_fragments()

        # Will reload files if:
        # reload_files is True
        # OR
        # No toc files are saved in the disk.
        reload_files = reload_files or all_tocs_content is None
        if reload_files:
            logger.debug("Reloading TOC files.")

            try:
                self._request_toc_files()
            except DecodeError as e:
                logger.error("Could not request TOC files. Decoder Error", exc_info=e)
                raise

        try:
            self._load_or_request_chapter_urls_from_toc()
        except DecodeError as e:
            logger.error(
                "Could not get chapter urls from TOC files. Decoder Error", exc_info=e
            )
            raise

        try:
            self._create_chapters_from_toc()
        except ValidationError as e:
            logger.error(
                "Could not create chapters from TOC files. Validation Error", exc_info=e
            )
            raise
        logger.info("TOC synced with files, Chapters created from Table of Contents.")

    def show_toc(self) -> Optional[str]:
        """
        Generates a human-readable representation of the Table Of Contents.

        Returns:
            Optional[str]: Formatted string showing chapter numbers and URLs, None if no chapters_urls found
        """

        if not self.chapters_url_list:
            logger.warning("No chapters in TOC")
            return None
        toc_str = "Table Of Contents:"
        for i, chapter_url in enumerate(self.chapters_url_list):
            toc_str += f"\nChapter {i + 1}: {chapter_url}"
        return toc_str

    # CHAPTERS MANAGEMENT

    def get_chapter(
        self, chapter_index: Optional[int] = None, chapter_url: Optional[str] = None
    ) -> Optional[Chapter]:
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
            raise ValidationError(
                "Exactly one of 'chapter_index' or 'chapter_url' must be provided"
            )

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
        """

        logger.debug("Scraping Chapter...")
        if chapter.chapter_url is None:
            logger.error("Chapter trying to be scrapped does not have a URL")
            raise ValidationError("Chapter trying to be scrapped does not have a URL")

        logger.debug(f"Using chapter url: {chapter.chapter_url}")

        if reload_file:
            logger.debug("Reload file Flag present, HTML will be requested...")

        try:
            with self._initialize_request_helper() as self.request_helper:
                chapter = self._load_or_request_chapter(
                    chapter, reload_file=reload_file
                )
        except ValidationError as e:
            logger.error(
                f'Could get chapter for URL "{chapter.chapter_url}" HTML content. Validation Error',
                exc_info=e,
            )
            raise
        except RequestError as e:
            logger.debug("Traceback: ", exc_info=True)
            raise ScraperError(e) from e

        # We get the chapter title and content
        # We pass an index so we can autogenerate a Title
        if self.scraper_behavior.title_in_content is not None:
            logger.debug(
                f"Custom scraper behavior configured, title in config option: {self.scraper_behavior.title_in_content}"
            )
            title_in_content = self.scraper_behavior.title_in_content
        else:
            title_in_content = self.decoder.title_in_content()

        try:
            chapter = self._decode_chapter(
                chapter=chapter, title_in_content=title_in_content
            )
        except DecodeError as e:
            logger.error(
                f'Could not decode HTML title and content for chapter with URL "{chapter.chapter_url}"',
                exc_info=e,
            )
            raise
        except ValidationError as e:
            logger.error(
                f'Could not decode HTML title and content for chapter with URL "{chapter.chapter_url}"',
                exc_info=e,
            )
            raise
        logger.info(f"Chapter scrapped from link: {chapter.chapter_url}")
        return chapter

    def request_all_chapters(
        self, reload_files: bool = False, clean_chapters: bool = False
    ) -> None:
        """
        Requests and processes all chapters of the novel.

        This method performs scraping of all available chapters in the novel,
        handling the loading and decoding of each one.

        Args:
            reload_files (bool, optional): If True, forces a new download of all
                chapters, even if they already exist locally. Defaults to False.
            clean_chapters (bool, optional): If True, cleans the HTML content of the files

        Raises:
            DecodeError: If there are issues during content decoding
            ValidationError: If there are issues during content decoding

        Note:
            - Process is performed sequentially for each chapter
            - Errors in individual chapters don't stop the complete process
            - Progress is logged through the logging system
        """

        logger.debug("Requesting all chapters...")
        if len(self.chapters_url_list) == 0:
            logger.warning("No chapters in TOC, returning without requesting any...")
            return None

        with self._initialize_request_helper() as self.request_helper:
            # We request the HTML files of all the chapters
            # The chapter will be requested again if:
            # 1. Reload files flag is True (Requested by user)
            # 2. Chapter doesn't have a chapter_html_filename, or the HTML file does not exist
            chapters_obtained = 0
            total_chapters = len(self.chapters)
            for i in range(len(self.chapters)):
                request_chapter = reload_files
                if self.chapters[i].chapter_html_filename is None:
                    logger.debug(
                        f"No HTML file name for chapter {i + 1} of {total_chapters}, requesting..."
                    )
                    request_chapter = True
                else:
                    chapter_file_exists = self.novel_data_helper.chapter_file_exists(
                        chapter_file=self.chapters[i].chapter_html_filename
                    )
                    if not chapter_file_exists:
                        logger.debug(
                            f"File for chapter {i + 1} of {total_chapters} does not exist, requesting..."
                        )
                        request_chapter = True

                if request_chapter:
                    logger.info(f"Requesting chapter {i + 1} of {total_chapters}")
                    try:
                        self.chapters[i] = self._load_or_request_chapter(
                            chapter=self.chapters[i], reload_file=reload_files
                        )
                    except ValidationError:
                        logger.warning(
                            f"Error validating chapter {i + 1} with url {self.chapters[i].chapter_url}, Skipping..."
                        )
                        continue
                    except RequestError:
                        logger.warning(
                            f"Error requesting chapter {i + 1} with url {self.chapters[i].chapter_url}, Skipping..."
                        )
                        continue

                    if clean_chapters:
                        self._clean_chapter(self.chapters[i].chapter_html_filename)
                    try:
                        self.save_novel()
                    except NovelDataError as e:
                        logger.warning(
                            f"Error when trying to Save Novel Data: {str(e)}. Requests will continue anyway."
                        )
                else:
                    logger.debug(
                        f"Chapter {i + 1} of {total_chapters} already requested, skipping..."
                    )
                chapters_obtained += 1
        logger.info(
            f"Successfully requested {chapters_obtained} of {total_chapters} chapters."
        )
        return None

    ## UTILS

    def clean_files(
        self,
        clean_chapters: bool = True,
        clean_toc: bool = True,
        hard_clean: bool = False,
    ) -> None:
        hard_clean = hard_clean or self.scraper_behavior.hard_clean
        if clean_chapters:
            for chapter in self.chapters:
                if chapter.chapter_html_filename:
                    self._clean_chapter(chapter.chapter_html_filename, hard_clean)
        if clean_toc:
            self._clean_toc(hard_clean)

    def show_novel_dir(self) -> str:
        return str(self.novel_data_helper.novel_base_dir)

    ## PRIVATE HELPERS

    def _initialize_request_helper(self) -> RequestHelper:
        scraper_config = get_active_scraper_config()
        request_config = scraper_config.config_options["request_config"]
        request_helper = RequestHelper(
            retries_number=request_config.get("request_retries"),
            request_timeout=request_config.get("request_timeout"),
            time_between_retries=request_config.get("request_time_between_retries"),
            cookies=request_config.get("request_cookies"),
            time_between_requests=request_config.get("request_time_between_requests"),
        )

        use_flaresolver = (
            request_config.get("force_flaresolver")
            or self.scraper_behavior.force_flaresolver
        )

        if use_flaresolver:
            request_helper.enable_flaresolverr(
                flaresolverr_url=request_config.get("flaresolver_url")
            )

        return request_helper

    def _clean_chapter(
        self, chapter_html_filename: str, hard_clean: bool = False
    ) -> None:
        hard_clean = hard_clean or self.scraper_behavior.hard_clean
        chapter_html = self.novel_data_helper.load_chapter_html(chapter_html_filename)
        if not chapter_html:
            logger.warning(f"No content found on file {chapter_html_filename}")
            return
        chapter_html = self.decoder.clean_html(chapter_html, hard_clean=hard_clean)
        self.novel_data_helper.save_chapter_html(chapter_html_filename, chapter_html)

    def _clean_toc(self, hard_clean: bool = False) -> None:
        hard_clean = hard_clean or self.scraper_behavior.hard_clean
        tocs_content = self.novel_data_helper.get_all_toc_fragments()
        for i, toc in enumerate(tocs_content):
            toc = self.decoder.clean_html(toc, hard_clean=hard_clean)
            self.novel_data_helper.update_toc(idx=i, html=toc)

    def _load_or_request_chapter(
        self, chapter: Chapter, reload_file: bool = False
    ) -> Chapter:
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
            ValidationError: If there's a validation error when requesting the chapter.
            NetworkError: If there's a network error when requesting the chapter.

        Note:
            - If the file doesn't exist locally, a web request will be made.
            - If the file exists but is empty, a web request will be made.
            - File saving errors are logged as warnings but don't stop execution.
        """

        # Generate a filename if needed
        if not chapter.chapter_html_filename:
            logger.debug("Generating a filename for the chapter")
            chapter.chapter_html_filename = utils.generate_file_name_from_url(
                chapter.chapter_url
            )

        # The HTML will be requested again if:
        # 1. "Reload file" flag is True (requested by user)
        # 2. Chapter file does not exist
        # 3. The Chapter file does exist, but there is no content
        reload_file = reload_file or not self.novel_data_helper.chapter_file_exists(
            chapter.chapter_html_filename
        )
        # Try loading from the disk first
        if not reload_file:
            try:
                logger.debug(
                    f'Loading chapter HTML from file: "{chapter.chapter_html_filename}"'
                )
                chapter.chapter_html = self.novel_data_helper.load_chapter_html(
                    chapter.chapter_html_filename
                )
            except ChapterFileNotFoundError or ChapterFileIsEmptyError:
                chapter.chapter_html = None
            except NovelDataError as e:
                logger.debug("Traceback:", exc_info=True)
                raise ScraperError(e) from e
            if chapter.chapter_html is not None:
                return chapter

        logger.debug(
            f'Chapter HTML not found locally, requesting from URL "{chapter.chapter_url}"'
        )
        # Fetch fresh content
        chapter.chapter_html = self.request_helper.get_url_content(chapter.chapter_url)

        # Save content
        try:
            logger.info(
                f'Saving chapter HTML to file: "{chapter.chapter_html_filename}"'
            )
            self.novel_data_helper.save_chapter_html(
                chapter.chapter_html_filename, chapter.chapter_html
            )
        except NovelDataError as e:
            logger.warning(f"Error when trying to save chapter HTML to file: {str(e)}.")
            # We can pass this error and try again later

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
                logger.debug(
                    f'Toc link is incomplete, trying with toc link: "{toc_url}"'
                )

            # Fetch fresh content
            logger.debug(f'Requesting TOC from link: "{toc_url}"')
            try:
                toc_content = self.request_helper.get_url_content(toc_url)
            except RequestError as e:
                logger.debug("Traceback: ", exc_info=True)
                raise ScraperError(e) from e

            logger.debug("Saving new TOC file to disk.")
            try:
                self.novel_data_helper.add_toc_fragment(toc_content)
            except NovelDataError as e:
                logger.debug("Traceback", exc_info=True)
                raise ScraperError(e) from e

            if get_next_page:
                try:
                    logger.debug(f"Parsing next page from link: {toc_url}")
                    next_page = self.decoder.get_toc_next_page_url(toc_content)
                except DecodeError:
                    raise
                return next_page
            return None

        self.novel_data_helper.delete_all_toc_fragments()
        has_pagination = self.decoder.has_pagination()
        try:
            toc_main_url = self.decoder.toc_main_url_process(self.toc_main_url)
        except DecodeError:
            logger.debug("Error when trying to preprocess toc main url")
            raise
        with self._initialize_request_helper() as self.request_helper:
            if not has_pagination:
                logger.debug("TOC does not have pagination, requesting only one file.")
                _get_toc(toc_main_url, get_next_page=False)
            else:
                logger.debug("TOC has pagination, requesting all files.")
                next_page_url = toc_main_url
                while next_page_url:
                    next_page_url = _get_toc(next_page_url, get_next_page=True)

    def _load_or_request_chapter_urls_from_toc(self) -> None:
        """
        Extracts and processes chapter URLs from the table of contents.

        Raises:
            DecodeError: If fails to decode chapter URLs from TOC content
        """

        # Get all TOC content at once
        try:
            all_tocs = self.novel_data_helper.get_all_toc_fragments()
        except NovelDataError as e:
            logger.debug("Traceback", exc_info=True)
            raise ScraperError(e) from e

        # Extract URLs from all TOC fragments
        self.chapters_url_list = []
        if self.decoder.pagination_in_descending_order():
            logger.debug(
                "TOC pagination is in descending order, reversing TOC Fragments list."
            )
            all_tocs.reverse()

        for toc_content in all_tocs:
            try:
                urls = self.decoder.get_chapter_urls(toc_content, self.toc_main_url)
                self.chapters_url_list.extend(urls)
            except DecodeError as e:
                logger.error(
                    "Failed to decode chapter URLs from TOC content", exc_info=e
                )
                raise

        # Remove duplicates while preserving order
        # self.chapters_url_list = utils.delete_duplicates(self.chapters_url_list)

        logger.info(
            f"Successfully extracted {len(self.chapters_url_list)} unique chapter URLs"
        )

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
            logger.info(f"Removing {len(urls_to_remove)} chapters not found in TOC")
            self.chapters = [
                ch for ch in self.chapters if ch.chapter_url not in urls_to_remove
            ]

        if urls_to_add:
            logger.info(f"Adding {len(urls_to_add)} new chapters from TOC")
            for url in self.chapters_url_list:
                if url in urls_to_add:
                    try:
                        new_chapter = Chapter(chapter_url=url)
                        self.chapters.append(new_chapter)
                    except ValidationError as e:
                        logger.error(f"Failed to create chapter for URL {url}: {e}")
                        raise

        # Reorder according to TOC
        logger.debug("Reordering chapters according to TOC")
        self.chapters.sort(key=lambda x: self.chapters_url_list.index(x.chapter_url))

        logger.info(
            f"Chapter synchronization complete. Total chapters: {len(self.chapters)}"
        )

    def _add_or_update_chapter_data(
        self, chapter: Chapter, save_in_file: bool = True
    ) -> None:

        # Check if the chapter exists
        chapter_idx = self._find_chapter_index_by_url(chapter.chapter_url)
        if chapter_idx is None:
            # If no existing chapter, we append it
            self.chapters.append(chapter)
        else:
            if chapter.chapter_title:
                self.chapters[chapter_idx].chapter_title = chapter.chapter_title
            if chapter.chapter_html_filename:
                self.chapters[
                    chapter_idx
                ].chapter_html_filename = chapter.chapter_html_filename

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
            return next(
                i for i, ch in enumerate(self.chapters) if ch.chapter_url == chapter_url
            )
        except StopIteration:
            return None

    def _decode_chapter(
        self,
        chapter: Chapter,
        title_in_content: TitleInContentOption = TitleInContentOption.SEARCH,
    ) -> Chapter:
        """
        Decodes a chapter's HTML content to extract title and content.

        This method processes the HTML content of a chapter to extract its title and content.
        If no title is found, it auto-generates one using the chapter's index in the URL list.

        Args:
            chapter (Chapter): Chapter object containing the HTML content to decode.
            title_in_content (TitleInContentOption, optional): Whether to include the title in the
                chapter content. Defaults to SEARCH.

        Returns:
            Chapter: The updated Chapter object with decoded title and content.

        Raises:
            ScraperError: If the chapter's HTML content is None.
            DecodeError: If there's an error decoding the chapter's title or content.

        Note:
            - If no title is found, it will be auto-generated as "{novel_title} Chapter {index}".
            - The chapter's HTML must be loaded before calling this method.
        """

        logger.debug(f"Decoding chapter with URL {chapter.chapter_url}...")
        if chapter.chapter_html is None:
            logger.error(
                f'Chapter HTML not found for chapter with URL "{chapter.chapter_url}"'
            )
            raise ScraperError(
                f'Chapter HTML not found for chapter with URL "{chapter.chapter_url}"'
            )

        logger.debug("Obtaining chapter title...")
        try:
            chapter_title = self.decoder.get_chapter_title(chapter.chapter_html)
        except DecodeError as e:
            logger.error(f"Failed to decode chapter title from HTML content: {e}")
            raise

        if chapter_title is None:
            logger.debug("No chapter title found, trying to autogenerate one...")
            try:
                chapter_idx = self.chapters_url_list.index(chapter.chapter_url)
            except ValueError:
                chapter_idx = ""

            chapter_title = f"{self.title} Chapter {chapter_idx}"

        chapter.chapter_title = chapter_title
        logger.info(f'Chapter title: "{chapter_title}"')

        logger.debug("Obtaining chapter content...")
        try:
            chapter.chapter_content = self.decoder.get_chapter_content(
                chapter.chapter_html, title_in_content, chapter.chapter_title
            )
        except DecodeError:
            logger.error(
                f'Failed to decode chapter content for chapter with URL "{chapter.chapter_url}"'
            )
            raise

        logger.debug("Chapter title and content successfully decoded from HTML")
        return chapter
