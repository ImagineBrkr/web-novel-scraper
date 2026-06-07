import re
from typing import List, Optional
from bs4 import BeautifulSoup
import json

from web_novel_scraper.custom_processor.custom_processor import (
    CustomProcessor,
    ProcessorRegistry,
)
from web_novel_scraper.exceptions import DecodeProcessorError


class BOTITranslationTocMainUrlProcessor(CustomProcessor):
    def process(self, toc_main_url: str) -> str:
        pattern_novel_id = r"/book/(\d+)"
        match = re.search(pattern_novel_id, toc_main_url)
        if match is None:
            raise DecodeProcessorError(
                "Could not get Novel Id, check if the toc_main_url has the correct format"
                " (https://www.botitranslation.com/book/{novel-id}-{novel-title})"
            )
        return f"https://api.mystorywave.com/story-wave-backend/api/v1/content/chapters/page?sortDirection=ASC&bookId={match.group(1)}&pageNumber=1&pageSize=10000"


class BOTITranslationIndexProcessor(CustomProcessor):
    def process(self, html: str) -> Optional[List[str]]:
        # TODO: When using Flaresolver, the JSON Response will be inside an HTML
        # In the future request_manager should always return a JSON object for this case

        if html.startswith("<html>"):
            soup = BeautifulSoup(html, "html.parser")
            chapters_json_text = soup.select("body pre")[0].text
        else:
            chapters_json_text = html

        chapters_json = json.loads(chapters_json_text)

        chapters_list = chapters_json["data"]["list"]

        if len(chapters_list) == 0:
            return None
        return [
            f"https://api.mystorywave.com/story-wave-backend/api/v1/content/chapters/{chapter['id']}"
            for chapter in chapters_list
            if chapter["paywallStatus"] == "free"
        ]


class BOTITranslationChapterContentProcessor(CustomProcessor):
    def process(self, html: str) -> Optional[str]:

        if html.startswith("<html>"):
            soup = BeautifulSoup(html, "html.parser")
            chapter_json_text = soup.select("body pre")[0].text
        else:
            chapter_json_text = html

        chapter_json = json.loads(chapter_json_text)

        chapter_content = chapter_json["data"]["content"]

        return chapter_content


class BOTITranslationChapterTitleProcessor(CustomProcessor):
    def process(self, html: str) -> Optional[str]:

        if html.startswith("<html>"):
            soup = BeautifulSoup(html, "html.parser")
            chapter_json_text = soup.select("body pre")[0].text
        else:
            chapter_json_text = html

        chapter_json = json.loads(chapter_json_text)

        chapter_title = chapter_json["data"]["title"]

        return chapter_title


ProcessorRegistry.register(
    "botitranslation.com", "toc_main_url", BOTITranslationTocMainUrlProcessor()
)
ProcessorRegistry.register(
    "botitranslation.com", "index", BOTITranslationIndexProcessor()
)
ProcessorRegistry.register(
    "botitranslation.com", "title", BOTITranslationChapterTitleProcessor()
)
ProcessorRegistry.register(
    "botitranslation.com", "content", BOTITranslationChapterContentProcessor()
)