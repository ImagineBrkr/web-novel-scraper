from dataclasses import dataclass, fields, field
import sys

from dataclasses_json import dataclass_json, config, Undefined
from ebooklib import epub
from typing import Optional

from . import logger_manager
from .decode import Decoder
from .file_manager import FileManager
from . import utils

from .request_manager import get_html_content
from .config_manager import ScraperConfig

logger = logger_manager.create_logger('NOVEL SCRAPPING')


@dataclass_json
@dataclass
class Metadata:
    author: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    language: Optional[str] = "en"
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    def update_behavior(self, **kwargs):
        """
        Updates the behavior configuration dynamically.
        Only updates the attributes provided in kwargs.
        """
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)

    def __str__(self):
        """
        Dynamic string representation of the configuration.
        """
        attributes = [(f"{field.name}="
                       f"{getattr(self, field.name)}") for field in fields(self)]
        attributes_str = '\n'.join(attributes)
        return (f"Metadata: \n"
                f"{attributes_str}")


@dataclass_json
@dataclass
class ScraperBehavior:
    # Some novels already have the title in the content.
    save_title_to_content: bool = False
    # Some novels have the toc link without the host
    auto_add_host: bool = False
    # Some hosts return 403 when scrapping, this will force the use of FlareSolver
    # to save time
    force_flaresolver: bool = False
    # When you clean the html files, you can use hard clean by default
    hard_clean: bool = False

    def update_behavior(self, **kwargs):
        """
        Updates the behavior configuration dynamically.
        Only updates the attributes provided in kwargs.
        """
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)

    def __str__(self):
        """
        Dynamic string representation of the configuration.
        """
        attributes = [(f"{field.name}="
                       f"{getattr(self, field.name)}") for field in fields(self)]
        attributes_str = '\n'.join(attributes)
        return (f"Scraper Behavior: \n"
                f"{attributes_str}")


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Chapter:
    chapter_url: str
    chapter_html_filename: Optional[str] = None
    chapter_title: Optional[str] = None

    def __init__(self, 
                 chapter_url: str,
                 chapter_html: str = None,
                 chapter_content: str = None, 
                 chapter_html_filename: str = None,
                 chapter_title: str = None):
        self.chapter_url = chapter_url
        self.chapter_html = chapter_html
        self.chapter_content = chapter_content
        self.chapter_html_filename = chapter_html_filename
        self.chapter_title = chapter_title

    def __str__(self):
        return f'Title: "{self.chapter_title}"\nURL: "{self.chapter_url}"\nFilename: "{self.chapter_html_filename}"'

    def __lt__(self, another):
        return self.chapter_title < another.chapter_title


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Novel:
    metadata: Metadata = None
    title: str = None
    scraper_behavior: ScraperBehavior = None
    chapters: list[Chapter] = field(default_factory=list)
    toc_main_url: Optional[str] = None
    chapters_url_list: list[str] = field(default_factory=list)
    host: str = None

    def __init__(self,
                 title: str,
                 toc_main_url: str = None,
                 toc_html: str = None,
                 chapters_url_list: list[str] = None,
                 metadata: Metadata = None,
                 chapters: list[Chapter] = None,
                 scraper_behavior: ScraperBehavior = None,
                 host: str = None
                 ):
        if toc_main_url and toc_html:
            logger.critical('There can only be one or toc_main_url or toc_html')
            raise ValueError('There can only be one or toc_main_url or toc_html')

        self.title = title
        self.metadata = Metadata()
        if metadata is not None:
            self.metadata = metadata

        if toc_html:
            self.file_manager.add_toc(toc_html)

        self.toc_main_url = toc_main_url
        self.chapters_url_list = chapters_url_list if chapters_url_list else []

        self.chapters = chapters if chapters else []

        self.scraper_behavior = scraper_behavior if scraper_behavior else ScraperBehavior()
        if not host and not toc_main_url:
            logger.error('You need to set "host" or "toc_main_url".')
            sys.exit(1)

        self.host = host if host else utils.obtain_host(self.toc_main_url)

        self.config = None
        self.file_manager = None
        self.decoder = None

    def __str__(self):
        """
        Dynamic string representation of the novel.
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

    @staticmethod
    def load(title: str, cfg: ScraperConfig, novel_base_dir: str | None = None):
        fm = FileManager(title, cfg.base_novels_dir, novel_base_dir, read_only=True)
        raw = fm.load_novel_json()
        if raw is None:
            logger.debug(f'Novel "{title}" was not found.')
            raise ValueError(f'Novel "{title}" was not found.')
        novel = Novel.from_json(raw)
        novel.config = cfg
        novel.set_config(cfg=cfg, novel_base_dir=novel_base_dir)
        return novel

    # NOVEL PARAMETERS MANAGEMENT

    def set_config(self,
                   cfg: ScraperConfig = None,
                   config_file: str = None,
                   base_novels_dir: str = None,
                   novel_base_dir: str = None,
                   decode_guide_file: str = None):
        if cfg is not None:
            self.config = cfg
        else:
            self.config = ScraperConfig(config_file=config_file,
                                        base_novels_dir=base_novels_dir,
                                        decode_guide_file=decode_guide_file)

        self.file_manager = FileManager(title=self.title,
                                        base_novels_dir=self.config.base_novels_dir,
                                        novel_base_dir=novel_base_dir)

        self.decoder = Decoder(self.host, self.config.decode_guide_file)

    def set_scraper_behavior(self, save: bool = False, **kwargs) -> None:
        self.scraper_behavior.update_behavior(**kwargs)

    def set_metadata(self, **kwargs) -> None:
        self.metadata.update_behavior(**kwargs)

    def add_tag(self, tag: str) -> bool:
        if tag not in self.metadata.tags:
            self.metadata.tags.append(tag)
            return True
        logger.warning(f'Tag "{tag}" already exists on novel {self.title}')
        return False

    def remove_tag(self, tag: str) -> bool:
        if tag in self.metadata.tags:
            self.metadata.tags.remove(tag)
            return True
        logger.warning(f'Tag "{tag}" doesn\'t exist on novel {self.title}')
        return False

    def set_cover_image(self, cover_image_path: str) -> bool:
        return self.file_manager.save_novel_cover(cover_image_path)

    def set_host(self, host: str) -> None:
        self.host = host
        self.decoder.set_host(host)

    def save_novel(self, save: bool = True) -> None:
        self.file_manager.save_novel_json(self.to_dict())

    # TABLE OF CONTENTS MANAGEMENT

    def set_toc_main_url(self, toc_main_url: str, host: str = None, update_host: bool = False) -> None:
        self.toc_main_url = toc_main_url
        self.file_manager.delete_toc()
        if host:
            self.host = host
            self.decoder = Decoder(self.host)
        elif update_host:
            self.decoder = Decoder(utils.obtain_host(self.toc_main_url))

    def add_toc_html(self, html: str, host: str = None) -> None:
        if self.toc_main_url:
            self.delete_toc()
            self.toc_main_url = None

        if host:
            self.host = host
            self.decoder = Decoder(self.host)
        self.file_manager.add_toc(html)
        # Delete toc_main_url since they are exclusive

    def delete_toc(self):
        self.file_manager.delete_toc()
        self.chapters = []
        self.chapters_url_list = []

    def sync_toc(self, reload_files: bool = False) -> bool:
        # Hard reload will request again the toc files from the toc_main_url
        # Only works with toc_main_url
        all_tocs_content = self.file_manager.get_all_toc()

        # If there is no toc_main_url and no manually added toc, there is no way to sync toc
        toc_not_exists = not all_tocs_content and self.toc_main_url is None
        if toc_not_exists:
            logger.critical(
                'There is no toc html and no toc url set, unable to get toc.')
            return False

        reload_files = reload_files and self.toc_main_url is not None
        if reload_files or not all_tocs_content:
            self.chapters = []
            self.file_manager.delete_toc()
            all_tocs_content = []
            toc_content = self._add_toc(self.toc_main_url)
            all_tocs_content.append(toc_content)
            if self.decoder.has_pagination():
                next_page = self.decoder.get_toc_next_page_url(toc_content)
                while next_page:
                    toc_content = self._add_toc(next_page)
                    next_page = self.decoder.get_toc_next_page_url(toc_content)
                    all_tocs_content.append(toc_content)

        # Now we get the links from the toc content
        self.chapters_url_list = []
        for toc_content in all_tocs_content:
            chapters_url_from_toc_content = self.decoder.get_chapter_urls(toc_content)
            if chapters_url_from_toc_content is None:
                logger.error('Chapters url not found on toc_content')
                return False
                # First we save a list of lists in case we need to invert the orderAdd commentMore actions
            self.chapters_url_list.append(chapters_url_from_toc_content)

        invert = self.decoder.is_index_inverted()
        self.chapters_url_list = [
            chapter
            for chapters_url in (self.chapters_url_list[::-1] if invert else self.chapters_url_list)
            for chapter in chapters_url
        ]
        add_host_to_chapter = self.scraper_behavior.auto_add_host or self.decoder.add_host_to_chapter()
        if add_host_to_chapter:
            self.chapters_url_list = [
                f'https://{self.host}{chapter_url}' for chapter_url in self.chapters_url_list]
        self.chapters_url_list = utils.delete_duplicates(
            self.chapters_url_list)
        self.save_novel()
        self._create_chapters_from_toc()
        return True

    def show_toc(self):
        if not self.chapters_url_list:
            return 'No chapters in TOC, reload TOC and try again'
        toc_str = 'Table Of Contents:'
        for i, chapter_url in enumerate(self.chapters_url_list):
            toc_str += f'\nChapter {i+1}: {chapter_url}'
        return toc_str

    # CHAPTERS MANAGEMENT

    def show_chapters(self) -> str:
        chapter_list = "Chapters List:\n"
        for i, chapter in enumerate(self.chapters):
            chapter_list += f"Chapter {i + 1}:\n"
            chapter_list += f"  Title: {chapter.chapter_title if chapter.chapter_title else 'Title not yet scrapped'}\n"
            chapter_list += f"  URL: {chapter.chapter_url}\n"
            chapter_list += f"  Filename: {chapter.chapter_html_filename if chapter.chapter_html_filename else 'File not yet requested'}\n"
        return chapter_list

    def scrap_chapter(self, chapter_url: str = None, chapter_idx: int = None, update_html: bool = False) -> Chapter:
        logger.info('Scraping Chapter...')
        chapter = None
        if not utils.check_exclusive_params(chapter_url, chapter_idx):
            raise ValueError("chapter_url and chapter_id, only one needs to be set")

        if chapter_url is not None:
            logger.debug(f'Using chapter url: {chapter_url}')
            chapter = self._get_chapter_by_url(chapter_url=chapter_url)
            if chapter is None:
                logger.warning(f'Chapter with url "{chapter_url}" does not exist, generating one...')
                chapter = Chapter(chapter_url=chapter_url)

        if chapter_idx is not None:
            logger.debug(f'Using chapter index: {chapter_idx}')
            if chapter_idx < 0 or chapter_idx >= len(self.chapters):
                logger.critical(f'Could not find chapter with idx {chapter_idx}')
                raise ValueError(f'Could not find chapter with idx {chapter_idx}')

            chapter = self.chapters[chapter_idx]
        if update_html:
            logger.debug('HTML will be updated...')

        chapter = self._get_chapter(chapter,
                                    reload=update_html)

        if not chapter.chapter_html or not chapter.chapter_html_filename:
            logger.critical(f'Failed to create chapter on link: "{chapter_url}" '
                           f'on path "{chapter.chapter_html_filename}"')
            raise ValueError(f'Failed to create chapter on link: "{chapter_url}" '
                           f'on path "{chapter.chapter_html_filename}"')

        # We get the chapter title and content
        # We pass an index so we can autogenerate a Title
        chapter = self._decode_chapter(chapter=chapter, idx_for_chapter_name=chapter_idx)

        logger.info(f'Chapter scrapped from link: {chapter_url}')
        return chapter

    def scrap_all_chapters(self, sync_toc: bool = False, update_chapters: bool = False, update_html: bool = False) -> None:
        if sync_toc:
            self.sync_toc()
        # We scrap all chapters from our chapter list
        if self.chapters_url_list:
            for i, chapter in enumerate(len(self.chapters)):

                # If update_chapters is true, we scrap again the chapter info
                if update_chapters:
                    chapter = self.scrap_chapter(chapter_idx=i,
                                                    update_html=update_html)
                    self._add_or_update_chapter_data(
                        chapter=chapter, link_idx=i)
                    continue
                # If not, we only update if the chapter doesn't have a title or html
                if chapter.chapter_html_filename and chapter.chapter_title:
                    continue
                chapter = self.scrap_chapter(chapter_idx=i,
                                                update_html=update_html)
                self._add_or_update_chapter_data(chapter=chapter,
                                                 save_in_file=True)
        else:
            logger.warning('No chapters found')

    def request_all_chapters(self, sync_toc: bool = False, update_html: bool = False, clean_chapters: bool = False) -> None:
        if sync_toc:
            self.sync_toc()
        if self.chapters_url_list:
            # We request the HTML files of all the chapters
            for i, chapter in enumerate(self.chapters):
                # If the chapter exists and update_html is false, we can skip
                if chapter.chapter_html_filename and not update_html:
                    continue
                chapter = self._get_chapter(
                    chapter=chapter, reload=update_html)
                if not chapter.chapter_html_filename:
                    logger.critical(f'Error requesting chapter {i} with url {chapter.chapter_url}')
                    return False

                self._add_or_update_chapter_data(chapter=chapter, link_idx=i,
                                                 save_in_file=True)
                if clean_chapters:
                    self._clean_chapter(chapter.chapter_html_filename)
            return True
        else:
            logger.warning('No chapters found')

# EPUB CREATION

    def save_novel_to_epub(self,
                           sync_toc: bool = False,
                           start_chapter: int = 1,
                           end_chapter: int = None,
                           chapters_by_book: int = 100) -> None:
        if sync_toc:
            self.sync_toc()

        if start_chapter > len(self.chapters):
            logger.info(f'The start chapter is bigger than the number of chapters saved ({len(self.chapters)})')
            return

        if not end_chapter:
            end_chapter = len(self.chapters)
        elif end_chapter > len(self.chapters):
            end_chapter = len(self.chapters)
            logger.info(f'The end chapter is bigger than the number of chapters, '
                        f'automatically setting it to {end_chapter}.')

        idx = 1
        start = start_chapter
        while start <= end_chapter:
            end = min(start + chapters_by_book - 1, end_chapter)
            result = self._save_chapters_to_epub(start_chapter=start,
                                                 end_chapter=end,
                                                 collection_idx=idx)
            if not result:
                logger.critical(f'Error with saving novel to epub, with start chapter: '
                                f'{start_chapter} and end chapter: {end_chapter}')
                return False
            start = start + chapters_by_book
            idx = idx + 1
        return True


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
        return self.file_manager.novel_base_dir


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
            self.file_manager.update_toc(toc, i)

    def _request_html_content(self, url: str) -> Optional[str]:
        request_config = self.decoder.request_config
        force_flaresolver = request_config.get('force_flaresolver') or self.scraper_behavior.force_flaresolver
        html_content = get_html_content(url,
                                        retries=request_config.get('request_retries'),
                                        timeout=request_config.get('request_timeout'),
                                        time_between_retries=request_config.get('request_time_between_retries'),
                                        force_flaresolver=force_flaresolver)
        return html_content

    def _get_chapter(self,
                     chapter: Chapter,
                     reload: bool = False) -> Chapter | None:

        # Generate filename if needed
        if not chapter.chapter_html_filename:
            chapter.chapter_html_filename = utils.generate_file_name_from_url(
                chapter.chapter_url)

        # Try loading from cache first
        if not reload:
            chapter.chapter_html = self.file_manager.load_chapter_html(
                chapter.chapter_html_filename)
            if chapter.chapter_html:
                return chapter

        # Fetch fresh content
        chapter.chapter_html = self._request_html_content(chapter.chapter_url)
        if not chapter.chapter_html:
            logger.error(f'No content found on link {chapter.chapter_url}')
            return chapter

        # Save content
        self.file_manager.save_chapter_html(
            chapter.chapter_html_filename, chapter.chapter_html)
        return chapter

    def _add_toc(self,
                 url: str,
                 toc_filename: str = None,
                 reload: bool = False):
        if not reload:
            content = self.file_manager.get_toc(toc_filename)
            if content:
                return content

        if utils.check_incomplete_url(url):
            url = self.toc_main_url + url

        # Fetch fresh content
        content = self._request_html_content(url)
        if not content:
            logger.warning(f'No content found on link {url}')
            sys.exit(1)

        self.file_manager.add_toc(content)
        return content

    def _add_or_update_chapter_data(self, chapter: Chapter, link_idx: int = None, save_in_file: bool = True) -> None:
        if link_idx:
            chapter_idx = link_idx
        else:
            # Check if the chapter exists
            chapter_idx = self._find_chapter_index_by_link(chapter.chapter_url)
            if chapter_idx is None:
                # If no existing chapter we append it
                self.chapters.append(chapter)
                chapter_idx = len(self.chapters)
            else:
                if chapter.chapter_title:
                    self.chapters[chapter_idx].chapter_title = chapter.chapter_title
                if chapter.chapter_html_filename:
                    self.chapters[chapter_idx].chapter_html_filename = chapter.chapter_html_filename
        if save_in_file:
            self.save_novel()
        return chapter_idx

    def _order_chapters_by_link_list(self) -> None:
        self.chapters.sort(
            key=lambda x: self.chapters_url_list.index(x.chapter_url))

    def _get_chapter_by_url(self, chapter_url: str) -> Chapter:
        for chapter in self.chapters:
            if chapter_url == chapter.chapter_url:
                return chapter
        return None

    def _find_chapter_index_by_link(self, chapter_url: str) -> str:
        for index, chapter in enumerate(self.chapters):
            if chapter.chapter_url == chapter_url:
                return index
        return None

    def _delete_chapters_not_in_toc(self) -> None:
        self.chapters = [
            chapter for chapter in self.chapters if chapter.chapter_url in self.chapters_url_list]

    def _create_chapters_from_toc(self):
        self._delete_chapters_not_in_toc()
        increment = 100
        aux = 1
        for chapter_url in self.chapters_url_list:
            aux += 1
            chapter_idx = self._find_chapter_index_by_link(chapter_url)
            if not chapter_idx:
                chapter = Chapter(chapter_url=chapter_url)
                self._add_or_update_chapter_data(
                    chapter=chapter, save_in_file=False)
            if aux == increment:
                self.save_novel()
                aux = 1
        self._order_chapters_by_link_list()
        self.save_novel()

    def _decode_chapter(self, chapter: Chapter, idx_for_chapter_name: str = None) -> Chapter:
        logger.debug('Decoding chapter...')
        if chapter.chapter_html is None:
            logger.debug(f'No HTML content found, requesting HTML content...')
            chapter = self._get_chapter(chapter)

            if not chapter.chapter_html:
                raise ValueError(f'Chapter HTML could not be obtained for chapter link "{chapter.chapter_url}" '
                                 f'on file "{chapter.chapter_html_filename}"')

        logger.debug('Obtaining chapter title...')
        chapter_title = self.decoder.get_chapter_title(chapter.chapter_html)
        if not chapter_title:
            logger.debug('No chapter title found, generating one...')
            chapter_title = f'{self.title} Chapter {idx_for_chapter_name}'
        chapter.chapter_title = str(chapter_title)
        logger.debug(f'Chapter title: "{chapter_title}"')

        logger.debug('Obtaining chapter content...')
        save_title_to_content = self.scraper_behavior.save_title_to_content or self.decoder.save_title_to_content()
        chapter.chapter_content = self.decoder.get_chapter_content(chapter.chapter_html,
                                                           save_title_to_content,
                                                           chapter.chapter_title)
        logger.debug('Chapter successfully decoded')

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
        chapter = self.scrap_chapter(
            chapter_url=chapter.chapter_url)
        if chapter is None:
            logger.warning('Error reading chapter')
            return
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
            return
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
        # If collection_idx is set, we create a calibre collection
        if collection_idx:
            calibre_collection = {'title': self.title,
                                  'idx': str(collection_idx)}
        book = self._create_epub_book(book_title, calibre_collection)

        for chapter in self.chapters[idx_start:idx_end]:
            book = self._add_chapter_to_epub_book(chapter=chapter,
                                                  book=book)
            if book is None:
                logger.critical(f'Error saving epub {book_title}, could not decode chapter {chapter} using host {self.host}')
                return False

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        self.file_manager.save_book(book, f'{book_title}.epub')
        self.save_novel()
        return True
