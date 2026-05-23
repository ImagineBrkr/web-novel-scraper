# tests/io_utils_test/test_novel_base_dir_helper.py

import json
from pathlib import Path

import pytest

from web_novel_scraper.io_helpers.novel_base_dir_helper import NovelBaseDirHelper
from web_novel_scraper.exceptions import (
    InvalidNovelBaseDirError,
    InvalidMetaFileError,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def base_novels_dir(tmp_path):
    """Create a base novels directory."""
    return tmp_path / "novels"


@pytest.fixture
def meta_file(base_novels_dir):
    """Create meta.json file in base novels dir."""
    base_novels_dir.mkdir(parents=True, exist_ok=True)
    meta_file_path = base_novels_dir / "meta.json"
    return meta_file_path


# ============================================================================
# get_novel_base_dir_from_meta tests
# ============================================================================


class TestGetNovelBaseDirFromMeta:
    """Tests for NovelBaseDirHelper.get_novel_base_dir_from_meta()"""

    def test_get_novel_base_dir_success(self, base_novels_dir, meta_file):
        """Test retrieving novel base directory from meta."""
        meta_data = {"Test Novel": {"novel_base_dir": "/path/to/novel"}}
        meta_file.write_text(json.dumps(meta_data))

        result = NovelBaseDirHelper.get_novel_base_dir_from_meta(
            "Test Novel", str(base_novels_dir)
        )

        assert result == "/path/to/novel"

    def test_get_novel_base_dir_multiple_novels(self, base_novels_dir, meta_file):
        """Test retrieving from meta with multiple novels."""
        meta_data = {
            "Novel 1": {"novel_base_dir": "/path/to/novel1"},
            "Novel 2": {"novel_base_dir": "/path/to/novel2"},
            "Novel 3": {"novel_base_dir": "/path/to/novel3"},
        }
        meta_file.write_text(json.dumps(meta_data))

        result1 = NovelBaseDirHelper.get_novel_base_dir_from_meta(
            "Novel 1", str(base_novels_dir)
        )
        result2 = NovelBaseDirHelper.get_novel_base_dir_from_meta(
            "Novel 2", str(base_novels_dir)
        )
        result3 = NovelBaseDirHelper.get_novel_base_dir_from_meta(
            "Novel 3", str(base_novels_dir)
        )

        assert result1 == "/path/to/novel1"
        assert result2 == "/path/to/novel2"
        assert result3 == "/path/to/novel3"

    def test_get_novel_base_dir_not_found_returns_none(
        self, base_novels_dir, meta_file
    ):
        """Test retrieving nonexistent novel returns None."""
        meta_data = {"Novel 1": {"novel_base_dir": "/path/to/novel1"}}
        meta_file.write_text(json.dumps(meta_data))

        result = NovelBaseDirHelper.get_novel_base_dir_from_meta(
            "Nonexistent Novel", str(base_novels_dir)
        )

        assert result is None

    def test_get_novel_base_dir_empty_dir_returns_none(self, base_novels_dir):
        """Test with nonexistent meta.json returns None."""
        result = NovelBaseDirHelper.get_novel_base_dir_from_meta(
            "Any Novel", str(base_novels_dir)
        )

        assert result is None

    def test_get_novel_base_dir_empty_meta_returns_none(
        self, base_novels_dir, meta_file
    ):
        """Test with empty meta.json returns None."""
        meta_file.write_text("{}")

        result = NovelBaseDirHelper.get_novel_base_dir_from_meta(
            "Any Novel", str(base_novels_dir)
        )

        assert result is None

    def test_get_novel_base_dir_missing_novel_base_dir_field_returns_none(
        self, base_novels_dir, meta_file
    ):
        """Test when novel_base_dir field is missing returns None."""
        meta_data = {
            "Novel 1": {}  # Missing novel_base_dir
        }
        meta_file.write_text(json.dumps(meta_data))

        result = NovelBaseDirHelper.get_novel_base_dir_from_meta(
            "Novel 1", str(base_novels_dir)
        )

        assert result is None

    def test_get_novel_base_dir_null_value_returns_none(
        self, base_novels_dir, meta_file
    ):
        """Test when novel_base_dir is null returns None."""
        meta_data = {"Novel 1": {"novel_base_dir": None}}
        meta_file.write_text(json.dumps(meta_data))

        result = NovelBaseDirHelper.get_novel_base_dir_from_meta(
            "Novel 1", str(base_novels_dir)
        )

        assert result is None

    def test_get_novel_base_dir_special_characters_in_title(
        self, base_novels_dir, meta_file
    ):
        """Test with special characters in novel title."""
        title = "Novel (Chinese Edition) - Chapter 1/2 [Updated]"
        meta_data = {title: {"novel_base_dir": "/path/to/novel"}}
        meta_file.write_text(json.dumps(meta_data))

        result = NovelBaseDirHelper.get_novel_base_dir_from_meta(
            title, str(base_novels_dir)
        )

        assert result == "/path/to/novel"

    def test_get_novel_base_dir_unicode_title(self, base_novels_dir, meta_file):
        """Test with unicode characters in novel title."""
        title = "中文小说: 修仙传记"
        meta_data = {title: {"novel_base_dir": "/path/to/novel"}}
        meta_file.write_text(json.dumps(meta_data, ensure_ascii=True))

        result = NovelBaseDirHelper.get_novel_base_dir_from_meta(
            title, str(base_novels_dir)
        )

        assert result == "/path/to/novel"


# ============================================================================
# save_novel_dir_to_meta tests
# ============================================================================


class TestSaveNovelDirToMeta:
    """Tests for NovelBaseDirHelper.save_novel_dir_to_meta()"""

    def test_save_novel_dir_success(self, base_novels_dir):
        """Test saving novel directory to meta successfully."""
        NovelBaseDirHelper.save_novel_dir_to_meta(
            "Test Novel", "/path/to/novel", str(base_novels_dir)
        )

        meta_file = base_novels_dir / "meta.json"
        assert meta_file.exists()

        meta_data = json.loads(meta_file.read_text())
        assert "Test Novel" in meta_data
        assert meta_data["Test Novel"]["novel_base_dir"] == "/path/to/novel"

    def test_save_multiple_novels(self, base_novels_dir):
        """Test saving multiple novels to meta."""
        NovelBaseDirHelper.save_novel_dir_to_meta(
            "Novel 1", "/path/1", str(base_novels_dir)
        )
        NovelBaseDirHelper.save_novel_dir_to_meta(
            "Novel 2", "/path/2", str(base_novels_dir)
        )
        NovelBaseDirHelper.save_novel_dir_to_meta(
            "Novel 3", "/path/3", str(base_novels_dir)
        )

        meta_file = base_novels_dir / "meta.json"
        meta_data = json.loads(meta_file.read_text())

        assert len(meta_data) == 3
        assert meta_data["Novel 1"]["novel_base_dir"] == "/path/1"
        assert meta_data["Novel 2"]["novel_base_dir"] == "/path/2"
        assert meta_data["Novel 3"]["novel_base_dir"] == "/path/3"

    def test_save_novel_overwrites_existing(self, base_novels_dir):
        """Test that saving same novel overwrites previous entry."""
        NovelBaseDirHelper.save_novel_dir_to_meta(
            "Novel 1", "/path/old", str(base_novels_dir)
        )
        NovelBaseDirHelper.save_novel_dir_to_meta(
            "Novel 1", "/path/new", str(base_novels_dir)
        )

        meta_file = base_novels_dir / "meta.json"
        meta_data = json.loads(meta_file.read_text())

        assert meta_data["Novel 1"]["novel_base_dir"] == "/path/new"

    def test_save_novel_creates_directory_if_not_exists(self, tmp_path):
        """Test that save creates base directory if it doesn't exist."""
        base_dir = tmp_path / "nonexistent" / "novels"

        NovelBaseDirHelper.save_novel_dir_to_meta(
            "Test Novel", "/path/to/novel", str(base_dir)
        )

        assert base_dir.exists()
        assert (base_dir / "meta.json").exists()

    def test_save_novel_preserves_existing_entries(self, base_novels_dir):
        """Test that saving new novel preserves existing entries."""
        NovelBaseDirHelper.save_novel_dir_to_meta(
            "Novel 1", "/path/1", str(base_novels_dir)
        )
        NovelBaseDirHelper.save_novel_dir_to_meta(
            "Novel 2", "/path/2", str(base_novels_dir)
        )

        meta_file = base_novels_dir / "meta.json"
        meta_data = json.loads(meta_file.read_text())

        # Both should exist
        assert "Novel 1" in meta_data
        assert "Novel 2" in meta_data

    def test_save_novel_with_special_characters_in_title(self, base_novels_dir):
        """Test saving with special characters in title."""
        title = "Novel [Complete] (Translator: John) - V2.0"
        path = "/path/to/novel"

        NovelBaseDirHelper.save_novel_dir_to_meta(title, path, str(base_novels_dir))

        meta_file = base_novels_dir / "meta.json"
        meta_data = json.loads(meta_file.read_text())

        assert title in meta_data
        assert meta_data[title]["novel_base_dir"] == path

    def test_save_novel_with_unicode_title(self, base_novels_dir):
        """Test saving with unicode characters in title."""
        title = "修仙小说：诡秘之主"
        path = "/path/to/novel"

        NovelBaseDirHelper.save_novel_dir_to_meta(title, path, str(base_novels_dir))

        meta_file = base_novels_dir / "meta.json"

        meta_data = json.loads(meta_file.read_text(encoding="utf-8"))

        assert title in meta_data
        assert meta_data[title]["novel_base_dir"] == path


# ============================================================================
# generate_novel_base_dir tests
# ============================================================================


class TestGenerateNovelBaseDir:
    """Tests for NovelBaseDirHelper.generate_novel_base_dir()"""

    def test_generate_valid_title(self, tmp_path):
        """Test generating base directory for valid title."""
        result = NovelBaseDirHelper.generate_novel_base_dir("My Novel", str(tmp_path))

        assert "My Novel" in result
        assert str(tmp_path) in result

    def test_generate_title_with_special_chars(self, tmp_path):
        """Test generating directory name sanitizes special characters."""
        result = NovelBaseDirHelper.generate_novel_base_dir(
            "My Novel @#$% [Special]", str(tmp_path)
        )

        # Should not contain invalid path characters
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result
        assert "%" not in result

    def test_generate_title_returns_path_string(self, tmp_path):
        """Test that result is a valid path string."""
        result = NovelBaseDirHelper.generate_novel_base_dir("Test Novel", str(tmp_path))

        assert isinstance(result, str)
        assert Path(result).is_absolute() or not Path(result).parts[0].startswith("/")

    def test_generate_different_titles_produce_different_paths(self, tmp_path):
        """Test that different titles produce different paths."""
        result1 = NovelBaseDirHelper.generate_novel_base_dir("Novel 1", str(tmp_path))
        result2 = NovelBaseDirHelper.generate_novel_base_dir("Novel 2", str(tmp_path))

        assert result1 != result2

    def test_generate_same_title_produces_same_path(self, tmp_path):
        """Test that same title produces same path."""
        result1 = NovelBaseDirHelper.generate_novel_base_dir(
            "Same Novel", str(tmp_path)
        )
        result2 = NovelBaseDirHelper.generate_novel_base_dir(
            "Same Novel", str(tmp_path)
        )

        assert result1 == result2

    def test_generate_title_with_spaces(self, tmp_path):
        """Test generating directory name preserves spaces."""
        result = NovelBaseDirHelper.generate_novel_base_dir(
            "My Test Novel", str(tmp_path)
        )

        # Spaces should be preserved in the path
        assert "My Test Novel" in result or "My_Test_Novel" in result

    def test_generate_title_with_unicode(self, tmp_path):
        """Test generating directory name with unicode."""
        result = NovelBaseDirHelper.generate_novel_base_dir("中文小说", str(tmp_path))

        assert isinstance(result, str)

    def test_generate_title_with_numbers(self, tmp_path):
        """Test generating directory name with numbers."""
        result = NovelBaseDirHelper.generate_novel_base_dir("Novel 123", str(tmp_path))

        assert "123" in result


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================


class TestNovelBaseDirHelperIntegration:
    """Integration tests for NovelBaseDirHelper."""

    def test_save_and_retrieve_novel(self, base_novels_dir):
        """Test save and retrieve operations together."""
        title = "Integration Test Novel"
        path = "/integration/test/novel"

        # Save
        NovelBaseDirHelper.save_novel_dir_to_meta(title, path, str(base_novels_dir))

        # Retrieve
        result = NovelBaseDirHelper.get_novel_base_dir_from_meta(
            title, str(base_novels_dir)
        )

        assert result == path

    def test_generate_save_and_retrieve(self, base_novels_dir):
        """Test generate, save, and retrieve operations together."""
        title = "Full Workflow Novel"

        # Generate
        generated_path = NovelBaseDirHelper.generate_novel_base_dir(
            title, str(base_novels_dir)
        )

        # Save
        NovelBaseDirHelper.save_novel_dir_to_meta(
            title, generated_path, str(base_novels_dir)
        )

        # Retrieve
        result = NovelBaseDirHelper.get_novel_base_dir_from_meta(
            title, str(base_novels_dir)
        )

        assert result == generated_path

    def test_complex_workflow_multiple_novels(self, base_novels_dir):
        """Test complex workflow with multiple novels."""
        novels = ["Novel A", "Novel B", "Novel C"]

        for novel in novels:
            path = NovelBaseDirHelper.generate_novel_base_dir(
                novel, str(base_novels_dir)
            )
            NovelBaseDirHelper.save_novel_dir_to_meta(novel, path, str(base_novels_dir))

        for novel in novels:
            result = NovelBaseDirHelper.get_novel_base_dir_from_meta(
                novel, str(base_novels_dir)
            )
            assert result is not None
            assert novel in result
