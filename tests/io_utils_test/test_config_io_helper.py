# tests/io_utils_test/test_config_io_helper.py

import json
from pathlib import Path

import pytest

from web_novel_scraper.io_helpers.config_io_helper import (
    load_config,
    get_default_config_file,
    get_default_decode_guide_file,
    get_default_base_novel_dirs,
)
from web_novel_scraper.exceptions import (
    LoadConfigError,
    ConfigFileNotFoundError,
    EmptyConfigFileError,
)


# ============================================================================
# Fixtures
# ============================================================================


def create_config_file(path: Path, content: str = ""):
    """Helper to create a config file with content."""
    path.write_text(content, encoding="utf-8")
    return path


# ============================================================================
# load_config tests
# ============================================================================


class TestLoadConfig:
    """Tests for load_config() function."""

    def test_load_valid_config_dict(self, tmp_path):
        """Test loading valid config file with dict."""
        config_file = tmp_path / "config.json"
        data = {"name": "test", "enabled": True, "value": 123}
        config_file.write_text(json.dumps(data))

        result = load_config(str(config_file))

        assert result == data

    def test_load_config_with_nested_structure(self, tmp_path):
        """Test loading config with nested dictionary."""
        config_file = tmp_path / "config.json"
        data = {
            "app": {"name": "test", "version": "1.0"},
            "settings": {"debug": True, "timeout": 30},
        }
        config_file.write_text(json.dumps(data))

        result = load_config(str(config_file))

        assert result == data

    def test_load_config_nonexistent_file_raises_error(self, tmp_path):
        """Test loading nonexistent config file raises ConfigFileNotFoundError."""
        path = tmp_path / "missing.json"

        with pytest.raises(ConfigFileNotFoundError):
            load_config(str(path))

    def test_load_empty_config_file_raises_error(self, tmp_path):
        """Test loading empty config file raises EmptyConfigFileError."""
        config_file = create_config_file(tmp_path / "config.json", "{}")

        with pytest.raises(EmptyConfigFileError):
            load_config(str(config_file))

    def test_load_config_directory_path_raises_error(self, tmp_path):
        """Test loading from directory path raises error."""
        directory = tmp_path / "folder"
        directory.mkdir()

        with pytest.raises(LoadConfigError):
            load_config(str(directory))

    def test_load_invalid_json_syntax_raises_error(self, tmp_path):
        """Test loading invalid JSON syntax raises error."""
        config_file = create_config_file(tmp_path / "config.json", '{"invalid": }')

        with pytest.raises(LoadConfigError):
            load_config(str(config_file))

    def test_load_json_number_instead_of_dict_raises_error(self, tmp_path):
        """Test JSON number type raises error."""
        config_file = create_config_file(tmp_path / "config.json", "123")

        with pytest.raises(LoadConfigError):
            load_config(str(config_file))

    def test_load_json_list_instead_of_dict_raises_error(self, tmp_path):
        """Test JSON list instead of dict raises error."""
        config_file = create_config_file(tmp_path / "config.json", '[{"key": "value"}]')

        with pytest.raises(LoadConfigError):
            load_config(str(config_file))

    def test_load_json_null_raises_error(self, tmp_path):
        """Test JSON null value raises error."""
        config_file = create_config_file(tmp_path / "config.json", "null")

        with pytest.raises(LoadConfigError):
            load_config(str(config_file))

    def test_load_json_string_instead_of_dict_raises_error(self, tmp_path):
        """Test JSON string instead of dict raises error."""
        config_file = create_config_file(tmp_path / "config.json", '"string value"')

        with pytest.raises(LoadConfigError):
            load_config(str(config_file))

    def test_load_config_wrong_extension_raises_error(self, tmp_path):
        """Test loading file with wrong extension raises error."""
        config_file = create_config_file(tmp_path / "config.txt", '{"test": 123}')

        with pytest.raises(LoadConfigError):
            load_config(str(config_file))

    def test_load_empty_json_object_raises_error(self, tmp_path):
        """Test loading empty JSON object raises error."""
        config_file = create_config_file(tmp_path / "config.json", "{}")

        with pytest.raises(EmptyConfigFileError):
            load_config(str(config_file))

    def test_load_config_with_special_characters(self, tmp_path):
        """Test loading config with special characters."""
        config_file = tmp_path / "config.json"
        data = {"app_name": "Scraper™", "description": "Español: áéíóú, 中文, 😀"}
        config_file.write_text(json.dumps(data, ensure_ascii=True))

        result = load_config(str(config_file))

        assert result == data

    def test_load_config_with_unicode(self, tmp_path):
        """Test loading config with unicode characters."""
        config_file = tmp_path / "config.json"
        data = {"title": "网络小说下载器", "author": "作者"}
        config_file.write_text(json.dumps(data, ensure_ascii=True))

        result = load_config(str(config_file))

        assert result == data

    def test_load_config_corrupted_json_raises_error(self, tmp_path):
        """Test loading corrupted JSON raises error."""
        config_file = create_config_file(
            tmp_path / "config.json",
            '{"test": "value"',  # Missing closing brace
        )

        with pytest.raises(LoadConfigError):
            load_config(str(config_file))

    def test_load_config_with_boolean_values(self, tmp_path):
        """Test loading config with boolean values."""
        config_file = tmp_path / "config.json"
        data = {"enabled": True, "debug": False, "verbose": True}
        config_file.write_text(json.dumps(data))

        result = load_config(str(config_file))

        assert result == data

    def test_load_config_with_numeric_values(self, tmp_path):
        """Test loading config with numeric values."""
        config_file = tmp_path / "config.json"
        data = {"timeout": 30, "retries": 5, "version": 1.5}
        config_file.write_text(json.dumps(data))

        result = load_config(str(config_file))

        assert result == data

    def test_load_config_with_arrays(self, tmp_path):
        """Test loading config with arrays inside dict."""
        config_file = tmp_path / "config.json"
        data = {"hosts": ["example.com", "test.org"], "ports": [8080, 9000, 3000]}
        config_file.write_text(json.dumps(data))

        result = load_config(str(config_file))

        assert result == data

    def test_load_config_path_as_path_object(self, tmp_path):
        """Test that Path objects work correctly."""
        config_file = tmp_path / "config.json"
        data = {"test": "value"}
        config_file.write_text(json.dumps(data))

        result = load_config(str(config_file))

        assert result == data


