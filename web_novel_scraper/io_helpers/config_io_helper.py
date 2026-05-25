from typing import Optional
from pathlib import Path

import platformdirs

from web_novel_scraper.io_helpers.utils import IOUtils
from web_novel_scraper.exceptions import (
    LoadConfigError,
    IOUtilsError,
    FileNotFoundCustomError,
    EmptyFileError,
    EmptyConfigFileError,
    ConfigFileNotFoundError,
)

app_author = "web-novel-scraper"
app_name = "web-novel-scraper"


def load_config(path: str) -> Optional[dict]:
    """Loads configuration from a JSON file at *path*."""

    try:
        config = IOUtils.read_json_file(path=path, type=dict)

    except EmptyFileError:
        raise EmptyConfigFileError(f"Config File at {path} is empty.")

    except FileNotFoundCustomError:
        raise ConfigFileNotFoundError(f"Config File not found at {path}.")

    except IOUtilsError as e:
        raise LoadConfigError(e) from e

    return config


def get_default_config_file() -> str:
    """Returns the default Config File path."""
    return str(platformdirs.user_config_dir(app_name, app_author)) + "/config.json"


def get_default_decode_guide_file() -> str:
    """Returns the default Decode Guide File path."""
    return str(
        Path(__file__).resolve().parent.parent / "decode_guide/decode_guide.json"
    )


def get_default_base_novel_dirs() -> str:
    """Returns the default base novels directory path."""
    return str(platformdirs.user_data_dir(app_name, app_author))
