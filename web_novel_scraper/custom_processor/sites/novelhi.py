import re
from typing import List, Optional
from ..custom_processor import CustomProcessor, ProcessorRegistry
from web_novel_scraper.utils import DecodeProcessorError


class NovelHiIndexProcessor(CustomProcessor):
    def process(self, html: str) -> Optional[List[str]]:
        pattern_chapter = r"gtag_report_conversion\(&#39;(\d+)&#39;\)"
        pattern_novel_name = r'id="bookSimpleName"\s+value="([^"]+)"'
        match_novel_name = re.search(pattern_novel_name, html)
        match_chapters = re.findall(pattern_chapter, html, re.DOTALL)
        if match_novel_name is None:
            raise DecodeProcessorError("Could not get Novel Name, check if the html is valid.")

        if len(match_chapters) == 0:
            return None

        return [f'https://novelhi.com/s/{match_novel_name.group(1)}/{chapter_index}' for chapter_index in
                match_chapters]


class NovelHiTocMainUrlProcessor(CustomProcessor):
    def process(self, toc_main_url: str) -> str:
        pattern_novel_id = r"novelhi.com/s/([^/?]+)"
        match = re.search(pattern_novel_id, toc_main_url)
        if match is None:
            raise DecodeProcessorError("Could not get Novel Id, check if the toc_main_url has the correct format"
                                       "(https://novelhi.com/s/{novel-id}).")
        return f'https://novelhi.com/s/index/{match.group(1)}/'


ProcessorRegistry.register('novelhi.com', 'index', NovelHiIndexProcessor())
ProcessorRegistry.register('novelhi.com', 'toc_main_url', NovelHiTocMainUrlProcessor())
