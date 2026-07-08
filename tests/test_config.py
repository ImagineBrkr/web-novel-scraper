import copy
import pytest
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch
from web_novel_scraper.config import (
    ScraperConfig,
    ENV_MAPPING,
    BoolField,
    CONFIG_SCHEMA,
    DEFAULT_CONFIG_OPTIONS,
    get_active_scraper_config,
    reset_active_scraper_config,
    set_active_scraper_config,
)


from web_novel_scraper.exceptions import (
    ConfigKeyConflictError,
    ConfigNotInitializedError,
    InvalidTypeConfigError,
    ParameterValueFormatError,
    InvalidParameterStructureError,
    ParameterKeyFormatError,
    LoadConfigError,
    ConfigFileNotFoundError,
)


@pytest.fixture
def base_config():
    """Returns a deep copy of DEFAULT_CONFIG_OPTIONS to use as a base in tests."""
    return copy.deepcopy(DEFAULT_CONFIG_OPTIONS)


class TestScraperConfigInit:
    """Tests for ScraperConfig initialization"""

    def test_init_with_no_parameters(self):
        """Test initialization with no parameters"""
        with patch.object(
            ScraperConfig, "_load_config_options_from_file", return_value={}
        ):
            config = ScraperConfig()
            assert config.config_options is not None
            assert "request_config" in config.config_options
            assert "base_novels_dir" in config.config_options

    def test_init_with_parameters(self):
        """Test initialization with parameters"""
        params = [{"request_config.request_timeout": "50"}]
        with patch.object(
            ScraperConfig, "_load_config_options_from_file", return_value={}
        ):
            config = ScraperConfig(parameters=params)
            assert config.config_options["request_config"]["request_timeout"] == 50

    def test_init_priority_parameter_over_env(self):
        """Test that parameters take priority over environment variables"""
        params = [{"request_config.request_timeout": "100"}]
        with patch.dict(os.environ, {"SCRAPER_REQUEST_TIMEOUT": "50"}):
            with patch.object(
                ScraperConfig, "_load_config_options_from_file", return_value={}
            ):
                config = ScraperConfig(parameters=params)
                # Parameters should have priority
                assert config.config_options["request_config"]["request_timeout"] == 100

    def test_init_priority_env_over_file(self):
        """Test that environment variables take priority over config file"""
        file_config = {"request_config": {"request_timeout": "30"}}
        with patch.dict(os.environ, {"SCRAPER_REQUEST_TIMEOUT": "60"}):
            with patch.object(
                ScraperConfig,
                "_load_config_options_from_file",
                return_value=file_config,
            ):
                config = ScraperConfig()
                # Environment variable should have priority
                assert config.config_options["request_config"]["request_timeout"] == 60

    def test_init_priority_file_over_default(self):
        """Test that config file takes priority over default values"""
        file_config = {"request_config": {"request_timeout": "40"}}
        with patch.object(
            ScraperConfig, "_load_config_options_from_file", return_value=file_config
        ):
            config = ScraperConfig()
            assert config.config_options["request_config"]["request_timeout"] == 40


class TestActiveScraperConfig:
    """Tests for module-level active ScraperConfig helpers"""

    def test_get_active_scraper_config_without_initialization_raises(self):
        reset_active_scraper_config()
        with pytest.raises(ConfigNotInitializedError):
            get_active_scraper_config()

    def test_init_sets_active_scraper_config(self):
        with patch.object(
            ScraperConfig, "_load_config_options_from_file", return_value={}
        ):
            config = ScraperConfig()
            assert get_active_scraper_config() is config

    def test_set_active_scraper_config_overrides_current(self):
        with patch.object(
            ScraperConfig, "_load_config_options_from_file", return_value={}
        ):
            config_one = ScraperConfig()
            config_two = ScraperConfig(
                parameters=[{"request_config.request_timeout": 55}]
            )

        set_active_scraper_config(config_one)
        assert get_active_scraper_config() is config_one

        set_active_scraper_config(config_two)
        assert get_active_scraper_config() is config_two


