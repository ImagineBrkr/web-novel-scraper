import os
import json

import platformdirs
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, Any

from .logger_manager import create_logger
from .utils import FileOps, ValidationError

load_dotenv()

CURRENT_DIR = Path(__file__).resolve().parent

app_author = "web-novel-scraper"
app_name = "web-novel-scraper"

# DEFAULT VALUES
SCRAPER_CONFIG_FILE = str(Path(platformdirs.user_config_dir(app_name, app_author)) / "config.json")
SCRAPER_BASE_NOVELS_DIR = platformdirs.user_data_dir(app_name, app_author)
SCRAPER_DECODE_GUIDE_FILE = str(CURRENT_DIR / 'decode_guide/decode_guide.json')

logger = create_logger("CONFIG MANAGER")


## ORDER PRIORITY
## 1. PARAMETER TO THE INIT FUNCTION
## 2. ENVIRONMENT VARIABLE
## 3. CONFIG FILE VALUE
## 4. DEFAULT VALUE
class ScraperConfig:
    base_novels_dir: Path
    decode_guide_file: Path

    def __init__(self,
                 parameters: dict[str, Any] | None = None):
        if parameters is None:
            parameters = {}
        ## LOADING CONFIGURATION
        config_file = self._get_config(default_value=SCRAPER_CONFIG_FILE,
                                       config_file_value=None,
                                       env_variable="SCRAPER_CONFIG_FILE",
                                       parameter_value=parameters.get('config_file'))

        config_file = Path(config_file)
        logger.debug(f'Obtaining configuration from file "{config_file}"')
        config = self._load_config(config_file)

        if config is None:
            logger.debug('No configuration found on config file.')
            logger.debug('If no other config option was set, the default configuration will be used.')
            config = {}

        ## SETTING CONFIGURATION VALUES

        self.base_novels_dir = Path(self._get_config(default_value=SCRAPER_BASE_NOVELS_DIR,
                                                config_file_value=config.get("base_novels_dir"),
                                                env_variable="SCRAPER_BASE_NOVELS_DIR",
                                                parameter_value=parameters.get('base_novels_dir')))

        self.decode_guide_file = Path(self._get_config(default_value=SCRAPER_DECODE_GUIDE_FILE,
                                                  config_file_value=config.get("decode_guide_file"),
                                                  env_variable="SCRAPER_DECODE_GUIDE_FILE",
                                                  parameter_value=parameters.get('decode_guide_file')))

    @staticmethod
    def _get_config(default_value: str,
                    config_file_value: Optional[str],
                    env_variable: str,
                    parameter_value: Optional[str]) -> str:
        return (
                parameter_value
                or os.getenv(env_variable)
                or config_file_value
                or default_value
        )

    @staticmethod
    def _load_config(config_file: Path) -> Optional[dict]:
        config = FileOps.read_json(config_file)
        if config is None:
            logger.debug(f'Could not load configuration from file "{config_file}". Skipping...')
        return config
