import re
import json
from typing import List, Optional
from ..custom_processor import CustomProcessor, ProcessorRegistry

class RoyalRoadChaptersProcessor(CustomProcessor):
    def process(self, html: str) -> Optional[List[dict]]:
        pattern = r'window\.chapters\s*=\s*(\[.*?\]);'
        match = re.search(pattern, html, re.DOTALL)

        if not match:
            return None

        try:
            chapters_json = match.group(1)
            chapters = json.loads(chapters_json)
            chapters = [chapter['url'] for chapter in chapters if 'url' in chapter]
            return chapters
        except (json.JSONDecodeError, IndexError):
            return None

ProcessorRegistry.register('www.royalroad.com', 'index', RoyalRoadChaptersProcessor())