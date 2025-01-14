from dataclasses import dataclass, fields, field
import sys

from dataclasses_json import dataclass_json
from ebooklib import epub
from typing import Optional

import logger_manager
from decode import Decoder
from file_manager import FileManager
import utils

import request_manager

logger = logger_manager.create_logger('NOVEL SCRAPPING')


@dataclass_json
@dataclass
class Metadata:
    novel_title: str
    author: Optional[str] = None
    start_year: Optional[str] = None
    end_year: Optional[str] = None
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
        attributes = [f"{field.name}={
            getattr(self, field.name)}" for field in fields(self)]
        return f"Metadata: \n{'\n'.join(attributes)}"


@dataclass_json
@dataclass
class ScrapperBehavior:
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
        attributes = [f"{field.name}={
            getattr(self, field.name)}" for field in fields(self)]
        return f"Scrapper Behavior: \n{'\n'.join(attributes)}"


@dataclass_json
@dataclass
class Chapter:
    chapter_url: str
    chapter_html_filename: Optional[str] = None
    chapter_title: Optional[str] = None

    def __str__(self):
        return f'Title: "{self.chapter_title}"\nURL: "{self.chapter_url}"\nFilename: "{self.chapter_html_filename}"'

    def __lt__(self, another):
        return self.chapter_title < another.chapter_title


