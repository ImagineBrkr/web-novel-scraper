from pathlib import Path
from typing import Protocol
from web_novel_scraper.models import Chapter
from web_novel_scraper.novel_scraper import Novel


class BaseExporter(Protocol):
    def export_novel(
        novel: Novel,
        chapters: list[Chapter],
        output_path: str | Path,
    ) -> None:
        pass
