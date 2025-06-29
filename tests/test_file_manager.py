import pytest

from web_novel_scraper.file_manager import *


@pytest.fixture
def temp_base_dir(tmp_path):
    """Create a temporary base directory for testing."""
    return tmp_path / "novels"


@pytest.fixture
def file_manager(temp_base_dir):
    """Create a FileManager instance for testing."""
    return FileManager(
        title="Test Novel",
        base_novels_dir=temp_base_dir
    )


def test_file_manager_initialization(temp_base_dir):
    """Test FileManager initialization and directory creation."""
    manager = FileManager("Test Novel", temp_base_dir)
    assert manager.novel_base_dir.exists()
    assert manager.novel_data_dir.exists()
    assert manager.novel_chapters_dir.exists()
    assert manager.novel_toc_dir.exists()


def test_file_manager_read_only(temp_base_dir):
    """Test FileManager in read-only mode."""
    manager = FileManager("Test Novel", temp_base_dir, read_only=True)

    assert not manager.novel_base_dir.exists()
    assert not manager.novel_data_dir.exists()
    assert not manager.novel_chapters_dir.exists()


def test_save_and_load_chapter(file_manager):
    """Test saving and loading chapter content."""
    chapter_content = "<h1>Test Chapter</h1>"
    chapter_filename = "chapter_1.html"

    # Test saving
    file_manager.save_chapter_html(chapter_filename, chapter_content)
    assert file_manager.chapter_file_exists(chapter_filename)

    # Test loading
    loaded_content = file_manager.load_chapter_html(chapter_filename)
    assert loaded_content == chapter_content


def test_load_nonexistent_chapter(file_manager):
    """Test loading a chapter that doesn't exist."""
    content = file_manager.load_chapter_html("nonexistent.html")
    assert content is None


def test_delete_chapter(file_manager):
    """Test chapter deletion."""
    chapter_filename = "chapter_to_delete.html"
    file_manager.save_chapter_html(chapter_filename, "content")

    assert file_manager.chapter_file_exists(chapter_filename)
    file_manager.delete_chapter_html(chapter_filename)
    assert not file_manager.chapter_file_exists(chapter_filename)


def test_save_and_load_novel_data(file_manager):
    """Test saving and loading novel JSON data."""
    test_data = {"title": "Test Novel", "author": "Test Author"}

    file_manager.save_novel_data(test_data)
    loaded_data = file_manager.load_novel_data()

    assert loaded_data is not None
    assert isinstance(loaded_data, dict)

def test_save_invalid_novel_data(file_manager):
    """Test saving invalid novel JSON data."""
    with pytest.raises(ValidationError):
        file_manager.save_novel_data("invalid")

def test_load_invalid_novel_data(file_manager):
    """Test saving invalid novel JSON data."""
    file_manager.novel_json_file.write_text("invalid")
    with pytest.raises(ValidationError):
        file_manager.load_novel_data()

def test_toc_operations(file_manager):
    """Test table of contents operations."""
    # Test adding TOC
    toc_content = "<div>Chapter 1</div>"
    idx = file_manager.add_toc(toc_content)
    assert idx == 0

    # Test getting TOC
    loaded_toc = file_manager.get_toc(idx)
    assert loaded_toc == toc_content

    # Test updating TOC
    new_content = "<div>Updated Chapter 1</div>"
    file_manager.update_toc(idx, new_content)
    updated_toc = file_manager.get_toc(idx)
    assert updated_toc == new_content

    # Test getting all TOC
    all_toc = file_manager.get_all_toc()
    assert len(all_toc) == 1
    assert all_toc[0] == new_content


def test_invalid_operations(file_manager):
    """Test error handling for invalid operations."""
    with pytest.raises(FileManagerError):
        file_manager.update_toc(999, "content")

    assert file_manager.load_chapter_html("/invalid/path/chapter.html") is None

@pytest.mark.parametrize("title,expected_clean", [
    ("Test Novel", "Test Novel"),
    ("Test/'\\\"Novel!", "Test____Novel_"),
    ("Test & Novel", "Test _ Novel"),
])
def test_novel_directory_naming(temp_base_dir, title, expected_clean):
    """Test novel directory name normalization."""
    manager = FileManager(title, temp_base_dir)
    assert manager.novel_base_dir.name == expected_clean

