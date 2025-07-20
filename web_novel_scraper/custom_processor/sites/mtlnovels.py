import re
from typing import List, Optional
from ..custom_processor import CustomProcessor, ProcessorRegistry
from web_novel_scraper.utils import DecodeProcessorError


class MtlNovelsTocMainUrlProcessor(CustomProcessor):
    def process(self, toc_main_url: str) -> str:
        base = "https://www.mtlnovels.com/"
        if not toc_main_url.startswith(base):
            raise DecodeProcessorError("The original url doesn't have the correct format."
                                       "https://www.mtlnovels.com/{novel-id}")

        path = toc_main_url[len(base):].rstrip("/")
        if "/" in path or not path:
            raise DecodeProcessorError("The original url doesn't have the correct format."
                                       "https://www.mtlnovels.com/{novel-id}")

        return f"{base}{path}/chapter-list/"


ProcessorRegistry.register('mtlnovels.com', 'toc_main_url', MtlNovelsTocMainUrlProcessor())
