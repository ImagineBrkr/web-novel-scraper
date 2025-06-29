import re
from typing import Optional
from ..custom_processor import CustomProcessor, ProcessorRegistry

class GenesisNextPageProcessor(CustomProcessor):
    def process(self, html: str) -> Optional[str]:
        pattern = r'href="([^"]+page=\d+[^"]*)">></a'
        match = re.search(pattern, html)
        if match is None:
            return None
        next_page = match.group(1)
        next_page = next_page.replace('&amp;', '&')
        return f'https://www.fanmtl.com{next_page}'

ProcessorRegistry.register('fanmtl.com', 'next_page', GenesisNextPageProcessor())