@dataclass_json
@dataclass
class Novel:
    metadata: Metadata
    scrapper_behavior: ScrapperBehavior = None
    chapters: list[Chapter] = field(default_factory=list)
    toc_main_url: Optional[str] = None
    chapters_url_list: list[str] = field(default_factory=list)
    host: str = None

    def __init__(self,
                 novel_title: str = None,
                 toc_main_url: str = None,
                 toc_html: str = None,
                 chapters_url_list: list[str] = None,
                 metadata: Metadata = None,
                 chapters: list[Chapter] = None,
                 novel_base_dir: str = None,
                 scrapper_behavior: ScrapperBehavior = None,
                 host: str = None):

        if toc_main_url and toc_html:
            logger.error('There can only be one or toc_main_url or toc_html')
            sys.exit(1)

        if metadata is not None:
            self.metadata = metadata
        elif novel_title is not None:
            self.metadata = Metadata(novel_title)
        else:
            logger.error('You need to set "novel_title" or "metadata".')
            sys.exit(1)

        self.file_manager = FileManager(novel_title=self.metadata.novel_title,
                                        novel_base_dir=novel_base_dir)

        if toc_html:
            self.file_manager.add_toc(toc_html)

        self.toc_main_url = toc_main_url
        self.chapters_url_list = chapters_url_list if chapters_url_list else []

        self.chapters = chapters if chapters else []

        self.scrapper_behavior = scrapper_behavior if scrapper_behavior else ScrapperBehavior()
        if not host and not toc_main_url:
            logger.error('You need to set "host" or "toc_main_url".')
            sys.exit(1)

        self.host = host if host else utils.obtain_host(self.toc_main_url)
        self.decoder = Decoder(self.host)

        self.save_novel()

    # NOVEL PARAMETERS MANAGEMENT

    def set_scrapper_behavior(self, **kwargs) -> None:
        self.scrapper_behavior.update_behavior(**kwargs)
        self.save_novel()

    def set_metadata(self, **kwargs) -> None:
        self.metadata.update_behavior(**kwargs)
        self.save_novel()

    def add_tag(self, tag: str) -> bool:
        if tag not in self.metadata.tags:
            self.metadata.tags.append(tag)
            self.save_novel()
            return True
        logger.warning(f'Tag "{tag}" already exists on novel {
                       self.metadata.novel_title}')
        return False

    def remove_tag(self, tag: str) -> bool:
        if tag in self.metadata.tags:
            self.metadata.tags.remove(tag)
            self.save_novel()
            return True
        logger.warning(f'Tag "{tag}" doesn\'t exist on novel {
                       self.metadata.novel_title}')
        return False

    def set_cover_image(self, cover_image_path: str) -> None:
        self.file_manager.save_novel_cover(cover_image_path)
        self.save_novel()
        logger.info('New cover image saved')

    def set_host(self, host: str) -> None:
        self.host = host
        self.decoder = Decoder(self.host)
        self.save_novel()

    def save_novel(self) -> None:
        self.file_manager.save_novel_json(self.to_dict())

    # TABLE OF CONTENTS MANAGEMENT

    def set_toc_main_url(self, toc_main_url: str, host: str = None, update_host: bool = False) -> None:
        self.toc_main_url = toc_main_url
        self.file_manager.clear_toc()
        if host:
            self.host = host
            self.decoder = Decoder(self.host)
        elif update_host:
            self.decoder = Decoder(utils.obtain_host(self.toc_main_url))

    def add_toc_html(self, html: str, host: str = None) -> None:
        if self.toc_main_url:
            self.clear_toc()
            self.toc_main_url = None

        if host:
            self.host = host
            self.decoder = Decoder(self.host)
        self.file_manager.add_toc(html)
        # Delete toc_main_url since they are exclusive
        self.save_novel()

    def clear_toc(self):
        self.file_manager.clear_toc()

    def sync_toc(self, reload_files: bool = False) -> None:
        # Hard reload will request again the toc files from the toc_main_url
        # Only works with toc_main_url
        all_tocs_content = self.file_manager.get_all_toc()
        if reload_files and self.toc_main_url or not all_tocs_content:
            self.chapters = []
            self.file_manager.clear_toc()
            all_tocs_content = []
            toc_content = self._add_toc(self.toc_main_url)
            all_tocs_content.append(toc_content)
            if self.decoder.has_pagination():
                next_page = self._get_next_page_from_toc_content(toc_content)
                while next_page:
                    toc_content = self._add_toc(next_page)
                    next_page = self._get_next_page_from_toc_content(
                        toc_content)
                    all_tocs_content.append(toc_content)

        # Now we get the links from the toc content
        self.chapters_url_list = []
        for toc_content in all_tocs_content:
            self.chapters_url_list = [*self.chapters_url_list,
                                      *self._get_chapter_urls_from_toc_content(toc_content)]
        if self.scrapper_behavior.auto_add_host:
            self.chapters_url_list = [
                f'https://{self.host}{chapter_url}' for chapter_url in self.chapters_url_list]
        self.chapters_url_list = utils.delete_duplicates(self.chapters_url_list)
        self.save_novel()
        self._create_chapters_from_toc()

    def show_toc(self):
        if not self.chapters_url_list:
            return 'No chapters in TOC, reload TOC and try again'
        toc_str = 'Table Of Contents:'
        for i, chapter_url in enumerate(self.chapters_url_list):
            toc_str += f'\nChapter {i+1}: {chapter_url}'
        return toc_str

    # CHAPTERS MANAGEMENT

    def scrap_chapter(self, chapter_url: str = None, chapter_idx: int = None, update_html: bool = False) -> tuple[Chapter, str]:
        if not chapter_idx and not chapter_url:
            logger.error('You need to set "chapter_url" or "chapter_idx"')
            sys.exit(1)

        if chapter_url and chapter_idx:
            logger.error('You can only set "chapter_url" or "chapter_idx"')
            sys.exit(1)
        chapter_html, chapter_html_filename = None, None
        if chapter_idx:
            chapter_html, chapter_html_filename = self._get_chapter(chapter_idx=chapter_idx,
                                                                    reload=update_html)
            chapter_url = self.chapters[chapter_idx].chapter_url

        if chapter_url:
            chapter_html, chapter_html_filename = self._get_chapter(chapter_url=chapter_url,
                                                                    reload=update_html)
            chapter_idx = self._get_chapter_url_idx(chapter_url)

        # We create a new chapter using the link and add it to the list of Chapters
        if not chapter_html or not chapter_html_filename:
            logger.warning(f'Failed to create chapter on link: "{
                           chapter_url}" on path "{chapter_html_filename}"')
            return

        # We get the title and content, if there's no title, we autogenerate one.
        chapter_title, chapter_content = self._decode_chapter(
            chapter_html=chapter_html, idx_for_chapter_name=chapter_idx)

        chapter = Chapter(chapter_title=chapter_title,
                          chapter_url=chapter_url,
                          chapter_html_filename=chapter_html_filename)
        logger.info(f'Chapter scrapped from link: {chapter_url}')
        return chapter, chapter_content

    def scrap_all_chapters(self, sync_toc: bool = False, update_chapters: bool = False, update_html: bool = False) -> None:
        if sync_toc:
            self.sync_toc()
        # We scrap all chapters from our chapter list
        if self.chapters_url_list:
            for i, chapter in enumerate(len(self.chapters)):

                # If update_chapters is true, we scrap again the chapter info
                if update_chapters:
                    chapter, _ = self.scrap_chapter(chapter_idx=i,
                                                    update_html=update_html)
                    self._add_or_update_chapter_data(
                        chapter=chapter, link_idx=i)
                    continue
                # If not, we only update if the chapter doesn't have a title or html
                if chapter.chapter_html_filename and chapter.chapter_title:
                    continue
                chapter, _ = self.scrap_chapter(chapter_idx=i,
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
                _, chapter_html_filename = self._get_chapter(
                    chapter_url=chapter.chapter_url, reload=update_html)
                chapter.chapter_html_filename = chapter_html_filename
                self._add_or_update_chapter_data(chapter=chapter, link_idx=i,
                                                 save_in_file=True)
                if clean_chapters:
                    self._clean_chapter(chapter_html_filename)
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
            logger.info(f'The start chapter is bigger than the number of chapters saved ({
                        len(self.chapters)})')
            return

        if not end_chapter:
            end_chapter = len(self.chapters)
        elif end_chapter > len(self.chapters):
            end_chapter = len(self.chapters)
            logger.info(f'The end chapter is bigger than the number of chapters, automatically setting it to {
                        end_chapter}.')

        idx = 1
        start = start_chapter
        while start <= end_chapter:
            end = min(start + chapters_by_book - 1, end_chapter)
            self._save_chapters_to_epub(start_chapter=start,
                                        end_chapter=end,
                                        collection_idx=idx)
            start = start + chapters_by_book
            idx = idx + 1


