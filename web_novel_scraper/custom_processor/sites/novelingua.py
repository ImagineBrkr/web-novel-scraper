from bs4 import BeautifulSoup
from typing import Optional
from ..custom_processor import CustomProcessor, ProcessorRegistry
from web_novel_scraper.exceptions import HTMLParseError

GENESIS_STUDIO_VIEWER_URL = "https://genesistudio.com/viewer"


class NovelinguaTitleProcessor(CustomProcessor):
    def process(self, html: str) -> Optional[str]:
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception as e:
            raise HTMLParseError(f"Error parsing HTML with BeautifulSoup: {e}")
        chapter_title_temp = soup.select("div.pagelayer-text-holder > p > span")
        if len(chapter_title_temp) > 0:
            for item in chapter_title_temp:
                text = item.get_text()
                if text.startswith("Chapter"):
                    return text

        return None


ProcessorRegistry.register("novelingua.com", "title", NovelinguaTitleProcessor())
