from web_novel_scraper.novel_scraper import Novel
from web_novel_scraper.models import Chapter
from web_novel_scraper.exporters.base_exporter import BaseExporter
from web_novel_scraper.exceptions import (
    ChapterContentNotFoundError,
    ChapterTitleNotFoundError,
    InvalidOutputDirectoryError,
    InvalidPathError,
    IOUtilsError,
    SaveBookError,
)
from web_novel_scraper.logger_manager import create_logger
from web_novel_scraper.io_helpers.utils import IOUtils
from pathlib import Path

logger = create_logger(__name__)


class TXTExporter(BaseExporter):
    _file_extension: str = ".txt"

    def __init__(self):
        self.novel = None
        self.book_title = None

        self.txt_book = ""

    def export_novel_to_book(
        self,
        novel: Novel,
        chapters: list[Chapter],
        book_title: str,
        output_directory: str | Path,
    ) -> None:
        try:
            IOUtils.ensure_dir(output_directory)
            output_path = IOUtils.get_path_in_dir(
                output_directory, book_title + TXTExporter._file_extension
            )
        except InvalidPathError as e:
            raise InvalidOutputDirectoryError(
                f'The Output Directory "{output_directory}" is invalid: {str(e)}'
            )
        logger.debug(f"Output path for the book: '{output_path}'")
        self.book_title = book_title
        self.novel = novel

        self._create_txt_book()
        for chapter in chapters:
            self._add_chapter_to_txt_book(chapter)

        self._save_txt_book(output_path)

    def _create_txt_book(self) -> None:
        self.txt_book += f"Title: {self.novel.title}\n\n"

        if self.novel.metadata.description:
            self.txt_book += f"Description: {self.novel.metadata.description}\n\n"

        if self.novel.metadata.author:
            self.txt_book += f"Author: {self.novel.metadata.author}\n"

    def _add_chapter_to_txt_book(self, chapter: Chapter) -> None:
        if chapter.chapter_content is None:
            raise ChapterContentNotFoundError(
                f'Chapter with url "{chapter.chapter_url}" has no content or has not been scrapped yet.'
            )
        if chapter.chapter_title is None:
            raise ChapterTitleNotFoundError(
                f'Chapter with url "{chapter.chapter_url} has no title or has not been scrapped yet.'
            )

        self.txt_book += "\n---\n\n"
        self.txt_book += f"{chapter.chapter_title}\n\n{chapter.chapter_content}\n"
        logger.debug(f"Chapter with URL '{chapter.chapter_url}' added to the book.")

    def _save_txt_book(self, output_path: Path):
        logger.debug(f"Trying to save book to {output_path}...")
        if output_path.exists():
            logger.warning(
                f"The file '{output_path}' already exists and will be overwritten."
            )
        try:
            IOUtils.save_text_file(output_path, self.txt_book)
            logger.info(f"Book '{self.book_title}' saved to file '{output_path}'.")
        except IOUtilsError as e:
            raise SaveBookError(f"Could not Save Book to {output_path}: {e}") from e
