import re
from typing import Optional
from web_novel_scraper.custom_processor.custom_processor import (
    CustomProcessor,
    ProcessorRegistry,
)


class EmpireNovelTitleProcessor(CustomProcessor):
    def process(self, html: str) -> Optional[str]:
        match = re.search(r'<div id="read-novel"[^>]*>\s*([^<]+)', html, re.IGNORECASE)
        return match.group(1).strip() if match else None


ProcessorRegistry.register("empirenovel.com", "title", EmpireNovelTitleProcessor())
