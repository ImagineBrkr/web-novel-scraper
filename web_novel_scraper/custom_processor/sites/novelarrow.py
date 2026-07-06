import json
from typing import List

from bs4 import BeautifulSoup
from web_novel_scraper.custom_processor.custom_processor import (
    CustomProcessor,
    ProcessorRegistry,
)
from web_novel_scraper.exceptions import DecodeProcessorError


# https://novelarrow.com/novel/{novel-id}
class NovelarrowTocMainUrlProcessor(CustomProcessor):
    def process(self, toc_main_url: str) -> str:
        novel_id = _extract_novel_id_from_toc_main_url(toc_main_url)

        return f"https://novelarrow.com/api-web/novels/{novel_id}/chapters?sort=asc"


def _extract_novel_id_from_toc_main_url(toc_main_url: str | None) -> str:
    if not toc_main_url:
        raise DecodeProcessorError(
            "Could not get Novel Id, toc_main_url was not provided to the processor."
        )

    if not toc_main_url.startswith(
        "https://novelarrow.com/novel/"
    ) and not toc_main_url.startswith("https://www.novelarrow.com/novel/"):
        raise DecodeProcessorError(
            "Could not get Novel Id, check if the toc_main_url has the correct format"
            " (https://novelarrow.com/novel/{novel-id})"
        )

    toc_main_url_stripped = toc_main_url.removeprefix("https://novelarrow.com/novel/")
    toc_main_url_stripped = toc_main_url_stripped.removeprefix(
        "https://www.novelarrow.com/novel/"
    )
    return toc_main_url_stripped.split("/")[0].split("?")[0].split("#")[0]


class NovelarrowIndexProcessor(CustomProcessor):
    def process(self, html: str, toc_main_url: str) -> List[str] | None:
        # TODO: When using Flaresolver, the JSON Response will be inside an HTML
        # In the future request_manager should always return a JSON object for this case

        if html.startswith("<html>"):
            soup = BeautifulSoup(html, "html.parser")
            chapters_json_text = soup.select("body pre")[0].text
        else:
            chapters_json_text = html

        chapters_json = json.loads(chapters_json_text)

        chapters_list = chapters_json["items"]
        novel_id = _extract_novel_id_from_toc_main_url(toc_main_url)
        if len(chapters_list) == 0:
            return None
        return [
            f"https://novelarrow.com/chapter/{novel_id}/{chapter['chapter_id']}"
            for chapter in chapters_list
            if chapter["premium_content"] is False
        ]


ProcessorRegistry.register(
    "novelarrow.com", "toc_main_url", NovelarrowTocMainUrlProcessor()
)
ProcessorRegistry.register("novelarrow.com", "index", NovelarrowIndexProcessor())
