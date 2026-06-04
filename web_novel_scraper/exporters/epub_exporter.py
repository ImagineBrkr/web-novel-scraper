from web_novel_scraper.novel_scraper import Novel
from web_novel_scraper.models import Chapter
from web_novel_scraper.exporters.base_exporter import BaseExporter
from web_novel_scraper.exceptions import (
    ChapterContentNotFoundError,
    ChapterTitleNotFoundError,
    CoverImageNotFoundError,
    InvalidOutputDirectoryError,
    InvalidPathError,
    NovelDataError,
    SaveBookError,
)
from web_novel_scraper.logger_manager import create_logger
from web_novel_scraper.utils import generate_file_name_from_url
from web_novel_scraper.io_helpers.utils import IOUtils
from pathlib import Path
from ebooklib import epub

logger = create_logger(__name__)


class EPUBExporter(BaseExporter):
    _file_extension: str = ".epub"

    def __init__(self):
        self.novel = None
        self.book_title = None

        # This will be the EPUB Book Object
        self.epub_book = None

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
                output_directory, book_title + EPUBExporter._file_extension
            )
        except InvalidPathError as e:
            raise InvalidOutputDirectoryError(
                f'The Output Directory "{output_directory}" is invalid: {str(e)}'
            )
        logger.debug(f"Output path for the book: '{output_path}'")
        self.book_title = book_title
        self.novel = novel

        self._create_epub_book()
        self._add_metadata()
        self._add_cover_image()
        for chapter in chapters:
            self._add_chapter_to_epub_book(chapter)

        self.epub_book.add_item(epub.EpubNcx())
        self.epub_book.add_item(epub.EpubNav())
        self.epub_book.spine.append("nav")

        self._save_epub_book(output_path)

    def _create_epub_book(self) -> None:
        self.epub_book = epub.EpubBook()
        self.epub_book.set_title(self.book_title)

    def _add_metadata(self) -> None:
        self.epub_book.set_language(self.novel.metadata.language)
        self.epub_book.add_metadata(
            "DC", "description", self.novel.metadata.description
        )
        self.epub_book.add_metadata("DC", "subject", "Web Novel")
        self.epub_book.add_metadata("DC", "subject", "Scrapped")

        if self.novel.metadata.tags:
            for tag in self.novel.metadata.tags:
                self.epub_book.add_metadata("DC", "subject", tag)

        if self.novel.metadata.author:
            self.epub_book.add_author(self.novel.metadata.author)

        date_metadata = self.novel.metadata.start_date or ""
        if date_metadata:
            self.epub_book.add_metadata("DC", "date", date_metadata)

        # Calibre specification doesn't use end_date.
        # For now, we use a custom metadata
        # https://idpf.org/epub/31/spec/epub-packages.html#sec-opf-dcdate
        # if self.metadata.end_date:
        #     date_metadata += f'/{self.metadata.end_date}'
        if self.novel.metadata.end_date:
            self.epub_book.add_metadata(
                "OPF",
                "meta",
                self.novel.metadata.end_date,
                {"name": "end_date", "content": self.novel.metadata.end_date},
            )

    def _add_calibre_metadata(self, collection_idx: int) -> None:
        self.epub_book.add_metadata(
            "OPF",
            "meta",
            "",
            {"name": "calibre:series", "content": self.book_title},
        )
        self.epub_book.add_metadata(
            "OPF",
            "meta",
            "",
            {"name": "calibre:series_index", "content": str(collection_idx)},
        )

    def _add_cover_image(self) -> None:
        try:
            cover_image_content = self.novel.novel_data_helper.load_novel_cover()
            self.epub_book.set_cover("cover.jpg", cover_image_content)
            self.epub_book.spine += ["cover"]
        except CoverImageNotFoundError:
            logger.debug("No Cover Image was found.")
        except NovelDataError as e:
            logger.warning(f"An error ocurred while loading the cover image: {e}")

    def _add_chapter_to_epub_book(self, chapter: Chapter):
        if chapter.chapter_html_filename is None:
            logger.warning(
                f"Chapter with url '{chapter.chapter_url}' has no HTML Filename, there may be an error."
            )
            chapter.chapter_html_filename = generate_file_name_from_url(
                chapter.chapter_url
            )

        if chapter.chapter_content is None:
            raise ChapterContentNotFoundError(
                f'Chapter with url "{chapter.chapter_url}" has no content or has not been scrapped yet.'
            )
        if chapter.chapter_title is None:
            raise ChapterTitleNotFoundError(
                f'Chapter with url "{chapter.chapter_url} has no title or has not been scrapped yet.'
            )

        file_name = chapter.chapter_html_filename.replace(".html", "xhtml")

        chapter_epub = epub.EpubHtml(title=chapter.chapter_title, file_name=file_name)
        chapter_epub.set_content(chapter.chapter_content)
        self.epub_book.add_item(chapter_epub)

        link = epub.Link(file_name, chapter.chapter_title, file_name.rstrip(".xhtml"))
        toc = self.epub_book.toc
        toc.append(link)
        self.epub_book.toc = toc
        self.epub_book.spine.append(chapter_epub)
        logger.debug(f"Chapter with URL '{chapter.chapter_url}' added to the book.")

    def _save_epub_book(self, output_path: Path):
        logger.debug(f"Trying to save book to {output_path}...")
        if output_path.exists():
            logger.warning(
                f"The file '{output_path}' already exists and will be overwritten."
            )
        try:
            epub.write_epub(
                str(output_path), self.epub_book, {"raise_exceptions": True}
            )
            logger.info(f"Book '{self.book_title}' saved to file '{output_path}'.")
        except OSError or PermissionError as e:
            raise SaveBookError(f"Could not Save Book to {output_path}: {e}") from e
