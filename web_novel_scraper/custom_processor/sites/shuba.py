from web_novel_scraper.custom_processor.custom_processor import (
    CustomProcessor,
    ProcessorRegistry,
)
from web_novel_scraper.exceptions import DecodeProcessorError


class ShubaTocMainUrlProcessor(CustomProcessor):
    def process(self, toc_main_url: str) -> str:
        toc_main_url = toc_main_url.removeprefix("https://")
        toc_main_url = toc_main_url.removeprefix("www.")
        base = "69shuba.com/book/"
        if not toc_main_url.startswith(base):
            raise DecodeProcessorError(
                "The original url doesn't have the correct format. "
                "https://www.69shuba.com/book/{novel-id}.htm"
            )

        path = toc_main_url[len(base) :].rstrip("/").rstrip(".htm")
        if "/" in path or not path:
            raise DecodeProcessorError(
                "The original url doesn't have the correct format. "
                "https://www.69shuba.com/book/{novel-id}.htm"
            )

        return f"https://www.{base}{path}/"


ProcessorRegistry.register("69shuba.com", "toc_main_url", ShubaTocMainUrlProcessor())
