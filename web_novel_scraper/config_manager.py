import os

from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, Any, Callable

from web_novel_scraper.logger_manager import create_logger
from web_novel_scraper.io_helpers.config_io_helper import (
    load_config,
    get_default_decode_guide_file,
    get_default_config_file,
    get_default_base_novel_dirs,
)
from web_novel_scraper.exceptions import (
    LoadConfigError,
    EmptyConfigFileError,
    ConfigFileNotFoundError,
    ValidationError,
)


load_dotenv()

# DEFAULT VALUES
SCRAPER_CONFIG_FILE = get_default_config_file()
SCRAPER_BASE_NOVELS_DIR = get_default_base_novel_dirs()
SCRAPER_DECODE_GUIDE_FILE = get_default_decode_guide_file()
DEFAULT_REQUEST_CONFIG = {
    "force_flaresolver": "False",
    "request_retries": "3",
    "request_timeout": "20",
    "request_time_between_retries": "3",
    "request_cookies": None,
}

logger = create_logger(__name__)


## ORDER PRIORITY
## 1. PARAMETER TO THE INIT FUNCTION
## 2. ENVIRONMENT VARIABLE
## 3. CONFIG FILE VALUE
## 4. DEFAULT VALUE
class ScraperConfig:
    base_novels_dir: Path
    decode_guide_file: Path
    force_flaresolver: bool
    request_retries: int
    request_timeout: int
    request_time_between_retries: int

    def __init__(self, parameters: dict[str, Any] | None = None):
        if parameters is None:
            parameters = {}
        ## LOADING CONFIGURATION
        config_file = self._get_config(
            default_value=SCRAPER_CONFIG_FILE,
            config_file_value=None,
            env_variable="SCRAPER_CONFIG_FILE",
            parameter_value=parameters.get("config_file"),
        )

        if config_file == SCRAPER_CONFIG_FILE:
            logger.debug(
                f"No Config File path provided, using default Config File path: {SCRAPER_CONFIG_FILE}."
            )

        logger.debug(f"Trying to load Config File from {config_file}")
        config = self._load_config(config_file)

        if config is None:
            logger.debug("No configuration found on config file.")
            logger.debug(
                "If no other config option was set, the default configuration will be used."
            )
            config = {}

        ## SETTING CONFIGURATION VALUES

        self.base_novels_dir = self._get_config(
            default_value=SCRAPER_BASE_NOVELS_DIR,
            config_file_value=config.get("base_novels_dir"),
            env_variable="SCRAPER_BASE_NOVELS_DIR",
            parameter_value=parameters.get("base_novels_dir"),
            config_type="path",
        )

        self.decode_guide_file = self._get_config(
            default_value=SCRAPER_DECODE_GUIDE_FILE,
            config_file_value=config.get("decode_guide_file"),
            env_variable="SCRAPER_DECODE_GUIDE_FILE",
            parameter_value=parameters.get("decode_guide_file"),
            config_type="path",
        )

        self.force_flaresolver = self._get_config(
            default_value=DEFAULT_REQUEST_CONFIG.get("force_flaresolver"),
            config_file_value=str(config.get("force_flaresolver")),
            env_variable="SCRAPER_FORCE_FLARESOLVER",
            parameter_value=str(parameters.get("force_flaresolver")),
            config_type="bool",
        )

        self.request_retries = self._get_config(
            default_value=DEFAULT_REQUEST_CONFIG.get("request_retries"),
            config_file_value=config.get("request_retries"),
            env_variable="SCRAPER_REQUEST_RETRIES",
            parameter_value=parameters.get("request_retries"),
            config_type="int",
        )

        self.request_timeout = self._get_config(
            default_value=DEFAULT_REQUEST_CONFIG.get("request_timeout"),
            config_file_value=config.get("request_timeout"),
            env_variable="SCRAPER_REQUEST_TIMEOUT",
            parameter_value=parameters.get("request_timeout"),
            config_type="int",
        )

        self.request_time_between_retries = self._get_config(
            default_value=DEFAULT_REQUEST_CONFIG.get("request_time_between_retries"),
            config_file_value=config.get("request_time_between_retries"),
            env_variable="SCRAPER_REQUEST_TIME_BETWEEN_RETRIES",
            parameter_value=parameters.get("request_time_between_retries"),
            config_type="int",
        )

    def get_request_config(self):
        return {
            "force_flaresolver": self.force_flaresolver,
            "request_retries": self.request_retries,
            "request_timeout": self.request_timeout,
            "request_time_between_retries": self.request_time_between_retries,
        }

    @staticmethod
    def _get_config(
        default_value: str,
        config_file_value: Optional[str],
        env_variable: str,
        parameter_value: Optional[str],
        config_type: str = "str",
    ) -> Any:
        config_value = (
            parameter_value
            or os.getenv(env_variable)
            or config_file_value
            or default_value
        )
        type_casts: dict[str, Callable[[str], Any]] = {
            "str": str,
            "int": int,
            "float": float,
            "path": Path,
            "bool": lambda v: v.lower() in ["1", "true", "yes", "on"],
        }

        try:
            caster = type_casts[config_type]
        except KeyError:
            raise ValidationError(f"Invalid configuration Type: {config_type}")

        try:
            return caster(config_value)
        except Exception as e:
            raise ValidationError from e

    @staticmethod
    def _load_config(config_file: Path) -> Optional[dict]:
        try:
            config = load_config(config_file)
            logger.info(f"Custom configuration loaded from file {config_file}")

        except EmptyConfigFileError:
            logger.warning(f"Config File at {config_file} is empty.")
            config = {}

        # Don't trigger a warning since this may be something expected
        except ConfigFileNotFoundError:
            logger.debug(f"Config File not found at {config_file}.")
            config = {}

        except LoadConfigError as e:
            logger.warning(f"Error loading config file from {config_file}.")
            logger.warning(f"LoadConfigError - {e}", exc_info=e)
            config = {}

        return config
