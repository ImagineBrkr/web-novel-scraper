from dataclasses import dataclass, field
import sys

from dataclasses_json import dataclass_json
from ebooklib import epub
from typing import Optional

import custom_logger
from decode import Decoder
from file_manager import FileManager
import utils

import custom_request

logger = custom_logger.create_logger('NOVEL SCRAPPING')


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


@dataclass_json
@dataclass
class Chapter:
    chapter_link: str
    chapter_html_filename: str = None
    chapter_title: str = None

    def __str__(self):
        return f'Title: {self.chapter_title}, link: {self.chapter_link}'

    def __lt__(self, another):
        return self.chapter_title < another.chapter_title


@dataclass_json
@dataclass
class Novel:
    metadata: Metadata
    chapters: list[Chapter] = field(default_factory=list)
    toc_main_url: str = None
    chapters_url_list: list[str] = field(default_factory=list)
    host: str = None
    # Some novels already have the title in the content.
    save_title_to_content: bool = True

    def __init__(self,
                 novel_title: str = None,
                 toc_main_url: str = None,
                 toc_html: str = None,
                 chapters_url_list: list[str] = None,
                 metadata: Metadata = None,
                 chapters: list[Chapter] = None,
                 save_title_to_content: bool = False,
                 novel_base_dir: str = None,
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

        self.save_title_to_content = save_title_to_content
        if not host and not toc_main_url:
            logger.error('You need to set "host" or "toc_main_url".')
            sys.exit(1)

        self.host = host if host else utils.obtain_host(self.toc_main_url)
        self.decoder = Decoder(self.host)

        self.save_novel_to_json()

    ## NOVEL PARAMETERS MANAGEMENT


    def set_save_title_to_content(self, save_title_to_content: bool):
        self.save_title_to_content = save_title_to_content
        self.save_novel_to_json()

    def set_metadata(self, author: str = None,
                     start_year: str = None,
                     end_year: str = None,
                     language: str = "en",
                     description: str = None) -> None:
        self.metadata.author = author if author is not None else self.metadata.author
        self.metadata.start_year = start_year if start_year is not None else self.metadata.start_year
        self.metadata.end_year = end_year if end_year is not None else self.metadata.end_year
        self.metadata.language = language if language is not None else self.metadata.language
        self.metadata.description = description if description is not None else self.metadata.description
        self.save_novel_to_json()

    def add_tag(self, tag: str) -> None:
        if tag not in self.metadata.tags:
            self.metadata.tags.append(tag)
            self.save_novel_to_json()
            return
        logger.warning(f'Tag "{tag}" already exists on novel {
                       self.metadata.novel_title}')

    def remove_tag(self, tag: str) -> None:
        if tag in self.metadata.tags:
            self.metadata.tags.remove(tag)
            self.save_novel_to_json()
            return
        logger.warning(f'Tag "{tag}" doesn\'t exist on novel {
                       self.metadata.novel_title}')

    def set_cover_image(self, cover_image_path: str) -> None:
        self.file_manager.save_novel_cover(cover_image_path)
        self.save_novel_to_json()
        logger.info('New cover image saved')

    def set_host(self, host: str) -> None:
        self.host = host
        self.decoder = Decoder(self.host)
        self.save_novel_to_json()

    def save_novel_to_json(self) -> None:
        self.file_manager.save_novel_json(self.to_dict())


    ## TABLE OF CONTENTS MANAGEMENT


    def set_toc_main_url(self, toc_main_url: str, host: str = None, update_host: bool = False) -> None:
        self.toc_main_url = toc_main_url
        self.file_manager.clear_toc()
        if host:
            self.host = host
            self.decoder = Decoder(self.host)
        elif update_host:
            self.decoder = Decoder(utils.obtain_host(self.toc_main_url))

    def add_toc_html(self, html: str, host: str = None) -> None:
        self.clear_toc()
        if host:
            self.host = host
            self.decoder = Decoder(self.host)
        self.file_manager.add_toc(html)
        # Delete toc_main_url since they are exclusive
        self.toc_main_url = None
        self.save_novel_to_json()

    def clear_toc(self):
        self.file_manager.clear_toc()

    def reload_toc(self, hard_reload: bool = False) -> None:
        # Hard reload will request again the toc files from the toc_main_url
        # Only works with toc_main_url
        if hard_reload and self.toc_main_url:
            self.file_manager.clear_toc()
            all_tocs_content = []
            toc_content = self._add_toc(self.toc_main_url)
            all_tocs_content.append(toc_content)
            if self.decoder.has_pagination():
                next_page = self._get_next_page_from_toc_content(toc_content)
                while next_page:
                    toc_content = self._add_toc(next_page)
                    next_page = self._get_next_page_from_toc_content(toc_content)
                    all_tocs_content.append(toc_content)
        else:
            all_tocs_content = self.file_manager.get_all_toc()

        # Now we get the links from the toc content
        for toc_content in all_tocs_content:
            self.chapters_url_list = [*self.chapters_url_list,
                                      *self._get_chapter_urls_from_toc_content(toc_content)]

        self.save_novel_to_json()
        self.create_chapters_from_toc()


    ## CHAPTERS MANAGEMENT


    def add_or_update_chapter(self, chapter: Chapter, link_idx: int = None) -> None:
        if link_idx:
            chapter_idx = link_idx
        else:
            # Check if the chapter exists
            chapter_idx = self.find_chapter_index_by_link(chapter.chapter_link)
            if chapter_idx is None:
                # If no existing chapter we append it
                self.chapters.append(chapter)
                chapter_idx = len(self.chapters)
            else:
                self.chapters[chapter_idx] = chapter
        self.save_novel_to_json()
        return chapter_idx

    def order_chapters_by_link_list(self) -> None:
        self.chapters.sort(
            key=lambda x: self.chapters_url_list.index(x.chapter_link))

    def scrap_chapter(self, chapter_link: str, chapter_filename: str = None, update_html: bool = False) -> Chapter:
        chapter_html, chapter_html_filename = self._get_chapter(chapter_link,
                                                                chapter_filename,
                                                                update_html)
        # We create a new chapter using the link and add it to the list of Chapters
        if not chapter_html or not chapter_html_filename:
            logger.warning(f'Failed to create chapter on link: "{
                           chapter_link}" on path "{chapter_html_filename}"')
            return

        chapter = Chapter(chapter_link=chapter_link,
                          chapter_html_filename=chapter_html_filename)
        self.add_or_update_chapter(chapter=chapter)

        # We get the title and content, if there's no title, we autogenerate one.
        chapter_title, chapter_content = self.get_chapter_content(
            chapter=chapter, chapter_html=chapter_html)

        chapter = Chapter(chapter_title=chapter_title,
                          chapter_link=chapter_link,
                          chapter_html_filename=chapter_html_filename)
        self.add_or_update_chapter(chapter)
        logger.info(f'Chapter scrapped from link: {chapter_link}')
        return chapter, chapter_title, chapter_content

    def create_chapters_from_toc(self):
        for chapter_link in self.chapters_url_list:
            chapter_idx = self.find_chapter_index_by_link(chapter_link)
            if not chapter_idx:
                chapter = Chapter(chapter_link=chapter_link)
                self.add_or_update_chapter(chapter=chapter)
        self.order_chapters_by_link_list()

    def scrap_all_chapters(self, update_chapters: bool = False, update_html: bool = False) -> None:
        if self.chapters_url_list:
            for chapter_link in self.chapters_url_list:
                # Search if the chapter exists
                chapter_idx = self.find_chapter_index_by_link(chapter_link)
                if not chapter_idx:
                    self.scrap_chapter(chapter_link,
                                       update_html=update_html)
                elif chapter_idx is not None and update_chapters:
                    self.scrap_chapter(chapter_link,
                                       update_html=update_html)
        else:
            logger.warning('No links found on chapters_url_list')

    def find_chapter_index_by_link(self, chapter_link: str) -> str:
        for index, chapter in enumerate(self.chapters):
            if chapter.chapter_link == chapter_link:
                return index
        return None

    def create_epub_book(self, book_title: str = None, calibre_collection: dict = None) -> epub.EpubBook:
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

    def get_chapter_content(self, chapter: Chapter = None, idx: int = None, chapter_html: str = None) -> tuple[str, str]:
        if idx:
            try:
                chapter = self.chapters[idx]
            except IndexError:
                logger.error(f'Chapter index {idx} not found')
                return
        if chapter:
            if not chapter_html:
                chapter_html, _ = self._get_chapter(chapter.chapter_link,
                                                    chapter.chapter_html_filename)
            paragraphs = self.decoder.decode_html(chapter_html, 'content')
            title = chapter.chapter_title
            if title is None:
                title = self.decoder.decode_html(chapter_html, 'title')
            if title is None:
                title = f'{self.metadata.novel_title} Chapter {
                    self.find_chapter_index_by_link(chapter.chapter_link) + 1}'
            title = str(title)

            chapter_content = ""
            if self.save_title_to_content:
                chapter_content += f'<h4>{title}</h4>'
            if paragraphs:
                logger.info(f'{len(paragraphs)} paragraphs found in chapter link {
                            chapter.chapter_link}')
                for paragraph in paragraphs:
                    chapter_content += str(paragraph)
                return title, chapter_content
            logger.warning(f'No chapter content found for chapter link {
                           chapter.chapter_link} on file {chapter.chapter_html_filename}')

        logger.warning('No chapter given')

    def save_chapters_to_epub(self,
                              chapters_start: int,
                              chapters_num: int = 100,
                              chapters_end: int = None,
                              collection_idx: int = None):
        idx_start = chapters_start - 1
        if idx_start >= len(self.chapters):
            logger.warning('start_chapter out of range')
            return

        if not chapters_end:
            chapters_end = chapters_start + chapters_num - 1
            if chapters_end > len(self.chapters):
                chapters_end = len(self.chapters)
        idx_end = chapters_end + 1

        book_title = f'{self.metadata.novel_title} Chapters {
            chapters_start} - {chapters_end}'
        calibre_collection = None
        if collection_idx:
            calibre_collection = {'title': self.metadata.novel_title,
                                  'idx': str(collection_idx)}
        book = self.create_epub_book(book_title, calibre_collection)

        for chapter in self.chapters[idx_start:idx_end]:
            _, title, chapter_content = self.scrap_chapter(
                chapter_link=chapter.chapter_link)
            if not chapter_content:
                logger.warning('Error reading chapter')
                continue
            file_name = utils.generate_epub_file_name_from_title(title)

            chapter_epub = epub.EpubHtml(title=title, file_name=file_name)
            chapter_epub.set_content(chapter_content)
            book.add_item(chapter_epub)
            link = epub.Link(file_name, title, file_name.rstrip('.xhtml'))
            toc = book.toc
            toc.append(link)
            book.toc = toc
            book.spine.append(chapter_epub)

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        self.file_manager.save_book(book, f'{book_title}.epub')

    def save_novel_to_epub(self, chaps_by_vol: int = 100) -> None:
        start = 1
        idx = 1
        while start < len(self.chapters):
            self.save_chapters_to_epub(chapters_start=start,
                                       chapters_num=chaps_by_vol,
                                       collection_idx=idx)
            start = start + chaps_by_vol
            idx = idx + 1

    def clean_chapters_html_files(self):
        for chapter in self.chapters:
            if chapter.chapter_html_filename:
                chapter_html, _ = self._get_chapter(
                    self.file_manager, chapter.chapter_link, chapter.chapter_html_filename)
                chapter_html = self.decoder.clean_html(chapter_html)
                self.file_manager.save_chapter_html(
                    chapter.chapter_html_filename, chapter_html)

    def _get_chapter(self,
                     url: str,
                     chapter_filename: str = None,
                     reload: bool = False):
        if not chapter_filename:
            chapter_filename = utils.generate_file_name_from_url(url)

        if not reload:
            content = self.file_manager.load_chapter_html(chapter_filename)
            if content:
                return content, chapter_filename

        content = custom_request.get_html_content(url)
        if not content:
            return

        if chapter_filename:
            self.file_manager.save_chapter_html(chapter_filename, content)
        return content, chapter_filename

    def _add_toc(self,
                 url: str,
                 toc_filename: str = None,
                 reload: bool = False):
        if not reload:
            content = self.file_manager.get_toc(toc_filename)
            if content:
                return content

        content = custom_request.get_html_content(url)
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

    def _get_next_page_from_toc_content(self, toc_content:str) -> str:
        next_page = self.decoder.decode_html(toc_content, 'next_page')
        if next_page:
            return next_page[0]['href']