import json
from bs4 import BeautifulSoup

from web_novel_scraper.custom_processor.custom_processor import (
    CustomProcessor,
    ProcessorRegistry,
)
from web_novel_scraper.exceptions import DecodeProcessorError


class FreeWebNovelMainUrlProcessor(CustomProcessor):
    def process(self, toc_main_url: str) -> str:
        if not toc_main_url.startswith("https://freewebnovel.com/novel/"):
            raise DecodeProcessorError(
                "Not supported URL format, check if the toc_main_url has the correct format"
                " (https://freewebnovel.com/novel/{novel-id})."
            )
        toc_main_url = toc_main_url.rstrip("/")
        return f'{toc_main_url}?ajax=chapters&page=1&pageSize=200'

class FreeWebNovelNextTocPageUrlProcessor(CustomProcessor):
    def process(self, html: str) -> str | None:
        try:
            json_data = json.loads(html)
        except json.JSONDecodeError:
            raise DecodeProcessorError("Could not obtain JSON data from TOC HTML.")

        if "page" not in json_data or "totalPage" not in json_data or "html" not in json_data:
            raise DecodeProcessorError("TOC JSON data does not contain required keys 'page', 'totalPage', and 'html'.")

        if json_data["page"] >= json_data["totalPage"]:
            return None

        # TODO Find a better way than using the Chapter URL to get the novel ID
        chapters_data = BeautifulSoup(json_data["html"], "html.parser")
        chapter_link = chapters_data.select_one('li a')['href']
        novel_link = chapter_link.split('/')[:-1]   # Remove the last part (chapter) to get the novel link
        novel_link = '/'.join(novel_link)

        return f'https://freewebnovel.com{novel_link}?ajax=chapters&page={json_data["page"] + 1}&pageSize=200'


class FreeWebNovelIndexProcessor(CustomProcessor):
    def process(self, html: str) -> int:
        try:
            json_data = json.loads(html)
        except json.JSONDecodeError:
            raise DecodeProcessorError("Could not obtain JSON data from TOC HTML.")

        if "html" not in json_data:
            raise DecodeProcessorError("TOC JSON data does not contain required key 'html'.")

        chapters_data = BeautifulSoup(json_data["html"], "html.parser")
        chapters = chapters_data.select('li a')
        chapters_link = [chapter['href'] for chapter in chapters]
        return chapters_link

ProcessorRegistry.register("freewebnovel.com", "toc_main_url", FreeWebNovelMainUrlProcessor())
ProcessorRegistry.register("freewebnovel.com", "next_page", FreeWebNovelNextTocPageUrlProcessor())
ProcessorRegistry.register("freewebnovel.com", "index", FreeWebNovelIndexProcessor())

