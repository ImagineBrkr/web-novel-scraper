import re
from typing import List, Optional
from ..custom_processor import CustomProcessor, ProcessorRegistry

class NovelHiIndexProcessor(CustomProcessor):
    def process(self, html: str) -> Optional[List[str]]:
        pattern_chapter = r"gtag_report_conversion\(&#39;(\d+)&#39;\)"
        pattern_novel_name = r'id="bookSimpleName"\s+value="([^"]+)"'
        match_novel_name = re.search(pattern_novel_name, html)
        match_chapters = re.findall(pattern_chapter, html, re.DOTALL)
        if match_novel_name is None:
            raise Exception("Could not get Novel Name")

        if len(match_chapters) == 0:
            return None

        return [f'https://novelhi.com/s/{match_novel_name.group(1)}/{chapter_index}' for chapter_index in match_chapters]

ProcessorRegistry.register('novelhi.com', 'index', NovelHiIndexProcessor())
