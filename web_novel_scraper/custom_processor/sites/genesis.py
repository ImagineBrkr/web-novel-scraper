import re
import json
from typing import List, Optional
from ..custom_processor import CustomProcessor, ProcessorRegistry

GENESIS_STUDIO_VIEWER_URL = 'https://genesistudio.com/viewer'

class GenesisChaptersProcessor(CustomProcessor):
    def process(self, html: str) -> Optional[List[dict]]:
        pattern = r',chapters:\s*{\s*free:\s*(\[.*?"}}])'
        match = re.search(pattern, html, re.DOTALL)

        if not match:
            if not match:
                return None

        try:
            chapters_json = match.group(1).strip()
            replaces = {
                "chapter_title:": '"chapter_tile":',
                "id:": '"id":',
                "nsfw:": '"nsfw":',
                "required_tier:": '"required_tier":',
                "date_created:": '"date_created":',
                "spoiler_title:": '"spoiler_title":',
                "chapter_number:": '"chapter_number":',
                "novel:": '"novel":',
            }
            # Ensure the JSON string ends properly
            if not chapters_json.endswith(']'):
                chapters_json += ']'
            for old_key, new_key in replaces.items():
                chapters_json = chapters_json.replace(old_key, new_key)

            chapters = json.loads(chapters_json)
            chapters_url = []
            for chapter in chapters:
                chapters_url.append(f"{GENESIS_STUDIO_VIEWER_URL}/{chapter['id']}")
            print(chapters)
            return chapters_url
            
        except (json.JSONDecodeError, IndexError) as e:
            print(f"Error processing JSON: {str(e)}")
            return None

ProcessorRegistry.register('genesistudio.com', 'index', GenesisChaptersProcessor())
