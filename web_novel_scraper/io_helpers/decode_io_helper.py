from typing import Optional

from web_novel_scraper.logger_manager import create_logger
from web_novel_scraper.io_helpers.utils import IOUtils
from web_novel_scraper.exceptions import (
    LoadDecodeGuideError,
    HostNotInDecodeGuideError,
    IOUtilsError,
    DecodeGuideNotFoundError,
    DecodeGuideIsEmptyError,
    EmptyFileError,
    FileNotFoundCustomError,
    InvalidDecodeGuideError,
)

logger = create_logger(__name__)


def load_decode_guide(path: str, host: str) -> dict:
    """Loads full Decode Guide from a JSON file at *path*. Returns the Decode Guide for the specified *host*."""

    try:
        decode_guide = IOUtils.read_json_file(path=path, type=list)

    except EmptyFileError as e:
        raise DecodeGuideIsEmptyError(f"Decode Guide File '{path}' is empty.") from e

    except FileNotFoundCustomError as e:
        raise DecodeGuideNotFoundError(
            f"Decode Guide File not found at '{path}'."
        ) from e

    except IOUtilsError as e:
        raise LoadDecodeGuideError(
            f"Couldn't load Decode Guide File '{path}': {e}"
        ) from e

    try:
        host_decode_guide = _get_element_by_key(decode_guide, "host", host)
    except KeyError:
        raise InvalidDecodeGuideError(f'Decode Guide File "{path}" is invalid.')
    if host_decode_guide is None:
        raise HostNotInDecodeGuideError(
            f"No Decode Guide found for Host '{host}' in Decode Guide File '{path}'."
        )

    return host_decode_guide


def _get_element_by_key(json_data, key: str, value: str) -> Optional[dict]:
    for item in json_data:
        if item[key] == value:
            return item
    return None