class TestSetHost:
    """Tests for set_host method"""

    def test_set_host_successfully(self):
        """Test setting a host configuration"""
        host_config = {"request_config": {"request_timeout": 15}}
        with patch.object(
            ScraperConfig, "_load_config_options_from_file", return_value={}
        ):
            with patch.object(
                ScraperConfig, "_load_host_config_options", return_value=host_config
            ):
                config = ScraperConfig()
                config.set_host("example.com")
                assert config.config_options["request_config"]["request_timeout"] == 15

    def test_set_host_with_empty_host_config(self):
        """Test setting a host with empty configuration"""
        with patch.object(
            ScraperConfig, "_load_config_options_from_file", return_value={}
        ):
            with patch.object(
                ScraperConfig, "_load_host_config_options", return_value={}
            ):
                config = ScraperConfig()
                original_timeout = config.config_options["request_config"][
                    "request_timeout"
                ]
                config.set_host("example.com")
                # Should keep the default value if host config is empty
                assert (
                    config.config_options["request_config"]["request_timeout"]
                    == original_timeout
                )


class TestGetConfigFilePath:
    """Tests for _get_config_file_path static method"""

    def test_get_config_file_path_with_parameter(self):
        """Test getting config file path from parameter"""
        path = ScraperConfig._get_config_file_path(
            parameter_value="/path/to/config.json"
        )
        assert path == "/path/to/config.json"

    def test_get_config_file_path_with_env_variable(self):
        """Test getting config file path from environment variable"""
        with patch.dict(os.environ, {"SCRAPER_CONFIG_FILE": "/env/config.json"}):
            path = ScraperConfig._get_config_file_path()
            assert path == "/env/config.json"

    def test_get_config_file_path_default(self):
        """Test getting default config file path"""
        with patch.dict(os.environ, {}, clear=True):
            path = ScraperConfig._get_config_file_path()
            # Should return the default path from SCRAPER_CONFIG_FILE constant
            assert isinstance(path, (str, Path))