# UTILS


    def clean_files(self, clean_chapters: bool = True, clean_toc: bool = True, hard_clean: bool = False) -> None:
        hard_clean = hard_clean or self.scrapper_behavior.hard_clean
        if clean_chapters:
            for chapter in self.chapters:
                if chapter.chapter_html_filename:
                    self._clean_chapter(
                        chapter.chapter_html_filename, hard_clean)
        if clean_toc:
            self._clean_toc(hard_clean)

    def _clean_chapter(self, chapter_html_filename: str, hard_clean: bool = False) -> None:
        hard_clean = hard_clean or self.scrapper_behavior.hard_clean
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
        hard_clean = hard_clean or self.scrapper_behavior.hard_clean
        tocs_content = self.file_manager.get_all_toc()
        for i, toc in enumerate(tocs_content):
            toc = self.decoder.clean_html(toc, hard_clean=hard_clean)
            self.file_manager.update_toc(toc, i)

    def _get_chapter(self,
                     chapter_url: str = None,
                     chapter_idx: int = None,
                     chapter_filename: str = None,
                     reload: bool = False) -> tuple[str, str] | None:
        try:
            # Validate input parameters
            if not chapter_url and not chapter_idx:
                raise ValueError(
                    'You need to set either "url" or "chapter_idx"')
            if chapter_idx and chapter_url:
                raise ValueError(
                    'You can only set either "url" or "chapter_idx"')

            # Handle chapter index
            if chapter_idx is not None:
                if not 0 <= chapter_idx < len(self.chapters):
                    raise IndexError(f'Chapter index {
                                     chapter_idx} out of range')
                chapter_url = self.chapters[chapter_idx].chapter_url
                chapter_filename = self.chapters[chapter_idx].chapter_html_filename

            # Generate filename if needed
            if not chapter_filename:
                chapter_filename = utils.generate_file_name_from_url(
                    chapter_url)

            # Try loading from cache first
            if not reload:
                content = self.file_manager.load_chapter_html(chapter_filename)
                if content:
                    return content, chapter_filename

            # Fetch fresh content
            content = request_manager.get_html_content(chapter_url,
                                                       force_flaresolver=self.scrapper_behavior.force_flaresolver)
            if not content:
                logger.error(f'No content found on link {chapter_url}')
                sys.exit()

            # Save content
            self.file_manager.save_chapter_html(chapter_filename, content)
            return content, chapter_filename

        except ValueError as e:
            logger.error(str(e))
        except IndexError as e:
            logger.error(str(e))
        except Exception as e:
            logger.error(f'Unexpected error getting chapter: {
                         e}', exc_info=True)
            sys.exit()

    def _add_toc(self,
                 url: str,
                 toc_filename: str = None,
                 reload: bool = False):
        if not reload:
            content = self.file_manager.get_toc(toc_filename)
            if content:
                return content

        content = request_manager.get_html_content(url)
        if not content:
            logger.warning(f'No content found on link {url}')
            sys.exit(1)

        self.file_manager.add_toc(content)
        return content

    def _get_chapter_urls_from_toc_content(self, toc_content: str) -> list[str]:
        toc_elements = self.decoder.decode_html(toc_content, 'index')
        toc_urls = [toc_element['href'] for toc_element in toc_elements]
        if toc_urls:
            return toc_urls
        logger.warning('No chapter links found on toc content')
        sys.exit(1)

    def _get_next_page_from_toc_content(self, toc_content: str) -> str:
        next_page = self.decoder.decode_html(toc_content, 'next_page')
        if next_page:
            return next_page[0]['href']

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

    def _get_chapter_url_idx(self, chapter_url: str) -> int:
        if chapter_url in self.chapters_url_list:
            return self.chapters_url_list.index(chapter_url)

    def _find_chapter_index_by_link(self, chapter_url: str) -> str:
        for index, chapter in enumerate(self.chapters):
            if chapter.chapter_url == chapter_url:
                return index
        return None

    def _delete_chapters_not_in_toc(self) -> None:
        self.chapters = [chapter for chapter in self.chapters if chapter.chapter_url in self.chapters_url_list]

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

    def _decode_chapter(self, chapter_idx: int = None, chapter_html: str = None, idx_for_chapter_name: str = None) -> tuple[str, str]:
        if not chapter_html and not chapter_idx:
            logger.error('No argument was passed to decode_chapter')
            return
        chapter = None
        if chapter_idx and chapter_html:
            logger.error(
                'You can only set either "chapter_idx" or "chapter_html"')
            return

        if chapter_idx:
            try:
                chapter = self.chapters[chapter_idx]
            except IndexError:
                logger.error(f'Chapter index {chapter_idx} not found')
                return
        chapter_title = None

        if chapter:
            chapter_html, _ = self._get_chapter(chapter.chapter_url,
                                                chapter.chapter_html_filename)
            chapter_title = chapter.chapter_title
            if not chapter_html:
                logger.error(f'No chapter content found for chapter link {
                             chapter.chapter_url} on file {chapter.chapter_html_filename}')
                return

        if not chapter_html:
            logger.error('No argument was passed to decode_chapter')
            return

        paragraphs = self.decoder.decode_html(chapter_html, 'content')

        if not paragraphs:
            if chapter:
                logger.warning(f'No paragraphs found in chapter link {
                    chapter.chapter_url} on file {chapter.chapter_html_filename}')
            else:
                logger.warning('No paragraphs found in chapter')
            return

        if not chapter_title:
            chapter_title = self.decoder.decode_html(chapter_html, 'title')
        if not chapter_title:
            chapter_title = f'{self.metadata.novel_title} Chapter {
                idx_for_chapter_name}'
        chapter_title = str(chapter_title)

        chapter_content = ""
        if self.scrapper_behavior.save_title_to_content:
            chapter_content += f'<h4>{chapter_title}</h4>'
        logger.info(f'{len(paragraphs)} paragraphs found in chapter')
        for paragraph in paragraphs:
            chapter_content += str(paragraph)

        return chapter_title, chapter_content

    def _create_epub_book(self, book_title: str = None, calibre_collection: dict = None) -> epub.EpubBook:
        book = epub.EpubBook()
        if not book_title:
            book_title = self.metadata.novel_title
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
        if self.metadata.start_year:
            book.add_metadata('OPF', 'meta', self.metadata.start_year,
                              {'name': 'start-year', 'content': self.metadata.start_year})
        if self.metadata.end_year:
            book.add_metadata('OPF', 'meta', self.metadata.end_year,
                              {'name': 'start-year', 'content': self.metadata.end_year})

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
        chapter, chapter_content = self.scrap_chapter(
            chapter_url=chapter.chapter_url)
        if not chapter_content:
            logger.warning('Error reading chapter')
            return
        self._add_or_update_chapter_data(
            chapter=chapter, save_in_file=False)
        file_name = utils.generate_epub_file_name_from_title(
            chapter.chapter_title)

        chapter_epub = epub.EpubHtml(
            title=chapter.chapter_title, file_name=file_name)
        chapter_epub.set_content(chapter_content)
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
        book_title = f'{self.metadata.novel_title} Chapters {
            start_chapter} - {end_chapter}'
        calibre_collection = None
        # If collection_idx is set, we create a calibre collection
        if collection_idx:
            calibre_collection = {'title': self.metadata.novel_title,
                                  'idx': str(collection_idx)}
        book = self._create_epub_book(book_title, calibre_collection)

        for chapter in self.chapters[idx_start:idx_end]:
            book = self._add_chapter_to_epub_book(chapter=chapter,
                                                  book=book)

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        self.file_manager.save_book(book, f'{book_title}.epub')
        self.save_novel()
