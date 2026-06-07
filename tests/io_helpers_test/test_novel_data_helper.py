# tests/io_utils_test/test_novel_data_helper.py

import json
import tempfile
import pytest
from pathlib import Path
from datetime import datetime

from web_novel_scraper.io_helpers.novel_data_helper import NovelDataHelper
from web_novel_scraper.exceptions import (
    SaveNovelDataError,
    InvalidNovelDataError,
    ChapterFileNotFoundError,
    ChapterFileIsEmptyError,
    CoverImageNotFoundError,
    LoadNovelDataError,
    TOCFragmentNotFoundError,
    CoverImageFileIsEmptyError,
    NovelDataNotFoundError,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_novel_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def novel_helper(temp_novel_dir):
    """Create a NovelDataHelper instance with a temp directory."""
    return NovelDataHelper(temp_novel_dir)


@pytest.fixture
def sample_novel_data():
    """Sample novel data for testing."""
    return {
        "title": "Test Novel",
        "author": "Test Author",
        "host": "example.com",
        "chapters": [],
    }


@pytest.fixture
def sample_html_content():
    """Sample HTML content for TOC fragments."""
    return """
    <html>
        <body>
            <ul>
                <li><a href="/chapter/1">Chapter 1</a></li>
                <li><a href="/chapter/2">Chapter 2</a></li>
            </ul>
        </body>
    </html>
    """


@pytest.fixture
def sample_cover_image(temp_novel_dir):
    """Create a sample cover image file."""
    cover_path = temp_novel_dir / "sample_cover.jpg"
    # Write some binary data to simulate an image
    cover_path.write_bytes(b"\xff\xd8\xff\xe0" + b"fake jpg data")
    return cover_path


# ============================================================================
# Constructor Tests
# ============================================================================


class TestNovelDataHelperConstructor:
    """Tests for NovelDataHelper initialization."""

    def test_constructor_creates_directories(self, temp_novel_dir):
        """Test that constructor creates all necessary directories."""
        helper = NovelDataHelper(temp_novel_dir)

        assert helper.novel_base_dir.exists()
        assert helper.novel_data_dir.exists()
        assert helper.novel_chapters_dir.exists()
        assert helper.novel_toc_dir.exists()

    def test_constructor_with_nonexistent_base_dir(self):
        """Test constructor creates base directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "nonexistent" / "path"
            NovelDataHelper(novel_dir)
            assert novel_dir.exists()


# ============================================================================
# Novel Data Tests
# ============================================================================


class TestSaveNovelData:
    """Tests for save_novel_data method."""

    def test_save_novel_data_success(self, novel_helper, sample_novel_data):
        """Test saving novel data successfully."""
        novel_helper.save_novel_data(sample_novel_data)

        assert novel_helper.novel_json_file.exists()
        with open(novel_helper.novel_json_file, "r") as f:
            saved_data = json.load(f)
        assert saved_data == sample_novel_data

    def test_save_novel_data_with_empty_dict(self, novel_helper):
        """Test saving an empty dictionary."""
        novel_helper.save_novel_data({})

        assert novel_helper.novel_json_file.exists()
        with open(novel_helper.novel_json_file, "r") as f:
            saved_data = json.load(f)
        assert saved_data == {}

    def test_save_novel_data_with_invalid_type_raises_error(self, novel_helper):
        """Test that saving non-dict data raises InvalidNovelDataError."""
        with pytest.raises(InvalidNovelDataError):
            novel_helper.save_novel_data("not a dict")

        with pytest.raises(InvalidNovelDataError):
            novel_helper.save_novel_data([1, 2, 3])

        with pytest.raises(InvalidNovelDataError):
            novel_helper.save_novel_data(None)

    def test_save_novel_data_overwrites_existing(self, novel_helper, sample_novel_data):
        """Test that saving twice overwrites the first data."""
        novel_helper.save_novel_data(sample_novel_data)

        new_data = {"title": "New Title", "author": "New Author"}
        novel_helper.save_novel_data(new_data)

        with open(novel_helper.novel_json_file, "r") as f:
            saved_data = json.load(f)
        assert saved_data == new_data


# ============================================================================
# Chapter Tests
# ============================================================================


class TestLoadNovelData:
    """Tests for the static load_novel_data method."""

    def test_load_novel_data_success(self, temp_novel_dir, sample_novel_data):
        """Test loading novel data from file successfully."""
        # Create the data directory structure and save some data
        helper = NovelDataHelper(temp_novel_dir)
        helper.save_novel_data(sample_novel_data)

        # Load the data using the static method
        loaded_data = NovelDataHelper.load_novel_data(temp_novel_dir)
        assert loaded_data == sample_novel_data

    def test_load_novel_from_existent_file(self, temp_novel_dir, sample_novel_data):
        """Test loading novel data from existing file successfully."""
        # Create the data directory structure and save some data
        novel_data_path = temp_novel_dir / "data"
        novel_data_path.mkdir(parents=True, exist_ok=True)
        json_data_path = novel_data_path / "main.json"

        json_data_path.write_text(json.dumps(sample_novel_data))

        # Load the data using the static method
        loaded_data = NovelDataHelper.load_novel_data(temp_novel_dir)
        assert loaded_data == sample_novel_data

    def test_load_novel_data_nonexistent_raises_error(self, temp_novel_dir):
        """Test loading novel data from nonexistent file raises NovelDataNotFoundError."""
        with pytest.raises(NovelDataNotFoundError):
            NovelDataHelper.load_novel_data(temp_novel_dir)

    def test_load_novel_data_empty_file_raises_error(self, temp_novel_dir):
        """Test loading from empty data file raises NovelDataNotFoundError."""
        helper = NovelDataHelper(temp_novel_dir)
        # Write empty JSON
        helper.novel_json_file.write_text("{}")

        with pytest.raises(NovelDataNotFoundError):
            NovelDataHelper.load_novel_data(temp_novel_dir)

    def test_load_novel_data_invalid_json_raises_error(self, temp_novel_dir):
        """Test loading invalid JSON raises LoadNovelDataError."""
        helper = NovelDataHelper(temp_novel_dir)
        # Write invalid JSON
        helper.novel_json_file.write_text("{ invalid json }")

        with pytest.raises(LoadNovelDataError):
            NovelDataHelper.load_novel_data(temp_novel_dir)


class TestChapterOperations:
    """Tests for chapter-related methods."""

    def test_save_chapter_html_success(self, novel_helper):
        """Test saving a chapter successfully."""
        chapter_content = "<h1>Chapter 1</h1><p>Content here</p>"
        novel_helper.save_chapter_html("chapter_1.html", chapter_content)

        chapter_path = novel_helper.novel_chapters_dir / "chapter_1.html"
        assert chapter_path.exists()
        assert chapter_path.read_text() == chapter_content

    def test_chapter_file_exists_returns_true_when_exists(self, novel_helper):
        """Test chapter_file_exists returns True for existing file."""
        chapter_file = "chapter_1.html"
        novel_helper.save_chapter_html(chapter_file, "<p>Content</p>")

        assert novel_helper.chapter_file_exists(chapter_file) is True

    def test_chapter_file_exists_returns_false_when_not_exists(self, novel_helper):
        """Test chapter_file_exists returns False for non-existing file."""
        assert novel_helper.chapter_file_exists("nonexistent.html") is False

    def test_load_chapter_html_success(self, novel_helper):
        """Test loading a chapter successfully."""
        chapter_content = "<h1>Chapter 1</h1><p>Content here</p>"
        novel_helper.save_chapter_html("chapter_1.html", chapter_content)

        loaded_content = novel_helper.load_chapter_html("chapter_1.html")
        assert loaded_content == chapter_content

    def test_load_chapter_html_nonexistent_raises_error(self, novel_helper):
        """Test loading nonexistent chapter raises ChapterFileNotFoundError."""
        with pytest.raises(ChapterFileNotFoundError):
            novel_helper.load_chapter_html("nonexistent.html")

    def test_load_empty_chapter_raises_error(self, novel_helper):
        """Test loading empty chapter raises ChapterFileIsEmptyError."""
        chapter_path = novel_helper.novel_chapters_dir / "empty.html"
        chapter_path.write_text("")

        with pytest.raises(ChapterFileIsEmptyError):
            novel_helper.load_chapter_html("empty.html")

    def test_delete_chapter_html_success(self, novel_helper):
        """Test deleting a chapter successfully."""
        novel_helper.save_chapter_html("chapter_1.html", "<p>Content</p>")
        novel_helper.delete_chapter_html("chapter_1.html")

        assert not novel_helper.chapter_file_exists("chapter_1.html")

    def test_delete_nonexistent_chapter_does_nothing(self, novel_helper):
        """Test deleting nonexistent chapter raises DeleteNovelDataError."""
        novel_helper.delete_chapter_html("nonexistent.html")

    def test_save_multiple_chapters(self, novel_helper):
        """Test saving multiple chapters."""
        for i in range(1, 6):
            content = f"<p>Chapter {i} content</p>"
            novel_helper.save_chapter_html(f"chapter_{i}.html", content)

        for i in range(1, 6):
            assert novel_helper.chapter_file_exists(f"chapter_{i}.html")


# ============================================================================
# Cover Image Tests
# ============================================================================


class TestCoverImageOperations:
    """Tests for cover image operations."""

    def test_save_novel_cover_success(self, novel_helper, sample_cover_image):
        """Test saving a cover image successfully."""
        novel_helper.save_novel_cover(str(sample_cover_image))

        assert novel_helper.novel_cover_file.exists()

    def test_load_novel_cover_success(self, novel_helper, sample_cover_image):
        """Test loading a cover image successfully."""
        novel_helper.save_novel_cover(str(sample_cover_image))
        loaded_cover = novel_helper.load_novel_cover()

        assert loaded_cover is not None
        assert isinstance(loaded_cover, bytes)
        assert len(loaded_cover) > 0

    def test_load_novel_cover_nonexistent_raises_error(self, novel_helper):
        """Test loading nonexistent cover raises CoverImageNotFoundError."""
        with pytest.raises(CoverImageNotFoundError):
            novel_helper.load_novel_cover()

    def test_save_cover_from_nonexistent_path_raises_error(self, novel_helper):
        """Test saving cover from nonexistent path raises SaveNovelDataError."""
        with pytest.raises(SaveNovelDataError):
            novel_helper.save_novel_cover("/nonexistent/path/cover.jpg")

    def test_load_empty_cover_raises_error(self, novel_helper):
        """Test loading empty cover file raises CoverImageFileIsEmptyError."""
        # Create empty cover file
        novel_helper.novel_cover_file.write_bytes(b"")
        with pytest.raises(CoverImageFileIsEmptyError):
            novel_helper.load_novel_cover()


# ============================================================================
# TOC Fragment Tests
# ============================================================================


class TestTOCFragmentOperations:
    """Tests for Table of Contents fragment operations."""

    def test_add_toc_fragment_success(self, novel_helper, sample_html_content):
        """Test adding a TOC fragment successfully."""
        novel_helper.add_toc_fragment(sample_html_content)

        toc_file = novel_helper.novel_toc_dir / "toc_0.html"
        assert toc_file.exists()
        assert toc_file.read_text() == sample_html_content

    def test_add_multiple_toc_fragments(self, novel_helper, sample_html_content):
        """Test adding multiple TOC fragments with correct indices."""
        for i in range(1, 4):
            novel_helper.add_toc_fragment(sample_html_content)

        for i in range(0, 3):
            toc_file = novel_helper.novel_toc_dir / f"toc_{i}.html"
            assert toc_file.exists()

    def test_get_toc_fragment_success(self, novel_helper, sample_html_content):
        """Test retrieving a TOC fragment successfully."""
        novel_helper.add_toc_fragment(sample_html_content)
        retrieved_content = novel_helper.get_toc_fragment(0)

        assert retrieved_content == sample_html_content

    def test_get_toc_fragment_nonexistent_raises_error(self, novel_helper):
        """Test retrieving nonexistent TOC fragment raises TOCFragmentNotFoundError."""
        with pytest.raises(TOCFragmentNotFoundError):
            novel_helper.get_toc_fragment(999)

    def test_get_all_toc_fragments_success(self, novel_helper, sample_html_content):
        """Test retrieving all TOC fragments."""
        contents = ["<html>Page 1</html>", "<html>Page 2</html>", "<html>Page 3</html>"]

        for content in contents:
            novel_helper.add_toc_fragment(content)

        all_fragments = novel_helper.get_all_toc_fragments()
        assert len(all_fragments) == 3
        assert all_fragments == contents

    def test_get_all_toc_fragments_empty_dir(self, novel_helper):
        """Test retrieving all TOC fragments from empty directory."""
        all_fragments = novel_helper.get_all_toc_fragments()
        assert all_fragments == []

    def test_delete_toc_fragment_success(self, novel_helper, sample_html_content):
        """Test deleting a TOC fragment successfully."""
        novel_helper.add_toc_fragment(sample_html_content)
        novel_helper.add_toc_fragment(sample_html_content)

        novel_helper.delete_toc_fragment(1)

        toc_file = novel_helper.novel_toc_dir / "toc_1.html"
        assert not toc_file.exists()

    def test_delete_toc_fragment_nonexistent_does_not_raise(self, novel_helper):
        """Test deleting nonexistent TOC fragment does not raise error."""
        # Should not raise, just log warning
        novel_helper.delete_toc_fragment(999)

    def test_delete_latest_toc_fragment_success(
        self, novel_helper, sample_html_content
    ):
        """Test deleting the latest TOC fragment."""
        novel_helper.add_toc_fragment(sample_html_content)
        novel_helper.add_toc_fragment(sample_html_content)
        novel_helper.add_toc_fragment(sample_html_content)

        novel_helper.delete_latest_toc_fragment()

        # The latest (toc_2) should be deleted
        toc_file = novel_helper.novel_toc_dir / "toc_2.html"
        assert not toc_file.exists()

        # Previous files should still exist
        assert (novel_helper.novel_toc_dir / "toc_0.html").exists()
        assert (novel_helper.novel_toc_dir / "toc_1.html").exists()

    def test_delete_latest_toc_fragment_when_only_one_exists(
        self, novel_helper, sample_html_content
    ):
        """Test delete_latest behavior when only toc_1 exists."""
        novel_helper.add_toc_fragment(sample_html_content)
        novel_helper.delete_latest_toc_fragment()

        assert not (novel_helper.novel_toc_dir / "toc_1.html").exists()

    def test_delete_latest_toc_fragment_empty_dir(self, novel_helper):
        """Test delete_latest_toc_fragment on empty directory doesn't raise."""
        # Should not raise, just log debug message
        novel_helper.delete_latest_toc_fragment()

    def test_delete_all_toc_fragments_success(self, novel_helper, sample_html_content):
        """Test deleting all TOC fragments successfully."""
        novel_helper.add_toc_fragment(sample_html_content)
        novel_helper.add_toc_fragment(sample_html_content)
        novel_helper.add_toc_fragment(sample_html_content)

        novel_helper.delete_all_toc_fragments()

        # All TOC files should be deleted
        assert (novel_helper.novel_toc_dir / "toc_0.html").exists() is False
        assert (novel_helper.novel_toc_dir / "toc_1.html").exists() is False
        assert (novel_helper.novel_toc_dir / "toc_2.html").exists() is False

    def test_delete_all_toc_fragments_empty_dir(self, novel_helper):
        """Test delete_all_toc_fragments on empty directory doesn't raise."""
        # Should not raise, just log debug message
        novel_helper.delete_all_toc_fragments()


# ============================================================================
# TOC Metadata Tests
# ============================================================================


class TestTOCMetadata:
    """Tests for TOC metadata operations."""

    def test_get_toc_last_updated_after_add(self, novel_helper, sample_html_content):
        """Test that last_updated is set after adding a fragment."""
        novel_helper.add_toc_fragment(sample_html_content)

        last_updated = novel_helper.get_toc_last_updated()
        assert last_updated is not None
        assert isinstance(last_updated, str)

        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(last_updated)

    def test_get_toc_last_updated_no_metadata(self, novel_helper):
        """Test get_toc_last_updated returns None when no metadata exists."""
        last_updated = novel_helper.get_toc_last_updated()
        assert last_updated is None

    def test_metadata_file_is_json(self, novel_helper, sample_html_content):
        """Test that metadata file is valid JSON."""
        novel_helper.add_toc_fragment(sample_html_content)

        metadata_file = novel_helper.novel_toc_metadata_file
        assert metadata_file.exists()

        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        assert "last_updated" in metadata

    def test_metadata_updated_on_multiple_adds(self, novel_helper, sample_html_content):
        """Test that metadata is updated each time a fragment is added."""
        novel_helper.add_toc_fragment(sample_html_content)
        first_update = novel_helper.get_toc_last_updated()

        # Add another fragment
        novel_helper.add_toc_fragment(sample_html_content)
        second_update = novel_helper.get_toc_last_updated()

        # The second timestamp should be >= first timestamp
        assert datetime.fromisoformat(second_update) >= datetime.fromisoformat(
            first_update
        )


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and integration scenarios."""

    def test_toc_indices_are_sequential(self, novel_helper, sample_html_content):
        """Test that TOC indices are sequential and correct."""
        for i in range(1, 6):
            novel_helper.add_toc_fragment(sample_html_content)

        for i in range(0, 5):
            assert (novel_helper.novel_toc_dir / f"toc_{i}.html").exists()

    def test_toc_index_continues_after_deletion(
        self, novel_helper, sample_html_content
    ):
        """Test that TOC index continues incrementing even after deletions."""
        novel_helper.add_toc_fragment(sample_html_content)  # toc_0
        novel_helper.add_toc_fragment(sample_html_content)  # toc_1
        novel_helper.delete_toc_fragment(0)

        novel_helper.add_toc_fragment(sample_html_content)  # Should be toc_2, not toc_1

        assert (novel_helper.novel_toc_dir / "toc_2.html").exists()
        assert not (novel_helper.novel_toc_dir / "toc_0.html").exists()

    def test_large_html_content_in_toc(self, novel_helper):
        """Test handling large HTML content in TOC."""
        large_content = "<html>" + "<li><a href='#'>Item</a></li>" * 10000 + "</html>"
        novel_helper.add_toc_fragment(large_content)

        retrieved = novel_helper.get_toc_fragment(0)
        assert retrieved == large_content

    def test_special_characters_in_html(self, novel_helper):
        """Test handling special characters in HTML content."""
        special_content = """
        <html>
            <body>
                <p>Spécial çháracters: 中文 日本語 한국어</p>
                <p>Symbols: © ® ™ € £ ¥</p>
            </body>
        </html>
        """
        novel_helper.add_toc_fragment(special_content)

        retrieved = novel_helper.get_toc_fragment(0)
        assert retrieved == special_content

    def test_mixed_operations(
        self, novel_helper, sample_novel_data, sample_cover_image, sample_html_content
    ):
        """Test mixed operations together."""
        # Save novel data
        novel_helper.save_novel_data(sample_novel_data)

        # Save cover
        novel_helper.save_novel_cover(str(sample_cover_image))

        # Add chapters
        novel_helper.save_chapter_html("ch1.html", "<p>Chapter 1</p>")
        novel_helper.save_chapter_html("ch2.html", "<p>Chapter 2</p>")

        # Add TOC fragments
        novel_helper.add_toc_fragment(sample_html_content)
        novel_helper.add_toc_fragment(sample_html_content)

        # Verify everything exists
        assert novel_helper.novel_json_file.exists()
        assert novel_helper.novel_cover_file.exists()
        assert novel_helper.chapter_file_exists("ch1.html")
        assert novel_helper.chapter_file_exists("ch2.html")
        assert (novel_helper.novel_toc_dir / "toc_0.html").exists()
        assert (novel_helper.novel_toc_dir / "toc_1.html").exists()
