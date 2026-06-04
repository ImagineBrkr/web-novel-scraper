from pathlib import Path
from typing import Protocol
from web_novel_scraper.models import Chapter
from web_novel_scraper.novel_scraper import Novel


class BaseExporter(Protocol):
    file_extension: str

    def export_novel_to_book(
        self,
        novel: Novel,
        chapters: list[Chapter],
        book_title: str,
        output_directory: str | Path,
    ) -> None:
        pass
