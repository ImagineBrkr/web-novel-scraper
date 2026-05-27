from web_novel_scraper.novel_scraper import Novel
from web_novel_scraper.models import Chapter
from web_novel_scraper.logger_manager import create_logger
from web_novel_scraper.exporters.html_exporter import save_novel_html
from web_novel_scraper.exceptions import ValidationError, ScraperError

logger = create_logger(__name__)

# HTML


def save_novel_to_html(
    novel: Novel,
    start_chapter: int = 1,
    end_chapter: int = None,
    chapters_by_book: int = 100,
) -> None:
    logger.debug("Saving novel to HTML...")

    if start_chapter < 1:
        logger.error("Start chapter is invalid.")
        raise ValidationError("Start chapter is invalid.")

    if start_chapter > len(novel.chapters):
        logger.error(
            f"The start chapter is bigger than the number of chapters saved ({len(novel.chapters)})"
        )
        raise ValidationError(
            f"The start chapter is bigger than the number of chapters saved ({len(novel.chapters)})"
        )

    if not end_chapter:
        end_chapter = len(novel.chapters)
    elif end_chapter > len(novel.chapters):
        end_chapter = len(novel.chapters)
        logger.info(
            f"The end chapter is bigger than the number of chapters, "
            f"automatically setting it to {end_chapter}."
        )

    idx = 1
    start = start_chapter
    while start <= end_chapter:
        end = min(start + chapters_by_book - 1, end_chapter)
        result = _save_chapters_to_html(
            novel=novel, start_chapter=start, end_chapter=end
        )
        if not result:
            logger.critical(
                f"Error with saving novel to HTML, with start chapter: "
                f"{start_chapter} and end chapter: {end_chapter}"
            )
        start = start + chapters_by_book
        idx = idx + 1


def _save_chapters_to_html(novel: Novel, start_chapter: int, end_chapter: int = None):
    if start_chapter > len(novel.chapters):
        logger.error("start_chapter out of range")
        return None
    # If end_chapter is not set, we set it to idx_start + chapters_num - 1
    if not end_chapter:
        end_chapter = len(novel.chapters)
    # If end_chapter is out of range, we set it to the last chapter
    if end_chapter > len(novel.chapters):
        end_chapter = len(novel.chapters)

    # We use a slice so every chapter starting from idx_start and before idx_end
    idx_start = start_chapter - 1
    idx_end = end_chapter
    # We create the epub book
    book_title = f"{novel.title} Chapters {start_chapter} - {end_chapter}"
    chapters = novel.chapters[idx_start:idx_end]

    for chapter in chapters:
        chapter = novel.scrap_chapter(chapter)
        if chapter is None:
            raise ScraperError("Error Reading Chapter")

    save_novel_html(
        novel=novel,
        chapters=chapters,
        output_path=novel.novel_data_helper.novel_base_dir / f"{book_title}.html",
    )

    novel.save_novel()
    return True