class TestLoadConfigOptionsFromFile:
    """Tests for _load_config_options_from_file static method"""

    def test_load_config_from_existing_file(self):
        """Test loading config from an existing file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"request_config": {"request_timeout": "25"}}, f)
            f.flush()
            temp_path = f.name

        try:
            with patch("web_novel_scraper.config.load_config") as mock_load:
                mock_load.return_value = {"request_config": {"request_timeout": "25"}}
                config = ScraperConfig._load_config_options_from_file(temp_path)
                assert config == {"request_config": {"request_timeout": "25"}}
        finally:
            os.unlink(temp_path)

    def test_load_config_empty_file(self):
        """Test loading from empty config file"""
        with patch("web_novel_scraper.config.load_config") as mock_load:
            from web_novel_scraper.exceptions import EmptyConfigFileError

            mock_load.side_effect = EmptyConfigFileError("Empty config file")
            config = ScraperConfig._load_config_options_from_file("dummy_path")
            assert config == {}

    def test_load_config_file_not_found(self):
        """Test loading when config file not found"""
        with patch("web_novel_scraper.config.load_config") as mock_load:
            mock_load.side_effect = ConfigFileNotFoundError("File not found")
            config = ScraperConfig._load_config_options_from_file("dummy_path")
            assert config == {}

    def test_load_config_error(self):
        """Test loading when error occurs"""
        with patch("web_novel_scraper.config.load_config") as mock_load:
            mock_load.side_effect = LoadConfigError("Error loading config")
            config = ScraperConfig._load_config_options_from_file("dummy_path")
            assert config == {}


class TestLoadHostConfigOptions:
    """Tests for _load_host_config_options static method"""

    def test_load_host_config_successfully(self):
        """Test loading host config successfully"""
        with patch("web_novel_scraper.config.load_hosts_config") as mock_load:
            mock_load.return_value = {"request_config": {"request_timeout": "12"}}
            config = ScraperConfig._load_host_config_options("example.com")
            assert config == {"request_config": {"request_timeout": "12"}}

    def test_load_host_config_not_found(self):
        """Test loading host config when host not in file"""
        from web_novel_scraper.exceptions import HostNotInHostConfigFileError

        with patch("web_novel_scraper.config.load_hosts_config") as mock_load:
            mock_load.side_effect = HostNotInHostConfigFileError("Host not found")
            config = ScraperConfig._load_host_config_options("unknown.com")
            assert config == {}

    def test_load_host_config_error(self):
        """Test loading host config when error occurs"""
        from web_novel_scraper.exceptions import LoadHostConfigError

        with patch("web_novel_scraper.config.load_hosts_config") as mock_load:
            mock_load.side_effect = LoadHostConfigError("Error loading")
            config = ScraperConfig._load_host_config_options("example.com")
            assert config == {}


class TestParseConfigOptionsFromEnvVariables:
    """Tests for _parse_config_options_from_env_variables static method"""

    def test_parse_env_with_values(self):
        """Test parsing environment variables with values"""
        env_vars = {
            "SCRAPER_REQUEST_TIMEOUT": "50",
            "SCRAPER_REQUEST_RETRIES": "5",
        }
        with patch.dict(os.environ, env_vars):
            config = ScraperConfig._parse_config_options_from_env_variables()
            assert config["request_config"]["request_timeout"] == "50"
            assert config["request_config"]["request_retries"] == "5"

    def test_parse_env_no_values(self):
        """Test parsing environment variables when no custom values set"""
        with patch.dict(os.environ, {}, clear=True):
            config = ScraperConfig._parse_config_options_from_env_variables()
            assert config == {}

    def test_parse_env_partial_values(self):
        """Test parsing environment variables with only some values set"""
        env_vars = {"SCRAPER_REQUEST_TIMEOUT": "75"}
        with patch.dict(os.environ, env_vars, clear=True):
            config = ScraperConfig._parse_config_options_from_env_variables()
            assert "request_config" in config
            assert config["request_config"]["request_timeout"] == "75"


class TestMergeDict:
    """Tests for _merge_dict static method"""

    def test_merge_dict_simple(self):
        """Test merging simple dictionaries"""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = ScraperConfig._merge_dict(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_merge_dict_nested(self):
        """Test merging nested dictionaries"""
        base = {"outer": {"inner": 1, "other": 2}}
        override = {"outer": {"inner": 10}}
        result = ScraperConfig._merge_dict(base, override)
        assert result == {"outer": {"inner": 10, "other": 2}}

    def test_merge_dict_deep_nested(self):
        """Test merging deeply nested dictionaries"""
        base = {"a": {"b": {"c": 1, "d": 2}}}
        override = {"a": {"b": {"c": 100}}}
        result = ScraperConfig._merge_dict(base, override)
        assert result == {"a": {"b": {"c": 100, "d": 2}}}

    def test_merge_dict_empty_base(self):
        """Test merging with empty base dictionary"""
        base = {}
        override = {"a": 1}
        result = ScraperConfig._merge_dict(base, override)
        assert result == {"a": 1}

    def test_merge_dict_empty_override(self):
        """Test merging with empty override dictionary"""
        base = {"a": 1}
        override = {}
        result = ScraperConfig._merge_dict(base, override)
        assert result == {"a": 1}

    def test_merge_dict_dict_to_non_dict(self):
        """Test merging when override changes dict to non-dict"""
        base = {"a": {"b": 1}}
        override = {"a": "string_value"}
        result = ScraperConfig._merge_dict(base, override)
        assert result == {"a": "string_value"}

    def test_merge_dict_non_dict_to_dict(self):
        """Test merging when override changes non-dict to dict"""
        base = {"a": "string_value"}
        override = {"a": {"b": 1}}
        result = ScraperConfig._merge_dict(base, override)
        assert result == {"a": {"b": 1}}


class TestParseConfigOptionsFromParameters:
    """Tests for _parse_config_options_from_parameters static method"""

    def test_parse_parameters_empty_list(self):
        """Test parsing empty parameters list"""
        result = ScraperConfig._parse_config_options_from_parameters([])
        assert result == {}

    def test_parse_parameters_single_option(self):
        """Test parsing single parameter"""
        params = [{"request_config.request_timeout": "55"}]
        result = ScraperConfig._parse_config_options_from_parameters(params)
        assert result["request_config"]["request_timeout"] == "55"

    def test_parse_parameters_multiple_options(self):
        """Test parsing multiple parameters"""
        params = [
            {"request_config.request_timeout": "55"},
            {"request_config.request_retries": "7"},
        ]
        result = ScraperConfig._parse_config_options_from_parameters(params)
        assert result["request_config"]["request_timeout"] == "55"
        assert result["request_config"]["request_retries"] == "7"

    def test_parse_parameters_not_list(self):
        """Test parsing when parameters is not a list"""
        with pytest.raises(InvalidParameterStructureError):
            ScraperConfig._parse_config_options_from_parameters({"key": "value"})

    def test_parse_parameters_not_dict_item(self):
        """Test parsing when list item is not a dict"""
        params = ["not_a_dict"]
        with pytest.raises(InvalidParameterStructureError):
            ScraperConfig._parse_config_options_from_parameters(params)

    def test_parse_parameters_empty_key(self):
        """Test parsing with empty key"""
        params = [{"": "value"}]
        with pytest.raises(ParameterKeyFormatError):
            ScraperConfig._parse_config_options_from_parameters(params)

    def test_parse_parameters_whitespace_key(self):
        """Test parsing with whitespace key"""
        params = [{"   ": "value"}]
        with pytest.raises(ParameterKeyFormatError):
            ScraperConfig._parse_config_options_from_parameters(params)

    def test_parse_parameters_key_starts_with_dot(self):
        """Test parsing with key starting with dot"""
        params = [{".request_config.timeout": "value"}]
        with pytest.raises(ParameterKeyFormatError):
            ScraperConfig._parse_config_options_from_parameters(params)

    def test_parse_parameters_key_ends_with_dot(self):
        """Test parsing with key ending with dot"""
        params = [{"request_config.timeout.": "value"}]
        with pytest.raises(ParameterKeyFormatError):
            ScraperConfig._parse_config_options_from_parameters(params)

    def test_parse_parameters_key_consecutive_dots(self):
        """Test parsing with consecutive dots in key"""
        params = [{"request_config..timeout": "value"}]
        with pytest.raises(ParameterKeyFormatError):
            ScraperConfig._parse_config_options_from_parameters(params)

    def test_parse_parameters_key_with_whitespace(self):
        """Test parsing with whitespace in key"""
        params = [{"request config.timeout": "value"}]
        with pytest.raises(ParameterKeyFormatError):
            ScraperConfig._parse_config_options_from_parameters(params)

    def test_parse_parameters_key_not_string(self):
        """Test parsing with non-string key"""
        params = [{123: "value"}]
        with pytest.raises(ParameterKeyFormatError):
            ScraperConfig._parse_config_options_from_parameters(params)

    def test_parse_parameters_value_dict(self):
        """Test parsing when value is a dict"""
        params = [{"request_config.nested": {"key": "value"}}]
        with pytest.raises(ParameterValueFormatError):
            ScraperConfig._parse_config_options_from_parameters(params)

    def test_parse_parameters_value_list(self):
        """Test parsing when value is a list"""
        params = [{"request_config.items": [1, 2, 3]}]
        with pytest.raises(ParameterValueFormatError):
            ScraperConfig._parse_config_options_from_parameters(params)

    def test_parse_parameters_valid_string_value(self):
        """Test parsing with valid string value"""
        params = [{"key": "string_value"}]
        result = ScraperConfig._parse_config_options_from_parameters(params)
        assert result["key"] == "string_value"

    def test_parse_parameters_valid_numeric_value(self):
        """Test parsing with numeric value"""
        params = [{"key": "123"}]
        result = ScraperConfig._parse_config_options_from_parameters(params)
        assert result["key"] == "123"

    def test_parse_parameters_valid_boolean_value(self):
        """Test parsing with boolean value"""
        params = [{"key": True}]
        result = ScraperConfig._parse_config_options_from_parameters(params)
        assert result["key"] is True


class TestParseConfigOptionFromAbbreviation:
    """Tests for _parse_config_option_from_abbreviation static method"""

    def test_parse_single_level_key(self):
        """Test parsing single level key"""
        config = {}
        ScraperConfig._parse_config_option_from_abbreviation(config, "key", "value")
        assert config == {"key": "value"}

    def test_parse_two_level_key(self):
        """Test parsing two level key"""
        config = {}
        ScraperConfig._parse_config_option_from_abbreviation(
            config, "request_config.timeout", "50"
        )
        assert config == {"request_config": {"timeout": "50"}}

    def test_parse_three_level_key(self):
        """Test parsing three level key"""
        config = {}
        ScraperConfig._parse_config_option_from_abbreviation(config, "a.b.c", "value")
        assert config == {"a": {"b": {"c": "value"}}}

    def test_parse_overwrite_existing_value(self):
        """Test overwriting existing value"""
        config = {"key": "old_value"}
        ScraperConfig._parse_config_option_from_abbreviation(config, "key", "new_value")
        assert config == {"key": "new_value"}

    def test_parse_conflict_dict_to_value(self):
        """Test conflict when trying to set value where dict exists"""
        config = {"request_config": {"timeout": "50"}}
        with pytest.raises(ConfigKeyConflictError):
            ScraperConfig._parse_config_option_from_abbreviation(
                config, "request_config", "value"
            )

    def test_parse_conflict_value_to_dict(self):
        """Test conflict when trying to set dict where value exists"""
        config = {"key": "value"}
        with pytest.raises(ConfigKeyConflictError):
            ScraperConfig._parse_config_option_from_abbreviation(
                config, "key.nested", "value"
            )

    def test_parse_merge_nested_keys(self):
        """Test merging when adding new nested key"""
        config = {"request_config": {"timeout": "50"}}
        ScraperConfig._parse_config_option_from_abbreviation(
            config, "request_config.retries", "3"
        )
        assert config == {"request_config": {"timeout": "50", "retries": "3"}}

    def test_parse_duplicate_warning(self):
        """Test duplicate key in same configuration"""
        config = {}
        ScraperConfig._parse_config_option_from_abbreviation(config, "key", "value1")
        # Should warn but use new value
        ScraperConfig._parse_config_option_from_abbreviation(config, "key", "value2")
        assert config == {"key": "value2"}


class TestValidateConfig:
    """Tests for _validate_config static method"""

    def test_validate_config_valid(self, base_config):
        """Test validating valid configuration"""
        # Should not raise
        ScraperConfig._validate_config(base_config)

    def test_validate_config_string_values(self, base_config):
        """Test that string values are converted correctly"""
        base_config["base_novels_dir"] = Path("/path")
        base_config["decode_guide_file"] = Path("/guide.json")
        config = ScraperConfig._validate_config(base_config)
        assert isinstance(config["base_novels_dir"], str)
        assert isinstance(config["decode_guide_file"], str)

    def test_validate_config_invalid_timeout(self, base_config):
        """Test validation with invalid timeout value"""
        base_config["request_config"]["request_timeout"] = "invalid"
        with pytest.raises(InvalidTypeConfigError):
            ScraperConfig._validate_config(base_config)

    def test_validate_config_invalid_retries(self, base_config):
        """Test validation with invalid retries value"""
        base_config["request_config"]["request_retries"] = "invalid"
        with pytest.raises(InvalidTypeConfigError):
            ScraperConfig._validate_config(base_config)

    def test_validate_config_bool_conversion(self, base_config):
        """Test boolean conversion in validation"""
        base_config["request_config"]["force_flaresolver"] = 0
        config = ScraperConfig._validate_config(base_config)
        assert isinstance(config["request_config"]["force_flaresolver"], bool)

    def test_validate_config_numeric_string_values(self, base_config):
        """Test validation with numeric strings that can be converted"""
        base_config["request_config"]["request_timeout"] = "20"
        base_config["request_config"]["request_retries"] = "3"
        config = ScraperConfig._validate_config(base_config)
        assert config["request_config"]["request_timeout"] == 20
        assert config["request_config"]["request_retries"] == 3


class TestConfigIntegration:
    """Integration tests for ScraperConfig"""

    def test_full_initialization_workflow(self):
        """Test complete initialization workflow"""
        with patch.object(
            ScraperConfig, "_load_config_options_from_file", return_value={}
        ):
            config = ScraperConfig(
                parameters=[
                    {"request_config.request_timeout": "100"},
                    {"request_config.force_flaresolver": "true"},
                ]
            )
            assert config.config_options["request_config"]["request_timeout"] == 100

    def test_config_file_with_host_override(self):
        """Test config file values with host override"""
        file_config = {"request_config": {"request_timeout": 40}}
        host_config = {"request_config": {"request_timeout": 15}}

        with patch.object(
            ScraperConfig, "_load_config_options_from_file", return_value=file_config
        ):
            with patch.object(
                ScraperConfig, "_load_host_config_options", return_value=host_config
            ):
                config = ScraperConfig()
                config.set_host("example.com")
                assert config.config_options["request_config"]["request_timeout"] == 40

    def test_env_variables_mapping(self):
        """Test all ENV_MAPPING keys are properly handled"""
        env_vars = {k: "test_value" for k in ENV_MAPPING.keys()}

        with patch.dict(os.environ, env_vars):
            config = ScraperConfig._parse_config_options_from_env_variables()
            # Check that at least one mapping worked
            assert len(config) > 0


class TestBoolField:
    """Tests for BoolField.parse static method"""

    def test_parse_bool_true(self):
        """Test parsing boolean True"""
        result = BoolField.parse(True)
        assert result is True

    def test_parse_bool_false(self):
        """Test parsing boolean False"""
        result = BoolField.parse(False)
        assert result is False

    def test_parse_string_true_lowercase(self):
        """Test parsing string 'true'"""
        result = BoolField.parse("true")
        assert result is True

    def test_parse_string_true_uppercase(self):
        """Test parsing string 'TRUE'"""
        result = BoolField.parse("TRUE")
        assert result is True

    def test_parse_string_true_mixed_case(self):
        """Test parsing string 'TrUe'"""
        result = BoolField.parse("TrUe")
        assert result is True

    def test_parse_string_false_lowercase(self):
        """Test parsing string 'false'"""
        result = BoolField.parse("false")
        assert result is False

    def test_parse_string_false_uppercase(self):
        """Test parsing string 'FALSE'"""
        result = BoolField.parse("FALSE")
        assert result is False

    def test_parse_string_yes(self):
        """Test parsing string 'yes'"""
        result = BoolField.parse("yes")
        assert result is True

    def test_parse_string_yes_uppercase(self):
        """Test parsing string 'YES'"""
        result = BoolField.parse("YES")
        assert result is True

    def test_parse_string_no(self):
        """Test parsing string 'no'"""
        result = BoolField.parse("no")
        assert result is False

    def test_parse_string_no_uppercase(self):
        """Test parsing string 'NO'"""
        result = BoolField.parse("NO")
        assert result is False

    def test_parse_string_1(self):
        """Test parsing string '1'"""
        result = BoolField.parse("1")
        assert result is True

    def test_parse_string_0(self):
        """Test parsing string '0'"""
        result = BoolField.parse("0")
        assert result is False

    def test_parse_int_1(self):
        """Test parsing integer 1"""
        result = BoolField.parse(1)
        assert result is True

    def test_parse_int_0(self):
        """Test parsing integer 0"""
        result = BoolField.parse(0)
        assert result is False

    def test_parse_float_1_0(self):
        """Test parsing float 1.0"""
        result = BoolField.parse(1.0)
        assert result is True

    def test_parse_float_0_0(self):
        """Test parsing float 0.0"""
        result = BoolField.parse(0.0)
        assert result is False

    def test_parse_invalid_string(self):
        """Test parsing invalid string"""
        with pytest.raises(ValueError):
            BoolField.parse("maybe")

    def test_parse_invalid_int(self):
        """Test parsing invalid integer"""
        with pytest.raises(ValueError):
            BoolField.parse(2)

    def test_parse_invalid_float(self):
        """Test parsing invalid float"""
        with pytest.raises(ValueError):
            BoolField.parse(2.5)

    def test_parse_none(self):
        """Test parsing None"""
        with pytest.raises(ValueError):
            BoolField.parse(None)

    def test_parse_empty_string(self):
        """Test parsing empty string"""
        with pytest.raises(ValueError):
            BoolField.parse("")

    def test_parse_list(self):
        """Test parsing list"""
        with pytest.raises((ValueError, TypeError)):
            BoolField.parse([True])

    def test_parse_dict(self):
        """Test parsing dict"""
        with pytest.raises((ValueError, TypeError)):
            BoolField.parse({"value": True})


class TestValidateConfigWithSchema:
    """Tests for _validate_config with new schema and request_cookies"""

    def test_validate_config_with_schema(self, base_config):
        """Test validating config with CONFIG_SCHEMA"""
        result = ScraperConfig._validate_config(base_config, CONFIG_SCHEMA)
        assert isinstance(result, dict)
        assert result["request_config"]["request_cookies"] == {}

    def test_validate_config_request_cookies_dict(self, base_config):
        """Test that request_cookies is validated as dict"""
        base_config["request_config"]["request_cookies"] = {
            "cookie1": "value1",
            "cookie2": "value2",
        }
        result = ScraperConfig._validate_config(base_config, CONFIG_SCHEMA)
        assert result["request_config"]["request_cookies"] == {
            "cookie1": "value1",
            "cookie2": "value2",
        }

    def test_validate_config_request_cookies_invalid_type(self, base_config):
        """Test that invalid request_cookies type raises error"""
        base_config["request_config"]["request_cookies"] = "not_a_dict"
        with pytest.raises(InvalidTypeConfigError):
            ScraperConfig._validate_config(base_config, CONFIG_SCHEMA)

    def test_validate_config_bool_field_true_string(self, base_config):
        """Test BoolField validation with string 'true'"""
        base_config["request_config"]["force_flaresolver"] = "true"
        result = ScraperConfig._validate_config(base_config, CONFIG_SCHEMA)
        assert result["request_config"]["force_flaresolver"] is True

    def test_validate_config_bool_field_false_string(self, base_config):
        """Test BoolField validation with string 'false'"""
        base_config["request_config"]["force_flaresolver"] = "false"
        result = ScraperConfig._validate_config(base_config, CONFIG_SCHEMA)
        assert result["request_config"]["force_flaresolver"] is False

    def test_validate_config_bool_field_int_1(self, base_config):
        """Test BoolField validation with integer 1"""
        base_config["request_config"]["force_flaresolver"] = 1
        result = ScraperConfig._validate_config(base_config, CONFIG_SCHEMA)
        assert result["request_config"]["force_flaresolver"] is True

    def test_validate_config_bool_field_int_0(self, base_config):
        """Test BoolField validation with integer 0"""
        base_config["request_config"]["force_flaresolver"] = 0
        result = ScraperConfig._validate_config(base_config, CONFIG_SCHEMA)
        assert result["request_config"]["force_flaresolver"] is False

    def test_validate_config_bool_field_invalid(self, base_config):
        """Test BoolField validation with invalid value"""
        base_config["request_config"]["force_flaresolver"] = "invalid_bool"
        with pytest.raises(InvalidTypeConfigError):
            ScraperConfig._validate_config(base_config, CONFIG_SCHEMA)

    def test_validate_config_type_conversion_string_to_int(self, base_config):
        """Test that numeric strings are converted to int"""
        base_config["request_config"]["request_timeout"] = "30"
        base_config["request_config"]["request_retries"] = "5"
        base_config["request_config"]["request_time_between_retries"] = "2"
        result = ScraperConfig._validate_config(base_config, CONFIG_SCHEMA)
        assert result["request_config"]["request_timeout"] == 30
        assert result["request_config"]["request_retries"] == 5
        assert result["request_config"]["request_time_between_retries"] == 2

    def test_validate_config_nested_schema(self, base_config):
        """Test validation of nested schema structure"""
        base_config["request_config"]["force_flaresolver"] = True
        base_config["request_config"]["request_timeout"] = 25
        base_config["request_config"]["request_retries"] = 4
        base_config["request_config"]["request_cookies"] = {"session": "abc123"}
        result = ScraperConfig._validate_config(base_config, CONFIG_SCHEMA)
        assert isinstance(result, dict)
        assert "request_config" in result
        assert isinstance(result["request_config"], dict)

    def test_validate_config_invalid_dict_type(self, base_config):
        """Test that non-dict value for dict type raises error"""
        base_config["request_config"]["request_cookies"] = "not_a_dict"
        with pytest.raises(InvalidTypeConfigError):
            ScraperConfig._validate_config(base_config, CONFIG_SCHEMA)

    def test_validate_config_invalid_dict_type_list(self, base_config):
        """Test that list value for dict type raises error"""
        base_config["request_config"]["request_cookies"] = [1, 2, 3]
        with pytest.raises(InvalidTypeConfigError):
            ScraperConfig._validate_config(base_config, CONFIG_SCHEMA)
