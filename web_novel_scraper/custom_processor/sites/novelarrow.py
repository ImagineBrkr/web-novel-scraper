import json
from typing import List

from bs4 import BeautifulSoup
from web_novel_scraper.custom_processor.custom_processor import (
    CustomProcessor,
    ProcessorRegistry,
)
from web_novel_scraper.exceptions import DecodeProcessorError

# TODO: When using Flaresolver, the JSON Response will be inside an HTML
# In the future request_manager should always return a JSON object for this case


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
        # TODO

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
            f"https://novelarrow.com/api-web/novels/{novel_id}/chapters/{chapter['chapter_id']}"
            for chapter in chapters_list
            if chapter["premium_content"] is False
        ]

        return [
            f"https://novelarrow.com/chapter/{novel_id}/{chapter['chapter_id']}"
            for chapter in chapters_list
            if chapter["premium_content"] is False
        ]


class NovelarrowContentProcessor(CustomProcessor):
    def process(self, html: str) -> str:
        # TODO

        if html.startswith("<html>"):
            soup = BeautifulSoup(html, "html.parser")
            chapters_json_text = soup.select("body pre")[0].text
        else:
            chapters_json_text = html

        chapter_json = json.loads(chapters_json_text)
        try:
            chapter_data = chapter_json["item"]["chapterInfo"]
        except KeyError:
            raise DecodeProcessorError(
                'JSON Response does not contain "item" or "chapterInfo" key, decode guide may be outdated.'
            )

        try:
            chapter_content = chapter_data["chapter_content"]
        except KeyError:
            raise DecodeProcessorError(
                'JSON Response does not contain "chapter_content" key, decode guide may be outdated.'
            )
        return chapter_content


class NovelarrowTitleProcessor(CustomProcessor):
    def process(self, html: str) -> str:
        # TODO

        if html.startswith("<html>"):
            soup = BeautifulSoup(html, "html.parser")
            chapters_json_text = soup.select("body pre")[0].text
        else:
            chapters_json_text = html

        chapter_json = json.loads(chapters_json_text)
        try:
            chapter_data = chapter_json["item"]["chapterInfo"]
        except KeyError:
            raise DecodeProcessorError(
                'JSON Response does not contain "item" or "chapterInfo" key, decode guide may be outdated.'
            )

        try:
            chapter_title = chapter_data["chapter_name"]
        except KeyError:
            raise DecodeProcessorError(
                'JSON Response does not contain "chapter_name" key, decode guide may be outdated.'
            )
        return chapter_title


ProcessorRegistry.register(
    "novelarrow.com", "toc_main_url", NovelarrowTocMainUrlProcessor()
)
ProcessorRegistry.register("novelarrow.com", "index", NovelarrowIndexProcessor())
ProcessorRegistry.register("novelarrow.com", "content", NovelarrowContentProcessor())
ProcessorRegistry.register("novelarrow.com", "title", NovelarrowTitleProcessor())
