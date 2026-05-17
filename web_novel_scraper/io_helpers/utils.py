import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

from web_novel_scraper.logger_manager import create_logger
from web_novel_scraper.utils import ScraperError

# Logger
logger = create_logger("IO HELPERS")

class IOUtilsError(ScraperError):
    """Exception raised for any exception for file operations"""


class FileValidationError(Exception):
    pass


class InvalidPathError(IOUtilsError):
    pass


class FileNotFoundCustomError(IOUtilsError):
    pass


class InvalidFileTypeError(IOUtilsError):
    pass


class OSCustomError(IOUtilsError):
    pass


class JsonParseError(IOUtilsError):
    pass

class InvalidJsonTypeError(IOUtilsError):
    pass

## FILE OPERATIONS HELPER

class IOUtils:
    """Static helper for disc operations."""

    ## HELPERS

    @staticmethod
    def _atomic_tmp(path: Path) -> Path:
        """Temporary file path in the same directory as *path*."""
        return path.with_suffix(path.suffix + ".tmp")

    @staticmethod
    def _normalize_path(path: Path | str) -> Path:
        """
        Converts a string path into a Path object and validates it.
        """

        if not path:
            raise InvalidPathError("Path cannot be empty.")

        try:
            normalized = Path(path)

        except TypeError as e:
            raise InvalidPathError(
                f"Invalid path type: {type(path)}"
            ) from e

        return normalized

    @staticmethod
    def _validate_file_exists(path: Path) -> None:
        """
        Validates that the file exists.
        """

        if not path.exists():
            raise FileNotFoundCustomError(
                f"File does not exist: {path}"
            )

    @staticmethod
    def _validate_is_file(path: Path) -> None:
        """
        Validates that the path is a file.
        """

        if not path.is_file():
            raise InvalidPathError(
                f"Path is not a file: {path}"
            )

    @staticmethod
    def _validate_extension(path: Path, expected_extension: str) -> None:
        """
        Validates file extension.
        """

        if path.suffix.lower() != expected_extension.lower():
            raise InvalidFileTypeError(
                f"Expected '{expected_extension}' file, got '{path.suffix}'"
            )

    @staticmethod
    def _read_text_file_content(path: Path, encoding: str = "utf-8") -> str:
        """
        Reads text content from file.
        """

        try:
            return path.read_text(encoding=encoding)

        except OSError as e:
            raise OSCustomError(
                f"Failed to read file: {path}"
            ) from e

    @staticmethod
    def _validate_json_data_type(json_data: Any, expected_type: type) -> None:
        """
        Validates that json data is of expected type.
        """

        if not isinstance(json_data, expected_type):
            raise InvalidJsonTypeError(
                f"Expected {expected_type.__name__}, got {type(json_data).__name__}"
            )

    @staticmethod
    def _parse_json(content: str, type: type) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Parses JSON content.
        """

        try:
            parsed = json.loads(content)

        except json.JSONDecodeError as e:
            raise JsonParseError(
                f"Invalid JSON format"
            ) from e

        IOUtils._validate_json_data_type(parsed, type)

        return parsed

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
    def read_json_file(
        path: Path | str,
        type: type
    ) -> Optional[dict[str, Any] | list[dict[str, Any]]]:
        """
        Reads and parses a JSON file.
        """

        normalized_path = IOUtils._normalize_path(path)

        IOUtils._validate_extension(normalized_path, ".json")
        IOUtils._validate_file_exists(normalized_path)
        IOUtils._validate_is_file(normalized_path)
        content = IOUtils._read_text_file_content(normalized_path)
        return IOUtils._parse_json(content, type)

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

def _get_element_by_key(json_data, key: str, value: str) -> Optional[dict]:
    for item in json_data:
        if item[key] == value:
            return item
    return None