from .custom_processor import CustomProcessor, ProcessorRegistry
from web_novel_scraper.custom_processor.sites import (
    royalroad,
    genesis,
    fanmtl,
    novelhi,
    novelbin,
)

__all__ = [
    "royalroad",
    "genesis",
    "fanmtl",
    "novelhi",
    "novelbin",
    "CustomProcessor",
    "ProcessorRegistry",
]
