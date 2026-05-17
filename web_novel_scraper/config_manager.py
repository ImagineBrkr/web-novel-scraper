import os
import json

from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, Any

from .logger_manager import create_logger
from web_novel_scraper.io_helpers.config_io_helper import load_config, get_default_decode_guide_file, get_default_config_file, get_default_base_novel_dirs, LoadConfigError

load_dotenv()
logger = create_logger("CONFIG MANAGER")


# DEFAULT VALUES
SRAPER_CONFIG_FILE = get_default_config_file()
SCRAPER_BASE_NOVELS_DIR = get_default_base_novel_dirs()
SCRAPER_DECODE_GUIDE_FILE = get_default_decode_guide_file()


## ORDER PRIORITY
## 1. PARAMETER TO THE INIT FUNCTION
## 2. ENVIRONMENT VARIABLE
## 3. CONFIG FILE VALUE
## 4. DEFAULT VALUE
class ScraperConfig:
    base_novels_dir: Path
    decode_guide_file: str

    def __init__(self,
                 parameters: dict[str, Any] | None = None):
        if parameters is None:
            parameters = {}

        ## LOADING CONFIGURATION
        config_file = self._get_config(default_value=SRAPER_CONFIG_FILE,
                                       config_file_value=None,
                                       env_variable="SCRAPER_CONFIG_FILE",
                                       parameter_value=parameters.get('config_file'))
        if config_file == SRAPER_CONFIG_FILE:
            logger.debug(f"No Config File path provided, using default Config File path: {SRAPER_CONFIG_FILE}.")

        config = self._load_config(config_file)

        if config:
            logger.info(f"Custom configuration loaded from file {config_file}")

        ## SETTING CONFIGURATION VALUES

        self.base_novels_dir = Path(self._get_config(default_value=SCRAPER_BASE_NOVELS_DIR,
                                                config_file_value=config.get("base_novels_dir"),
                                                env_variable="SCRAPER_BASE_NOVELS_DIR",
                                                parameter_value=parameters.get('base_novels_dir')))

        self.decode_guide_file = ScraperConfig._get_config(default_value=SCRAPER_DECODE_GUIDE_FILE,
                                                  config_file_value=config.get("decode_guide_file"),
                                                  env_variable="SCRAPER_DECODE_GUIDE_FILE",
                                                  parameter_value=parameters.get('decode_guide_file'))

    @staticmethod
    def _get_config(default_value: str,
                    config_file_value: Optional[str],
                    env_variable: str,
                    parameter_value: Optional[str]) -> Optional[str]:
        return (
                parameter_value
                or os.getenv(env_variable)
                or config_file_value
                or default_value
        )

    @staticmethod
    def _load_config(config_file: Path) -> Optional[dict]:
        try:
            config = load_config(config_file)
        except LoadConfigError as e:
            logger.error(f"Error loading config file")
            logger.error(f"LoadConfigError - {e}", exc_info=e)
            config = {}

        return config
