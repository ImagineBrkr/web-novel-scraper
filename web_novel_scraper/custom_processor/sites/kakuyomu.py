from bs4 import BeautifulSoup
from typing import List, Optional
from ..custom_processor import CustomProcessor, ProcessorRegistry
from web_novel_scraper.exceptions import HTMLParseError, DecodeError

import json


class KakuyomuIndexProcessor(CustomProcessor):
    def process(self, html: str) -> Optional[List[str]]:
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception as e:
            raise HTMLParseError(f"Error parsing HTML with BeautifulSoup: {e}")
        chapters_json = soup.select_one("script#__NEXT_DATA__")
        if chapters_json is None:
            return None
        try:
            chapters_urls = []
            chapters_json = json.loads(chapters_json.string)
            work_id = chapters_json["props"]["pageProps"]["additionalDataLayer"][
                "workId"
            ]
            chapters_json = chapters_json["props"]["pageProps"]["__APOLLO_STATE__"]
            for key in chapters_json:
                if key.startswith("Episode:"):
                    chapters_urls.append(
                        f"https://kakuyomu.jp/works/{work_id}/episodes/{chapters_json[key]['id']}"
                    )
            return chapters_urls
        except Exception as e:
            raise DecodeError(f"Error parsing JSON from the script tag: {e}")


ProcessorRegistry.register("kakuyomu.jp", "index", KakuyomuIndexProcessor())