# ============================================================================
# Default Config Path Tests
# ============================================================================


class TestGetDefaultConfigFile:
    """Tests for get_default_config_file() function."""

    def test_get_default_config_file_returns_string(self):
        """Test that default config file path is a string."""
        path = get_default_config_file()
        assert isinstance(path, str)

    def test_get_default_config_file_ends_with_config_json(self):
        """Test that default config file path ends with config.json."""
        path = get_default_config_file()
        assert path.endswith("config.json")

    def test_get_default_config_file_path_is_valid(self):
        """Test that default config file path can be converted to Path."""
        path = get_default_config_file()
        path_obj = Path(path)
        assert isinstance(path_obj, Path)


class TestGetDefaultDecodeGuideFile:
    """Tests for get_default_decode_guide_file() function."""

    def test_get_default_decode_guide_file_returns_string(self):
        """Test that decode guide file path is a string."""
        path = get_default_decode_guide_file()
        assert isinstance(path, str)

    def test_get_default_decode_guide_file_ends_with_json(self):
        """Test that decode guide file path ends with .json."""
        path = get_default_decode_guide_file()
        assert path.endswith(".json")

    def test_get_default_decode_guide_file_contains_decode_guide(self):
        """Test that path contains 'decode_guide'."""
        path = get_default_decode_guide_file()
        assert "decode_guide" in path.lower()

    def test_get_default_decode_guide_file_exists(self):
        """Test that default decode guide file exists."""
        path = get_default_decode_guide_file()
        assert Path(path).exists()


class TestGetDefaultBaseNovelDirs:
    """Tests for get_default_base_novel_dirs() function."""

    def test_get_default_base_novel_dirs_returns_string(self):
        """Test that base novel dirs path is a string."""
        path = get_default_base_novel_dirs()
        assert isinstance(path, str)

    def test_get_default_base_novel_dirs_path_is_valid(self):
        """Test that base novel dirs path can be converted to Path."""
        path = get_default_base_novel_dirs()
        path_obj = Path(path)
        assert isinstance(path_obj, Path)

    with pytest.raises(LoadConfigError):
        load_config(str(create_config_file))


def test_load_non_json_extension_raises_error(tmp_path):
    config_file = create_config_file(tmp_path / "config.txt", '{"test": 123}')

    with pytest.raises(LoadConfigError):
        load_config(str(config_file))


def test_load_invalid_path_type_raises_error():
    with pytest.raises(Exception):
        load_config(None)


def test_load_corrupted_json_raises_error(tmp_path):
    config_file = create_config_file(tmp_path / "config.json", '{"test": "abc"')

    with pytest.raises(LoadConfigError):
        load_config(str(config_file))


def test_load_json_null_returns_error(tmp_path):
    config_file = create_config_file(tmp_path / "config.json", "null")

    with pytest.raises(LoadConfigError):
        load_config(str(config_file))


def test_load_empty_json_object_returns_none(tmp_path):
    config_file = create_config_file(tmp_path / "config.json", "{}")
    with pytest.raises(EmptyConfigFileError):
        load_config(str(config_file))
