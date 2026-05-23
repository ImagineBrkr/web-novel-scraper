# tests/io_utils_test/test_decode_io_helper.py

import json

import pytest

from web_novel_scraper.io_helpers.decode_io_helper import (
    load_decode_guide,
)
from web_novel_scraper.exceptions import (
    LoadDecodeGuideError,
    DecodeGuideNotFoundError,
    DecodeGuideIsEmptyError,
    HostNotInDecodeGuideError,
    InvalidDecodeGuideError,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_decode_guide():
    """Sample decode guide data."""
    return [
        {"host": "example.com", "pattern": "pattern1", "encoding": "utf-8"},
        {"host": "test.org", "pattern": "pattern2", "encoding": "utf-8"},
        {"host": "novel.site", "pattern": "pattern3", "encoding": "gbk"},
    ]


@pytest.fixture
def decode_guide_file(tmp_path, sample_decode_guide):
    """Create a temporary decode guide file."""
    guide_file = tmp_path / "decode_guide.json"
    guide_file.write_text(json.dumps(sample_decode_guide))
    return guide_file


# ============================================================================
# load_decode_guide tests
# ============================================================================


class TestLoadDecodeGuide:
    """Tests for load_decode_guide() function."""

    def test_load_decode_guide_success(self, decode_guide_file, sample_decode_guide):
        """Test loading decode guide successfully."""
        result = load_decode_guide(str(decode_guide_file), "example.com")

        assert result == sample_decode_guide[0]
        assert result["host"] == "example.com"

    def test_load_decode_guide_multiple_hosts(
        self, decode_guide_file, sample_decode_guide
    ):
        """Test loading decode guide for different hosts."""
        result1 = load_decode_guide(str(decode_guide_file), "example.com")
        result2 = load_decode_guide(str(decode_guide_file), "test.org")
        result3 = load_decode_guide(str(decode_guide_file), "novel.site")

        assert result1["host"] == "example.com"
        assert result2["host"] == "test.org"
        assert result3["host"] == "novel.site"

    def test_load_decode_guide_with_complex_data(self, tmp_path):
        """Test loading decode guide with complex data structure."""
        guide_data = [
            {
                "host": "complex.com",
                "patterns": {"title": "regex_pattern", "content": "another_pattern"},
                "encoding": "utf-8",
                "settings": {"timeout": 30, "retries": 3},
            }
        ]
        guide_file = tmp_path / "complex_guide.json"
        guide_file.write_text(json.dumps(guide_data))

        result = load_decode_guide(str(guide_file), "complex.com")

        assert result == guide_data[0]
        assert result["patterns"]["title"] == "regex_pattern"

    def test_load_decode_guide_nonexistent_file_raises_error(self, tmp_path):
        """Test loading nonexistent decode guide file raises error."""
        nonexistent_file = tmp_path / "missing_guide.json"

        with pytest.raises(DecodeGuideNotFoundError):
            load_decode_guide(str(nonexistent_file), "example.com")

    def test_load_decode_guide_empty_file_raises_error(self, tmp_path):
        """Test loading empty decode guide file raises error."""
        empty_file = tmp_path / "empty_guide.json"
        empty_file.write_text("[]")

        with pytest.raises(DecodeGuideIsEmptyError):
            load_decode_guide(str(empty_file), "example.com")

    def test_load_decode_guide_empty_list_raises_error(self, tmp_path):
        """Test loading decode guide with empty list raises error."""
        empty_list_file = tmp_path / "empty_list_guide.json"
        empty_list_file.write_text("[]")

        with pytest.raises(DecodeGuideIsEmptyError):
            load_decode_guide(str(empty_list_file), "example.com")

    def test_load_decode_guide_host_not_found_raises_error(self, decode_guide_file):
        """Test loading with nonexistent host raises error."""
        with pytest.raises(HostNotInDecodeGuideError):
            load_decode_guide(str(decode_guide_file), "nonexistent.com")

    def test_load_decode_guide_invalid_json_raises_error(self, tmp_path):
        """Test loading invalid JSON raises error."""
        invalid_file = tmp_path / "invalid_guide.json"
        invalid_file.write_text('{"invalid": }')

        with pytest.raises(LoadDecodeGuideError):
            load_decode_guide(str(invalid_file), "example.com")

    def test_load_decode_guide_not_list_raises_error(self, tmp_path):
        """Test loading non-list JSON raises error."""
        dict_file = tmp_path / "dict_guide.json"
        dict_file.write_text('{"host": "example.com"}')

        with pytest.raises(LoadDecodeGuideError):
            load_decode_guide(str(dict_file), "example.com")

    def test_load_decode_guide_invalid_structure_raises_error(self, tmp_path):
        """Test loading with invalid structure raises error."""
        invalid_structure = [
            {"name": "example.com"},  # Missing "host" key
            {"host": "test.org"},
        ]
        invalid_file = tmp_path / "invalid_structure.json"
        invalid_file.write_text(json.dumps(invalid_structure))

        with pytest.raises(InvalidDecodeGuideError):
            load_decode_guide(str(invalid_file), "example.com")

    def test_load_decode_guide_none_file_raises_error(self):
        """Test with None file path raises error."""
        with pytest.raises(Exception):  # Will raise some error
            load_decode_guide(None, "example.com")

    def test_load_decode_guide_directory_path_raises_error(self, tmp_path):
        """Test with directory path raises error."""
        directory = tmp_path / "folder"
        directory.mkdir()

        with pytest.raises(Exception):  # InvalidPathError or similar
            load_decode_guide(str(directory), "example.com")

    def test_load_decode_guide_wrong_extension_raises_error(self, tmp_path):
        """Test with wrong file extension raises error."""
        wrong_file = tmp_path / "guide.txt"
        wrong_file.write_text("[]")

        with pytest.raises(Exception):  # InvalidFileTypeError
            load_decode_guide(str(wrong_file), "example.com")

    def test_load_decode_guide_case_sensitive_host(self, tmp_path):
        """Test that host matching is case sensitive."""
        guide_data = [{"host": "Example.COM", "pattern": "test"}]
        guide_file = tmp_path / "case_guide.json"
        guide_file.write_text(json.dumps(guide_data))

        # Should find exact match
        result = load_decode_guide(str(guide_file), "Example.COM")
        assert result["host"] == "Example.COM"

        # Should not find case-insensitive match
        with pytest.raises(HostNotInDecodeGuideError):
            load_decode_guide(str(guide_file), "example.com")

    def test_load_decode_guide_with_unicode_host(self, tmp_path):
        """Test loading decode guide with unicode characters."""
        guide_data = [{"host": "小说.中国", "pattern": "测试", "encoding": "utf-8"}]
        guide_file = tmp_path / "unicode_guide.json"
        guide_file.write_text(json.dumps(guide_data, ensure_ascii=True))

        result = load_decode_guide(str(guide_file), "小说.中国")

        assert result["host"] == "小说.中国"
        assert result["pattern"] == "测试"

    def test_load_decode_guide_with_extra_fields(self, tmp_path):
        """Test loading decode guide with extra fields."""
        guide_data = [
            {
                "host": "example.com",
                "pattern": "test",
                "encoding": "utf-8",
                "extra_field_1": "value1",
                "extra_field_2": {"nested": "value"},
            }
        ]
        guide_file = tmp_path / "extra_fields_guide.json"
        guide_file.write_text(json.dumps(guide_data))

        result = load_decode_guide(str(guide_file), "example.com")

        assert result["host"] == "example.com"
        assert result["extra_field_1"] == "value1"
        assert result["extra_field_2"]["nested"] == "value"
