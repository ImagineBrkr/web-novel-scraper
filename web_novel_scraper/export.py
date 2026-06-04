from web_novel_scraper.novel_scraper import Novel
from web_novel_scraper.logger_manager import create_logger
from web_novel_scraper.exceptions import (
    ExportError,
    ExportFormatNotSupportedError,
    ExporterError,
    InvalidChapterByBookFromChapterRangeError,
    InvalidEndChapterFromChapterRangeError,
    InvalidStartChapterFromChapterRangeError,
)
from web_novel_scraper.exporters.base_exporter import BaseExporter
from web_novel_scraper.exporters.epub_exporter import EPUBExporter

logger = create_logger(__name__)

# HTML

EXPORTERS = {"epub": EPUBExporter}


class NovelExporter:
    @staticmethod
    def export_novel_to_format(
        novel: Novel,
        format: str,
        start_chapter: int = 1,
        end_chapter: int = None,
        chapters_by_book: int = 100,
    ) -> None:
        if format not in EXPORTERS:
            raise ExportFormatNotSupportedError(
                f"Export Format '{format}' not supported."
            )

        logger.info(f"Exporting novel to {format}...")

        if chapters_by_book < 1:
            raise InvalidChapterByBookFromChapterRangeError(
                f'Invalid Chapter Range: The number of Chapter By Book "{chapters_by_book}" can not be less than 1.'
            )

        if start_chapter < 1:
            raise InvalidStartChapterFromChapterRangeError(
                f"Invalid Chapter Range: The Start Chapter {start_chapter} can not be less than 1."
            )

        if start_chapter > len(novel.chapters):
            raise InvalidStartChapterFromChapterRangeError(
                f"Invalid Chapter Range: The Start Chapter {start_chapter} is bigger than the number of chapters recorded from TOC ({len(novel.chapters)})"
            )

        if end_chapter is None:
            logger.info(
                "No End Chapter was specified, so the last available Chapter will be used."
            )
            end_chapter = len(novel.chapters)
        else:
            if end_chapter < 1:
                raise InvalidEndChapterFromChapterRangeError(
                    f"Invalid Chapter Range: The End Chapter {start_chapter} can not be less than 1."
                )
            elif end_chapter < start_chapter:
                raise InvalidEndChapterFromChapterRangeError(
                    f"Invalid Chapter Range: The End Chapter '{end_chapter}' is smaller than the Start Chapter '{start_chapter}'"
                )

            elif end_chapter > len(novel.chapters):
                logger.warning(
                    f"The End Chapter specified '({end_chapter})' is bigger than the number of chapters ({len(novel.chapters)}), so that number will be used instead."
                )
                end_chapter = len(novel.chapters)

        idx = 1
        book_start = start_chapter
        while book_start <= end_chapter:
            book_end = min(book_start + chapters_by_book - 1, end_chapter)
            NovelExporter._save_chapters_to_format(
                novel=novel,
                exporter=EXPORTERS[format],
                start_chapter=book_start,
                end_chapter=book_end,
            )
            book_start = book_start + chapters_by_book
            idx = idx + 1

    @staticmethod
    def _save_chapters_to_format(
        novel: Novel,
        exporter: BaseExporter,
        start_chapter: int,
        end_chapter: int = None,
    ):

        idx_start = start_chapter - 1
        idx_end = end_chapter

        book_title = f"{novel.title} Chapters {start_chapter} - {end_chapter}"
        chapters = novel.chapters[idx_start:idx_end]

        for chapter in chapters:
            chapter = novel.scrap_chapter(chapter)

        exporter = exporter()
        try:
            exporter.export_novel_to_book(
                novel=novel,
                chapters=chapters,
                book_title=book_title,
                output_directory=novel.novel_data_helper.novel_base_dir,
            )
        except ExporterError as e:
            raise ExportError(f"Could not export the novel to a book: {str(e)}")

        novel.save_novel()
