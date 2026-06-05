import os

from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, Any

from web_novel_scraper.logger_manager import create_logger
from web_novel_scraper.io_helpers.config_io_helper import (
    load_config,
    get_default_decode_guide_file,
    get_default_config_file,
    get_default_base_novel_dirs,
    load_hosts_config,
)
from web_novel_scraper.exceptions import (
    ConfigKeyConflictError,
    InvalidTypeConfigError,
    LoadConfigError,
    LoadHostConfigError,
    HostNotInHostConfigFileError,
    EmptyConfigFileError,
    ConfigFileNotFoundError,
    ParameterValueFormatError,
    InvalidParameterStructureError,
    ParameterKeyConflictError,
    ParameterKeyFormatError,
)


load_dotenv()


class BoolField:
    @staticmethod
    def parse(value):
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            if value.lower() in {"true", "1", "yes"}:
                return True
            if value.lower() in {"false", "0", "no"}:
                return False

        if isinstance(value, (int, float)):
            if value == 1:
                return True
            if value == 0:
                return False

        raise ValueError(f"'{value}' is not a valid bool")


CONFIG_SCHEMA = {
    "base_novels_dir": str,
    "decode_guide_file": str,
    "request_config": {
        "force_flaresolver": BoolField,
        "request_timeout": int,
        "request_retries": int,
        "request_time_between_retries": int,
        "request_cookies": dict,
    },
}

# DEFAULT VALUES
DEFAULT_CONFIG_OPTIONS = {
    "base_novels_dir": get_default_base_novel_dirs(),
    "decode_guide_file": get_default_decode_guide_file(),
    "request_config": {
        "force_flaresolver": False,
        "request_retries": 3,
        "request_timeout": 20,
        "request_time_between_retries": 3,
        "request_cookies": {},
    },
}
SCRAPER_CONFIG_FILE = get_default_config_file()

# ENV PARAMETERS
ENV_MAPPING = {
    "SCRAPER_BASE_NOVELS_DIR": "base_novels_dir",
    "SCRAPER_DECODE_GUIDE_FILE": "decode_guide_file",
    "SCRAPER_FORCE_FLARESOLVER": "request_config.force_flaresolver",
    "SCRAPER_REQUEST_TIMEOUT": "request_config.request_timeout",
    "SCRAPER_REQUEST_RETRIES": "request_config.request_retries",
    "SCRAPER_REQUEST_TIME_BETWEEN_RETRIES": "request_config.request_time_between_retries",
}

logger = create_logger(__name__)


