from bs4 import BeautifulSoup
from typing import Optional
from ..custom_processor import CustomProcessor, ProcessorRegistry
from web_novel_scraper.utils import HTMLParseError


class SyosetuNextPageProcessor(CustomProcessor):
    def process(self, html: str) -> Optional[str]:
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception as e:
            raise HTMLParseError(f"Error parsing HTML with BeautifulSoup: {e}")
        next_page_path = soup.select_one("a.c-pager__item--next")
        if next_page_path is not None:
            return f"https://ncode.syosetu.com{next_page_path['href']}"
        return None


ProcessorRegistry.register("ncode.syosetu.com", "next_page", SyosetuNextPageProcessor())
