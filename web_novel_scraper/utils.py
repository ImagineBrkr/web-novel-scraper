import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import hashlib
from urllib.parse import urlparse
import re
import unicodedata


def _always(_: object) -> bool:
    """Predicate used by dataclasses_json to skip a field."""
    return True


## EXCEPTIONS

class ScraperError(Exception):
    """Default Exception for Scraper Exceptions"""


class NetworkError(ScraperError):
    """Exception raised for any exception for request operations"""


class DecodeError(ScraperError):
    """Exception raised for any exception for decoding operations"""


class HTMLParseError(DecodeError):
    """Raised when HTML parsing fails"""


class DecodeGuideError(DecodeError):
    """Raised when there are issues with decode guide configuration"""


class ContentExtractionError(DecodeError):
    """Raised when content extraction fails"""


class DecodeProcessorError(DecodeError):
    """Raised when there is an error in a decoder processor"""


class FileManagerError(ScraperError):
    """Exception raised for any exception for file operations"""


class ValidationError(ScraperError):
    """Exception raised for any exception for invalid values"""


## FILE OPERATIONS HELPER

class FileOps:
    """Static helper for disc operations."""

    ## HELPERS

    @staticmethod
    def _atomic_tmp(path: Path) -> Path:
        """Temporary file path in the same directory as *path*."""
        return path.with_suffix(path.suffix + ".tmp")

    ## DIRECTORY MANAGEMENT
    @staticmethod
    def ensure_dir(path: Path) -> Path:
        """Create *path* (and parents) if missing."""
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path
        except Exception as e:
            raise FileManagerError(str(e)) from e

    ## READ OPERATIONS

    @staticmethod
    def read_text(path: Path) -> Optional[str]:
        """Return UTF-8 contents or None if *path* does not exist."""
        if not path.exists():
            return None
        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            raise FileManagerError(str(e)) from e

    @staticmethod
    def read_json(path: Path | str) -> Optional[dict]:
        """Return JSON object or None if *path* does not exist."""
        path = Path(path)
        raw = FileOps.read_text(path)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.decoder.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in {path}: {e}") from e

    @staticmethod
    def read_binary(path: Path) -> Optional[bytes]:
        """Return binary contents or None if *path* does not exist."""
        if not path.exists():
            return None
        try:
            return path.read_bytes()
        except Exception as e:
            raise FileManagerError(str(e)) from e

    ## WRITE OPERATION

    @staticmethod
    def save_text(path: Path, text: str) -> None:
        """Atomically write UTF-8 text to *path*."""
        tmp = FileOps._atomic_tmp(path)
        try:
            tmp.write_text(text, encoding="utf-8")
            tmp.replace(path)
        except Exception as e:
            FileOps.delete(tmp)
            raise FileManagerError(str(e)) from e

    @staticmethod
    def save_json(path: Path, obj: dict) -> None:
        """Atomically write pretty-printed JSON to *path*."""
        tmp = FileOps._atomic_tmp(path)
        try:
            tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(path)
        except Exception as e:
            FileOps.delete(tmp)
            raise FileManagerError(str(e)) from e

    @staticmethod
    def save_binary(path: Path, data: bytes) -> None:
        """Atomically write binary data to *path* (e.g., cover images)."""
        tmp = FileOps._atomic_tmp(path)
        try:
            tmp.write_bytes(data)
            tmp.replace(path)
        except Exception as e:
            FileOps.delete(tmp)
            raise FileManagerError(str(e)) from e

    ## DELETE/COPY OPERATIONS

    @staticmethod
    def delete(path: Path) -> None:
        """Delete *path* if it exists."""
        try:
            if path.exists():
                path.unlink()
        except Exception as e:
            raise FileManagerError(str(e)) from e

    @staticmethod
    def copy(src: Path, dst: Path) -> None:
        """Copy *src* to *dst*."""
        try:
            shutil.copy(src, dst)
        except Exception as e:
            raise FileManagerError(str(e)) from e


def _normalize_dirname(name: str) -> str:
    """
    Keep whitespace as-is while replacing any other unsupported characters
    with an underscore.
    Allowed: letters, digits, underscore, hyphen, and spaces.
    """
    # Collapse multiple spaces into a single space (optional; comment out if not desired)
    name = re.sub(r'\s+', ' ', name.strip())

    # Replace any char that is *not* letter, digit, underscore, hyphen, or space.
    return re.sub(r'[^\w\-\s]', '_', name)


def now_iso() -> str:
    """Current timestamp in ISO-8601 (seconds precision)."""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def generate_file_name_from_url(url: str) -> str:
    # Parsea URL
    parsed_url = urlparse(url)
    # Delete slash
    path = parsed_url.path.strip('/')
    path_parts = path.split('/')
    last_two_parts = path_parts[-2:] if len(path_parts) >= 2 else path_parts
    base_name = '_'.join(last_two_parts) if last_two_parts else 'index'

    # Replace not allowed characters
    safe_base_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', base_name)
    # Limit the path length
    if len(safe_base_name) > 50:
        safe_base_name = safe_base_name[:50]
    # Hash if neccesary
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:8]
    filename = f"{safe_base_name}_{url_hash}.html"
    return filename


def generate_epub_file_name_from_title(title: str) -> str:
    normalized_title = unicodedata.normalize(
        'NFKD', title).encode('ASCII', 'ignore').decode('ASCII')
    normalized_title = normalized_title.lower()
    normalized_title = re.sub(r'[\s\-]+', '_', normalized_title)
    sanitized_title = re.sub(r'[^a-zA-Z0-9_]', '', normalized_title)
    title_hash = hashlib.md5(sanitized_title.encode('utf-8')).hexdigest()[:8]

    max_length = 50
    if len(sanitized_title) > max_length:
        sanitized_title = sanitized_title[:max_length]
    if not sanitized_title:
        sanitized_title = 'chapter'

    filename = f"{sanitized_title}_{title_hash}.xhtml"
    return filename


def delete_duplicates(str_list: list[str]) -> list[str]:
    return list(dict.fromkeys(str_list))


def obtain_host(url: str):
    host = url.split(':')[1]
    # try:
    #     host = url.split(':')[1]
    # except Exception as e:
    #     pass
    while host.startswith('/'):
        host = host[1:]

    host = host.split('/')[0].replace('www.', '')

    return host


def check_exclusive_params(param1: any, param2: any) -> bool:
    return (param1 is None) != (param2 is None)


def create_volume_id(n: int):
    return f'v{n:02}'


def check_incomplete_url(url: str) -> bool:
    if url.startswith('?') or url.startswith('#'):
        return True

    parsed = urlparse(url)
    return not parsed.scheme or not parsed.netloc