## ORDER PRIORITY
## 1. PARAMETER TO THE INIT FUNCTION
## 2. ENVIRONMENT VARIABLE
## 3. CONFIG FILE VALUE
## 4. DEFAULT VALUE
class ScraperConfig:
    config_options: dict
    _config_file_config_options: dict
    _parameters_config_options: dict
    _env_variables_config_options: dict

    def __init__(self, parameters: list[dict] = []) -> None:
        self._env_variables_config_options = (
            ScraperConfig._parse_config_options_from_env_variables()
        )
        self._parameters_config_options = (
            ScraperConfig._parse_config_options_from_parameters(parameters)
        )

        ## LOADING CONFIG FILE

        config_file = self._get_config_file_path(
            parameter_value=self._parameters_config_options.get("config_file")
        )

        self._config_file_config_options = self._load_config_options_from_file(
            config_file
        )

        ## SETTING CONFIGURATION VALUES

        config = DEFAULT_CONFIG_OPTIONS

        config = ScraperConfig._merge_dict(config, self._config_file_config_options)

        config = ScraperConfig._merge_dict(config, self._env_variables_config_options)

        config = ScraperConfig._merge_dict(config, self._parameters_config_options)

        config = ScraperConfig._validate_config(config)

        self.config_options = config

    # Config specific Host in host_config.json File counts as the Default
    # Configuration passed by the user still takes priority
    def set_host(self, host: str) -> None:
        host_config = self._load_host_config_options(host)
        self.config_options = ScraperConfig._merge_dict(
            DEFAULT_CONFIG_OPTIONS, host_config
        )
        self.config_options = ScraperConfig._merge_dict(
            self.config_options, self._config_file_config_options
        )
        self.config_options = ScraperConfig._merge_dict(
            self.config_options, self._env_variables_config_options
        )
        self.config_options = ScraperConfig._merge_dict(
            self.config_options, self._parameters_config_options
        )
        self.config_options = ScraperConfig._validate_config(self.config_options)

    @staticmethod
    def _get_config_file_path(parameter_value: str | None = None) -> str:
        if parameter_value is not None:
            logger.debug(
                f"Using Config File Location {parameter_value} passed as a parameter"
            )
            return parameter_value

        env_variable_value = os.getenv("SCRAPER_CONFIG_FILE")
        if env_variable_value is not None:
            logger.debug(
                f'Using Config FIle Location {env_variable_value} passed as an Environment Variable "SCRAPER_CONFIG_FILE"'
            )
            return env_variable_value

        logger.debug(f"Using default Config File Location {SCRAPER_CONFIG_FILE}")
        return SCRAPER_CONFIG_FILE

    @staticmethod
    def _load_config_options_from_file(config_file: Path) -> Optional[dict]:
        logger.debug(f"Trying to load Config File from {config_file}")
        try:
            config = load_config(config_file)
            logger.info(f"Custom Configuration Options loaded from file {config_file}")

        except EmptyConfigFileError:
            logger.warning(f"Config File at {config_file} is empty.")
            config = {}

        # Don't trigger a warning since this may be something expected
        except ConfigFileNotFoundError:
            logger.debug(f"Config File not found at {config_file}.")
            config = {}

        except LoadConfigError as e:
            logger.warning(f"Error loading Config File from {config_file}: {str(e)}.")
            config = {}

        return config

    @staticmethod
    def _load_host_config_options(host: str) -> dict:
        try:
            host_config = load_hosts_config(host)
            logger.debug(f"Host Config for host {host} loaded from Host Config File.")
        except HostNotInHostConfigFileError:
            logger.debug(
                f"Host {host} does not have a specific configuration in Host Config File."
            )
            host_config = {}
        except LoadHostConfigError as e:
            logger.warning(f"Error loading Host Config for host {host}: {str(e)}.")
            host_config = {}
        return host_config

    @staticmethod
    def _parse_config_options_from_env_variables() -> dict:
        env_vars_with_values = []
        result = {}

        for env_var, path in ENV_MAPPING.items():
            value = os.getenv(env_var)

            if value is None:
                continue

            env_vars_with_values.append({env_var: value})

            ScraperConfig._parse_config_option_from_abbreviation(
                config=result, key=path, value=value
            )

        if len(env_vars_with_values) == 0:
            logger.debug("No Configuration Options set from Environment Variables.")
        else:
            logger.debug(
                f"Configuration options from Environments Variables: {env_vars_with_values}"
            )
        return result

    @staticmethod
    def _merge_dict(base: dict, override: dict) -> dict:
        result = base.copy()

        for key, value in override.items():
            if (
                isinstance(value, dict)
                and key in result
                and isinstance(result[key], dict)
            ):
                result[key] = ScraperConfig._merge_dict(result[key], value)
            else:
                result[key] = value

        return result

    # Parses [{'request_config.request_timeout': '50'}] -> {'request_config': {'request_timeout': '50'}}
    @staticmethod
    def _parse_config_options_from_parameters(params_list: list[dict]) -> dict:

        def _validate_parameter_key(parameter_key: str) -> None:
            # Validate parameter_key format
            if not isinstance(parameter_key, str):
                raise ParameterKeyFormatError(
                    f"Config Parameter '{parameter_key}' is not a string, got {type(parameter_key).__name__}"
                )

            if not parameter_key or parameter_key.isspace():
                raise ParameterKeyFormatError(
                    f"Config Parameter {parameter_key} is empty or whitespace."
                )

            if parameter_key.startswith(".") or parameter_key.endswith("."):
                raise ParameterKeyFormatError(
                    f"Config Parameter '{parameter_key}' cannot start or end with a dot"
                )

            if ".." in parameter_key:
                raise ParameterKeyFormatError(
                    f"Config Parameter '{parameter_key}' contains consecutive dots"
                )

            if " " in parameter_key:
                raise ParameterKeyFormatError(
                    f"Config Parameter '{parameter_key}' contains whitespace."
                )

        def _validate_parameter_value(parameter_value: Any) -> None:
            if isinstance(value, (dict, list)):
                raise ParameterValueFormatError(
                    f'Config Paramater Value "{parameter_value}" can not be a dict or a list.'
                )

        # Validate input structure
        if not isinstance(params_list, list):
            raise InvalidParameterStructureError(
                f"Expected list of dictionaries, got {type(params_list).__name__}"
            )

        result = {}

        if len(params_list) == 0:
            logger.debug("No Configuration Options set from Parameters.")
            return result

        for param_dict in params_list:
            if not isinstance(param_dict, dict):
                raise InvalidParameterStructureError(
                    f"Item '{param_dict}' is not a dictionary, got {type(param_dict).__name__}"
                )

            for key, value in param_dict.items():
                _validate_parameter_key(parameter_key=key)
                _validate_parameter_value(parameter_value=value)
                try:
                    ScraperConfig._parse_config_option_from_abbreviation(
                        result, key, value
                    )
                except ConfigKeyConflictError as e:
                    raise ParameterKeyConflictError(e) from e

        logger.debug(f"Configuration Options Set from Parameters: {params_list}")
        return result

    @staticmethod
    def _parse_config_option_from_abbreviation(
        config: dict, key: str, value: Any
    ) -> dict:
        current = config
        splitted_keys = key.split(".")

        # Navigate and build the nested structure
        for i, splitted_key in enumerate(splitted_keys[:-1]):
            if splitted_key not in current:
                current[splitted_key] = {}

            elif not isinstance(current[splitted_key], dict):
                raise ConfigKeyConflictError(
                    f'Cannot set "{key}": "{".".join(splitted_keys[: i + 1])}" is already set to a non-dict value: {current[splitted_key]}'
                )

            current = current[splitted_key]

        # Set the final value
        final_key = splitted_keys[-1]
        if final_key in current and isinstance(current[final_key], dict):
            raise ConfigKeyConflictError(
                f'Cannot set "{key}": "{key}" is set to a dict value: {current[final_key]}'
            )
        elif final_key in current:
            logger.warning(
                f'Config Option "{key}" seems to be duplicated, Final Value "{value}" will be used.'
            )

        current[final_key] = value
        return config

    @staticmethod
    def _validate_config(config_options: dict, schema: dict = CONFIG_SCHEMA) -> dict:
        result = {}

        for key, expected_type in schema.items():
            value = config_options[key]

            # If the expected type is dict, check the value is a dict
            if expected_type is dict:
                if isinstance(value, dict):
                    result[key] = value
                    continue
                else:
                    raise InvalidTypeConfigError(
                        f"Invalid type for Config Option '{key}', expected 'dict', got a '{type(value).__name__}': '{value}'"
                    )

            # If the expected type is NOT a dict, fail if it is expecting another type
            if isinstance(value, dict):
                if isinstance(expected_type, dict):
                    result[key] = ScraperConfig._validate_config(value, expected_type)
                    continue
                else:
                    raise InvalidTypeConfigError(
                        f"Invalid type for Config Option '{key}', expected '{type(expected_type).__name__}', got a dict '{value}'"
                    )
            if expected_type is BoolField:
                try:
                    result[key] = BoolField.parse(value)
                except (ValueError, TypeError) as e:
                    raise InvalidTypeConfigError(
                        f"Invalid type for Config Option '{key}', expected '{expected_type.__name__}': {e}"
                    ) from e
                continue

            try:
                result[key] = expected_type(value)
            except (ValueError, TypeError) as e:
                raise InvalidTypeConfigError(
                    f"Invalid type for Config Option '{key}', expected '{expected_type.__name__}': {e}"
                ) from e

        return result
