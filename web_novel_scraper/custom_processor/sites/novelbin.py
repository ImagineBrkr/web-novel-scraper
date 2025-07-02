import re
from ..custom_processor import CustomProcessor, ProcessorRegistry
from web_novel_scraper.utils import DecodeProcessorError


class NovelbinTocMainUrlProcessor(CustomProcessor):
    def process(self, toc_main_url: str) -> str:
        pattern_novel_id = r"novel-book/([^/?]+)"
        match = re.search(pattern_novel_id, toc_main_url)
        if match is None:
            raise DecodeProcessorError("Could not get Novel Id, check if the toc_main_url has the correct format"
                                       "(https://novelbin.me/novel-book/{novel-id}).")
        return f'https://novelbin.me/ajax/chapter-archive?novelId={match.group(1)}'


ProcessorRegistry.register('novelbin.me', 'toc_main_url', NovelbinTocMainUrlProcessor())
ProcessorRegistry.register('novelbin.com', 'toc_main_url', NovelbinTocMainUrlProcessor())
