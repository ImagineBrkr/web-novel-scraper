import os
from pathlib import Path
from dataclasses import dataclass, field
import json

from dataclasses_json import dataclass_json
from ebooklib import epub
from typing import Optional

import custom_logger
from decode import Decoder
import custom_request
from output_file import OutputFiles
import utils

CURRENT_DIR = Path(__file__).resolve().parent
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
    cover_image_path: Optional[str] = None
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
    toc_main_link: str = None
    toc_links_list: list[str] = field(default_factory=list)
    # Some novels already have the title in the content.
    save_title_to_content: bool = True

    def __init__(self,
                 novel_title: str = None,
                 toc_main_link: str = None,
                 toc_links_list: list[str] = None,
                 metadata: Metadata = None,
                 chapters: list[Chapter] = None,
                 save_title_to_content: bool = False):

        if metadata is not None:
            self.metadata = metadata
        elif novel_title is not None:
            self.metadata = Metadata(novel_title)
        else:
            raise ValueError("You need to set 'novel_title' or 'metadata'.")

        self.chapters = chapters if chapters else []
        self.toc_main_link = toc_main_link
        self.toc_links_list = toc_links_list if toc_links_list else []

        self.toc = [{}]
        self.output_files = OutputFiles(self.metadata.novel_title)
        self.save_novel_to_json()
        self.decoder = Decoder(utils.obtain_host(self.toc_main_link))
        self.save_title_to_content = save_title_to_content

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
        new_cover_image_path = self.output_files.save_cover_img(
            cover_image_path)
        if new_cover_image_path:
            self.metadata.cover_image_path = new_cover_image_path
            self.save_novel_to_json()
            logger.info(f'New cover image on file {
                        self.metadata.cover_image_path}')

    def save_novel_to_json(self) -> None:
        self.output_files.save_novel_json(self.to_dict())

    def set_toc_main_link(self, toc_main_link: str) -> None:
        self.toc_main_link = toc_main_link
        self.output_files.clear_toc()
        self.decoder = Decoder(utils.obtain_host(self.toc_main_link))
        self.update_toc_links_list(update_toc=True)

    def get_links_from_toc(self) -> None:
        links = []
        tocs = self.output_files.get_all_toc()
        for toc_content in tocs:
            toc_links = self.decoder.decode_html(toc_content, 'index')
            toc_links = [link['href'] for link in toc_links]
            if toc_links:
                links = [*links, *toc_links]
        links = [f'https://www.{self.decoder.host}{link}' for link in links if self.decoder.host not in link]
        self.toc_links_list = links
        self.create_chapters_from_toc()
        self.save_novel_to_json()

    def update_toc_links_list(self, update_toc: bool = False) -> None:
        toc_content, _ = utils.get_url_or_temp_file(self.output_files,
                                                    self.toc_main_link,
                                                    reload=update_toc)

        if not toc_content:
            logger.warning(f'No content found on link {self.toc_main_link}')
            return
        self.output_files.add_toc(toc_content)

        if self.decoder.has_pagination():
            next_link_tag = self.decoder.decode_html(toc_content, 'next_page')
            aux = 1

            while next_link_tag:
                next_link = next_link_tag[0]['href']

                toc_new_content, _ = utils.get_url_or_temp_file(self.output_files,
                                                                next_link,
                                                                reload=update_toc)
                if toc_new_content:
                    next_link_tag = self.decoder.decode_html(
                        toc_new_content, 'next_page')
                    self.output_files.add_toc(toc_new_content)
                aux += 1
        self.get_links_from_toc()


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
            key=lambda x: self.toc_links_list.index(x.chapter_link))

    def scrap_chapter(self, chapter_link: str, file_path: str = None, update_html: bool = False) -> Chapter:
        chapter_html, chapter_html_filename = utils.get_url_or_temp_file(self.output_files,
                                                                         chapter_link,
                                                                         file_path,
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

    def set_custom_toc(self, html: str):
        self.clear_toc()
        self.output_files.add_toc(html)
        self.get_links_from_toc()

    def create_chapters_from_toc(self):
        for chapter_link in self.toc_links_list:
            chapter_idx = self.find_chapter_index_by_link(chapter_link)
            if not chapter_idx:
                chapter = Chapter(chapter_link=chapter_link)
                self.add_or_update_chapter(chapter=chapter)
        self.order_chapters_by_link_list()

    def scrap_all_chapters(self, update_chapters: bool = False, update_html: bool = False) -> None:
        if self.toc_links_list:
            for chapter_link in self.toc_links_list:
                # Search if the chapter exists
                chapter_idx = self.find_chapter_index_by_link(chapter_link)
                if not chapter_idx:
                    self.scrap_chapter(chapter_link,
                                       update_html=update_html)
                elif chapter_idx is not None and update_chapters:
                    self.scrap_chapter(chapter_link,
                                       update_html=update_html)
        else:
            logger.warning('No links found on toc_links_list')

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

        if self.metadata.cover_image_path:
            cover_image_content = self.output_files.load_cover_img(
                self.metadata.cover_image_path)
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
                chapter_html, _ = utils.get_url_or_temp_file(self.output_files,
                                                             chapter.chapter_link,
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
            logger.warning(f'start_chapter out of range')
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
                logger.warning(f'Error reading chapter')
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
        output_epub_filepath = f'{
            self.output_files.get_output_dir()}/{book_title}.epub'
        epub.write_epub(output_epub_filepath, book)
        logger.info(f'Saved epub to file {output_epub_filepath}')

    def save_novel_to_epub(self, chaps_by_vol: int = 100) -> None:
        start = 1
        idx = 1
        while start < len(self.chapters):
            self.save_chapters_to_epub(chapters_start=start,
                                       chapters_num=chaps_by_vol,
                                       collection_idx=idx)
            start = start + chaps_by_vol
            idx = idx + 1
            
    def clear_toc(self):
        self.output_files.clear_toc()

    def add_custom_toc(self, html: str):
        self.output_files.add_toc(html)
        self.get_links_from_toc()

    def clean_chapters_html_files(self):
        for chapter in self.chapters:
            if chapter.chapter_html_filename:
                chapter_html, _ = utils.get_url_or_temp_file(
                    self.output_files, chapter.chapter_link, chapter.chapter_html_filename)
                chapter_html = self.decoder.clean_html(chapter_html)
                self.output_files.save_to_temp_file(
                    chapter.chapter_html_filename, chapter_html)
