from __future__ import annotations

from dataclasses import dataclass, field, asdict
from dataclasses_json import dataclass_json, config
from typing import Optional, Tuple
from urllib.parse import urlparse
import pprint

from .utils import _always, ValidationError


def _pretty(obj, *, skip: set[str] | None = None) -> str:
    """Pretty-print dataclass dict, omits keys in *skip*."""
    d = asdict(obj)
    if skip:
        for key in skip:
            d.pop(key, None)
    return pprint.pformat(d, sort_dicts=False, compact=True)


@dataclass_json
@dataclass(slots=True, frozen=True)
class Metadata:
    author: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    language: str = "en"
    description: Optional[str] = None
    tags: Tuple[str, ...] = field(default_factory=tuple)

    def __str__(self) -> str:
        return "Metadata:\n" + _pretty(self)


@dataclass_json
@dataclass(slots=True, frozen=True)
class ScraperBehavior:
    # Some novels already have the title in the content.
    save_title_to_content: bool = False
    # Some novels have the toc link without the host
    auto_add_host: bool = False
    # Some hosts return 403 when scrapping, this will force the use of FlareSolver
    # to save time
    force_flaresolver: bool = False
    # When you clean the HTML files, you can use hard clean by default
    hard_clean: bool = False

    def __str__(self) -> str:
        return "ScraperBehavior:\n" + _pretty(self)


@dataclass_json()
@dataclass
class Chapter:
    chapter_url: str
    chapter_html: Optional[str] = field(
        default=None,
        repr=False,
        compare=False,
        metadata=config(exclude=_always)
    )
    chapter_content: Optional[str] = field(
        default=None,
        repr=False,
        compare=False,
        metadata=config(exclude=_always)
    )
    chapter_html_filename: Optional[str] = None
    chapter_title: Optional[str] = field(default=None, compare=False)

    def __post_init__(self):
        if not urlparse(self.chapter_url).scheme:
            raise ValidationError(f"Invalid URL: {self.chapter_url}")

    def __str__(self) -> str:
        return "Chapter:\n" + _pretty(self, skip={"chapter_html"})
