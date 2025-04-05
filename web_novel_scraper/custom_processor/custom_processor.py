from abc import ABC, abstractmethod
from typing import Any, Dict

class CustomProcessor(ABC):
    @abstractmethod
    def process(self, html: str) -> Any:
        """Process the HTML content using custom logic"""
        pass

class ProcessorRegistry:
    _processors: Dict[str, Dict[str, CustomProcessor]] = {}

    @classmethod
    def register(cls, host: str, content_type: str, processor: CustomProcessor):
        if host not in cls._processors:
            cls._processors[host] = {}
        cls._processors[host][content_type] = processor

    @classmethod
    def get_processor(cls, host: str, content_type: str) -> CustomProcessor:
        return cls._processors.get(host, {}).get(content_type)

    @classmethod
    def has_processor(cls, host: str, content_type: str) -> bool:
        return bool(cls.get_processor(host, content_type))