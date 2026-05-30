from typing import Optional
from pathlib import Path

import platformdirs

from web_novel_scraper.io_helpers.utils import IOUtils
from web_novel_scraper.exceptions import (
    LoadConfigError,
    LoadHostConfigError,
    IOUtilsError,
    FileNotFoundCustomError,
    EmptyFileError,
    EmptyConfigFileError,
    ConfigFileNotFoundError,
    HostNotInHostConfigFileError,
)

app_author = "web-novel-scraper"
app_name = "web-novel-scraper"
hosts_config_file = (
    Path(__file__).resolve().parent.parent / "resources/host_config.json"
)


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


def load_hosts_config(host: str) -> dict:
    """Loads configuration from a JSON file at *path*."""

    try:
        hosts_config = IOUtils.read_json_file(path=hosts_config_file, type=dict)

    except EmptyFileError or FileNotFoundCustomError:
        raise LoadHostConfigError(
            f"Could not find Host Config file from {hosts_config_file}."
        )

    except IOUtilsError as e:
        raise LoadHostConfigError(
            f"Could not load Host Config File from {hosts_config_file}: {str(e)}"
        ) from e

    if host not in hosts_config:
        raise HostNotInHostConfigFileError(
            f"Host {host} not found in Host Config File from {hosts_config_file}."
        )

    host_config = hosts_config[host]
    if not isinstance(host_config, dict):
        raise LoadHostConfigError(
            f"Host {host} config in Host Config File from {hosts_config_file} is not a valid."
        )

    return host_config


def get_default_config_file() -> str:
    """Returns the default Config File path."""
    return str(platformdirs.user_config_dir(app_name, app_author)) + "/config.json"


def get_default_decode_guide_file() -> str:
    """Returns the default Decode Guide File path."""
    return str(
        Path(__file__).resolve().parent.parent / "decode_guide/decode_guide.json"
    )


def get_default_hosts_config_file() -> str:
    """Returns the default Decode Guide File path."""
    return


def get_default_base_novel_dirs() -> str:
    """Returns the default base novels directory path."""
    return str(platformdirs.user_data_dir(app_name, app_author))
