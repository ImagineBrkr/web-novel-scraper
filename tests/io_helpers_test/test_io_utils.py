# tests/test_io_utils.py

import json
import pytest
from pathlib import Path

from web_novel_scraper.io_helpers.utils import IOUtils
from web_novel_scraper.exceptions import (
    InvalidPathError,
    FileNotFoundCustomError,
    InvalidFileTypeError,
    JsonParseError,
    InvalidJsonTypeError,
    EmptyFileError,
)


# ============================================================================
# Test Helpers
# ============================================================================


def create_json_file(path: Path, data: dict | list) -> Path:
    """Helper to create a JSON file with data."""
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def create_text_file(path: Path, content: str) -> Path:
    """Helper to create a text file."""
    path.write_text(content, encoding="utf-8")
    return path


# ============================================================================
# read_json_file tests
# ============================================================================


class TestReadJsonFile:
    """Tests for IOUtils.read_json_file()"""

    def test_invalid_path(self):
        """Test with None path raises InvalidPathError"""
        with pytest.raises(InvalidPathError):
            IOUtils.read_json_file(None, dict)

    def test_empty_string_path(self):
        """Test with empty string path raises InvalidPathError"""
        with pytest.raises(InvalidPathError):
            IOUtils.read_json_file("", dict)

    def test_file_not_found(self, tmp_path):
        """Test with non-existent file raises FileNotFoundCustomError"""
        path = tmp_path / "missing.json"
        with pytest.raises(FileNotFoundCustomError):
            IOUtils.read_json_file(path, dict)

    def test_directory_instead_of_file(self, tmp_path):
        """Test with directory path raises InvalidPathError"""
        directory = tmp_path / "folder.json"
        directory.mkdir()
        with pytest.raises(InvalidPathError):
            IOUtils.read_json_file(directory, dict)

    def test_wrong_extension(self, tmp_path):
        """Test with wrong file extension raises InvalidFileTypeError"""
        path = tmp_path / "config.txt"
        path.write_text("{}")
        with pytest.raises(InvalidFileTypeError):
            IOUtils.read_json_file(path, dict)

    def test_valid_json_dict(self, tmp_path):
        """Test reading valid JSON file with dict type"""
        data = {"name": "test", "value": 123}
        path = create_json_file(tmp_path / "config.json", data)
        result = IOUtils.read_json_file(path, dict)
        assert result == data

    def test_valid_json_list(self, tmp_path):
        """Test reading valid JSON file with list type"""
        data = [{"id": 1}, {"id": 2}]
        path = create_json_file(tmp_path / "items.json", data)
        result = IOUtils.read_json_file(path, list)
        assert result == data

    def test_invalid_json_syntax(self, tmp_path):
        """Test with invalid JSON syntax raises JsonParseError"""
        path = tmp_path / "invalid.json"
        path.write_text('{"invalid": }')
        with pytest.raises(JsonParseError):
            IOUtils.read_json_file(path, dict)

    def test_json_list_when_dict_expected(self, tmp_path):
        """Test JSON list when dict expected raises InvalidJsonTypeError"""
        data = [{"id": 1}]
        path = create_json_file(tmp_path / "data.json", data)
        with pytest.raises(InvalidJsonTypeError):
            IOUtils.read_json_file(path, dict)

    def test_json_dict_when_list_expected(self, tmp_path):
        """Test JSON dict when list expected raises InvalidJsonTypeError"""
        data = {"id": 1}
        path = create_json_file(tmp_path / "data.json", data)
        with pytest.raises(InvalidJsonTypeError):
            IOUtils.read_json_file(path, list)

    def test_json_number_raises_error(self, tmp_path):
        """Test JSON number type raises InvalidJsonTypeError"""
        path = tmp_path / "data.json"
        path.write_text("123")
        with pytest.raises(InvalidJsonTypeError):
            IOUtils.read_json_file(path, dict)

    def test_empty_dict(self, tmp_path):
        """Test reading empty JSON dict"""
        path = create_json_file(tmp_path / "empty.json", {})
        with pytest.raises(EmptyFileError):
            IOUtils.read_json_file(path, dict)

    def test_empty_list(self, tmp_path):
        """Test reading empty JSON list"""
        path = create_json_file(tmp_path / "empty.json", [])
        with pytest.raises(EmptyFileError):
            IOUtils.read_json_file(path, list)

    def test_complex_nested_json(self, tmp_path):
        """Test reading complex nested JSON structure"""
        data = {
            "users": [
                {"id": 1, "name": "Alice", "tags": ["admin", "user"]},
                {"id": 2, "name": "Bob", "tags": ["user"]},
            ],
            "settings": {"debug": True, "timeout": 30},
        }
        path = create_json_file(tmp_path / "complex.json", data)
        result = IOUtils.read_json_file(path, dict)
        assert result == data

    def test_path_as_string(self, tmp_path):
        """Test that string paths work correctly"""
        data = {"test": "value"}
        path = create_json_file(tmp_path / "config.json", data)
        result = IOUtils.read_json_file(str(path), dict)
        assert result == data


# ============================================================================
# read_text_file tests
# ============================================================================


class TestReadTextFile:
    """Tests for IOUtils.read_text_file()"""

    def test_invalid_path(self):
        """Test with None path raises InvalidPathError"""
        with pytest.raises(InvalidPathError):
            IOUtils.read_text_file(None)

    def test_file_not_found(self, tmp_path):
        """Test with non-existent file raises FileNotFoundCustomError"""
        path = tmp_path / "missing.txt"
        with pytest.raises(FileNotFoundCustomError):
            IOUtils.read_text_file(path)

    def test_directory_instead_of_file(self, tmp_path):
        """Test with directory path raises InvalidPathError"""
        directory = tmp_path / "folder"
        directory.mkdir()
        with pytest.raises(InvalidPathError):
            IOUtils.read_text_file(directory)

    def test_read_valid_text_file(self, tmp_path):
        """Test reading valid text file"""
        content = "Hello, World!\nThis is a test."
        path = create_text_file(tmp_path / "test.txt", content)
        result = IOUtils.read_text_file(path)
        assert result == content

    def test_read_empty_text_file(self, tmp_path):
        """Test reading empty text file"""
        path = create_text_file(tmp_path / "empty.txt", "")

        with pytest.raises(EmptyFileError):
            IOUtils.read_text_file(path)

    def test_read_multiline_text(self, tmp_path):
        """Test reading multiline text file"""
        content = "Line 1\nLine 2\nLine 3\n"
        path = create_text_file(tmp_path / "multiline.txt", content)
        result = IOUtils.read_text_file(path)
        assert result == content

    def test_read_text_with_special_chars(self, tmp_path):
        """Test reading text with special characters"""
        content = "Español: áéíóú\nChinese: 中文\nEmoji: 😀"
        path = create_text_file(tmp_path / "special.txt", content)
        result = IOUtils.read_text_file(path)
        assert result == content

    def test_path_as_string(self, tmp_path):
        """Test that string paths work correctly"""
        content = "test content"
        path = create_text_file(tmp_path / "test.txt", content)
        result = IOUtils.read_text_file(str(path))
        assert result == content


# ============================================================================
# read_binary_file tests
# ============================================================================


class TestReadBinaryFile:
    """Tests for IOUtils.read_binary_file()"""

    def test_invalid_path(self):
        """Test with None path raises InvalidPathError"""
        with pytest.raises(InvalidPathError):
            IOUtils.read_binary_file(None)

    def test_file_not_found(self, tmp_path):
        """Test with non-existent file raises FileNotFoundCustomError"""
        path = tmp_path / "missing.bin"
        with pytest.raises(FileNotFoundCustomError):
            IOUtils.read_binary_file(path)

    def test_read_binary_file(self, tmp_path):
        """Test reading binary file"""
        data = bytes("Binary content", encoding="utf-8")
        path = tmp_path / "test.bin"
        path.write_bytes(data)
        result = IOUtils.read_binary_file(path)
        assert result == data

    def test_read_empty_binary_file(self, tmp_path):
        """Test reading empty binary file"""
        path = tmp_path / "empty.bin"
        path.write_bytes(b"")
        with pytest.raises(EmptyFileError):
            IOUtils.read_binary_file(path)

    def test_path_as_string(self, tmp_path):
        """Test that string paths work correctly"""
        data = b"test data"
        path = tmp_path / "test.bin"
        path.write_bytes(data)
        result = IOUtils.read_binary_file(str(path))
        assert result == data


# ============================================================================
# save_json_file tests
# ============================================================================


class TestSaveJsonFile:
    """Tests for IOUtils.save_json_file()"""

    def test_invalid_path(self):
        """Test with None path raises InvalidPathError"""
        with pytest.raises(InvalidPathError):
            IOUtils.save_json_file(None, {})

    def test_wrong_extension(self, tmp_path):
        """Test with wrong extension raises InvalidFileTypeError"""
        path = tmp_path / "config.txt"
        with pytest.raises(InvalidFileTypeError):
            IOUtils.save_json_file(path, {})

    def test_invalid_data_type(self, tmp_path):
        """Test with invalid data type raises InvalidJsonTypeError"""
        path = tmp_path / "data.json"
        with pytest.raises(InvalidJsonTypeError):
            IOUtils.save_json_file(path, "invalid")

    def test_save_dict_to_json(self, tmp_path):
        """Test saving dict to JSON file"""
        data = {"name": "test", "value": 123}
        path = tmp_path / "config.json"
        IOUtils.save_json_file(path, data)
        assert path.exists()
        result = json.loads(path.read_text())
        assert result == data

    def test_save_list_to_json(self, tmp_path):
        """Test saving list to JSON file"""
        data = [{"id": 1}, {"id": 2}]
        path = tmp_path / "items.json"
        IOUtils.save_json_file(path, data)
        assert path.exists()
        result = json.loads(path.read_text())
        assert result == data

    def test_save_empty_dict(self, tmp_path):
        """Test saving empty dict"""
        path = tmp_path / "empty.json"
        IOUtils.save_json_file(path, {})
        assert path.exists()
        result = json.loads(path.read_text())
        assert result == {}

    def test_save_empty_list(self, tmp_path):
        """Test saving empty list"""
        path = tmp_path / "empty.json"
        IOUtils.save_json_file(path, [])
        assert path.exists()
        result = json.loads(path.read_text())
        assert result == []

    def test_overwrite_existing_json(self, tmp_path):
        """Test overwriting existing JSON file"""
        path = tmp_path / "config.json"
        old_data = {"old": "data"}
        new_data = {"new": "data"}

        IOUtils.save_json_file(path, old_data)
        IOUtils.save_json_file(path, new_data)

        result = json.loads(path.read_text())
        assert result == new_data
        assert "old" not in result

    def test_complex_nested_json_saved(self, tmp_path):
        """Test saving complex nested JSON"""
        data = {
            "users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
            "settings": {"debug": True},
        }
        path = tmp_path / "complex.json"
        IOUtils.save_json_file(path, data)
        result = json.loads(path.read_text())
        assert result == data

    def test_unicode_in_json(self, tmp_path):
        """Test saving JSON with Unicode characters"""
        data = {"message": "Hola mundo 中文 😀"}
        path = tmp_path / "unicode.json"
        IOUtils.save_json_file(path, data)
        result = json.loads(path.read_text(encoding="utf-8"))
        assert result == data

    def test_path_as_string(self, tmp_path):
        """Test that string paths work correctly"""
        data = {"test": "value"}
        path = str(tmp_path / "config.json")
        IOUtils.save_json_file(path, data)
        result = json.loads(Path(path).read_text())
        assert result == data


# ============================================================================
# save_text_file tests
# ============================================================================


class TestSaveTextFile:
    """Tests for IOUtils.save_text_file()"""

    def test_invalid_path(self):
        """Test with None path raises InvalidPathError"""
        with pytest.raises(InvalidPathError):
            IOUtils.save_text_file(None, "content")

    def test_save_text_file(self, tmp_path):
        """Test saving text file"""
        content = "Hello, World!"
        path = tmp_path / "test.txt"
        IOUtils.save_text_file(path, content)
        assert path.exists()
        assert path.read_text() == content

    def test_save_empty_text_file(self, tmp_path):
        """Test saving empty text file"""
        path = tmp_path / "empty.txt"
        IOUtils.save_text_file(path, "")
        assert path.exists()
        assert path.read_text() == ""

    def test_save_multiline_text(self, tmp_path):
        """Test saving multiline text"""
        content = "Line 1\nLine 2\nLine 3\n"
        path = tmp_path / "multiline.txt"
        IOUtils.save_text_file(path, content)
        assert path.read_text() == content

    def test_overwrite_existing_text_file(self, tmp_path):
        """Test overwriting existing text file"""
        path = tmp_path / "test.txt"
        IOUtils.save_text_file(path, "old content")
        IOUtils.save_text_file(path, "new content")
        assert path.read_text() == "new content"

    def test_save_unicode_text(self, tmp_path):
        """Test saving text with Unicode characters"""
        content = "Español: áéíóú\nChinese: 中文\nEmoji: 😀"
        path = tmp_path / "unicode.txt"
        IOUtils.save_text_file(path, content)
        assert path.read_text(encoding="utf-8") == content

    def test_path_as_string(self, tmp_path):
        """Test that string paths work correctly"""
        content = "test content"
        path = str(tmp_path / "test.txt")
        IOUtils.save_text_file(path, content)
        assert Path(path).read_text() == content


# ============================================================================
# save_binary_file tests
# ============================================================================


class TestSaveBinaryFile:
    """Tests for IOUtils.save_binary_file()"""

    def test_invalid_path(self):
        """Test with None path raises InvalidPathError"""
        with pytest.raises(InvalidPathError):
            IOUtils.save_binary_file(None, b"data")

    def test_save_binary_file(self, tmp_path):
        """Test saving binary file"""
        data = b"Binary content"
        path = tmp_path / "test.bin"
        IOUtils.save_binary_file(path, data)
        assert path.exists()
        assert path.read_bytes() == data

    def test_save_empty_binary(self, tmp_path):
        """Test saving empty binary file"""
        path = tmp_path / "empty.bin"
        IOUtils.save_binary_file(path, b"")
        assert path.exists()
        assert path.read_bytes() == b""

    def test_overwrite_binary_file(self, tmp_path):
        """Test overwriting existing binary file"""
        path = tmp_path / "test.bin"
        IOUtils.save_binary_file(path, b"old data")
        IOUtils.save_binary_file(path, b"new data")
        assert path.read_bytes() == b"new data"

    def test_path_as_string(self, tmp_path):
        """Test that string paths work correctly"""
        data = b"test data"
        path = str(tmp_path / "test.bin")
        IOUtils.save_binary_file(path, data)
        assert Path(path).read_bytes() == data


# ============================================================================
# delete_file tests
# ============================================================================


class TestDeleteFile:
    """Tests for IOUtils.delete_file()"""

    def test_delete_existing_file(self, tmp_path):
        """Test deleting existing file"""
        path = tmp_path / "test.txt"
        path.write_text("content")
        assert path.exists()
        IOUtils.delete_file(path)
        assert not path.exists()

    def test_delete_nonexistent_file(self, tmp_path):
        """Test deleting non-existent file does not raise error"""
        path = tmp_path / "missing.txt"
        IOUtils.delete_file(path)  # Should not raise

    def test_delete_directory_raises_error(self, tmp_path):
        """Test deleting a directory raises InvalidPathError"""
        directory = tmp_path / "folder"
        directory.mkdir()
        with pytest.raises(InvalidPathError):
            IOUtils.delete_file(directory)

    def test_invalid_path(self):
        """Test with None path raises InvalidPathError"""
        with pytest.raises(InvalidPathError):
            IOUtils.delete_file(None)

    def test_path_as_string(self, tmp_path):
        """Test that string paths work correctly"""
        path = tmp_path / "test.txt"
        path.write_text("content")
        IOUtils.delete_file(str(path))
        assert not path.exists()


# ============================================================================
# delete_dir tests
# ============================================================================


class TestDeleteDir:
    """Tests for IOUtils.delete_dir()"""

    def test_delete_existing_directory(self, tmp_path):
        """Test deleting existing empty directory"""
        directory = tmp_path / "folder"
        directory.mkdir()
        assert directory.exists()
        IOUtils.delete_dir(directory)
        assert not directory.exists()

    def test_delete_nonexistent_directory(self, tmp_path):
        """Test deleting non-existent directory does not raise error"""
        directory = tmp_path / "missing"
        IOUtils.delete_dir(directory)  # Should not raise

    def test_delete_file_raises_error(self, tmp_path):
        """Test deleting a file raises InvalidPathError"""
        path = tmp_path / "test.txt"
        path.write_text("content")
        with pytest.raises(InvalidPathError):
            IOUtils.delete_dir(path)

    def test_invalid_path(self):
        """Test with None path raises InvalidPathError"""
        with pytest.raises(InvalidPathError):
            IOUtils.delete_dir(None)

    def test_delete_nonempty_directory_raises_error(self, tmp_path):
        """Test deleting non-empty directory raises error"""
        directory = tmp_path / "folder"
        directory.mkdir()
        file_in_dir = directory / "file.txt"
        file_in_dir.write_text("content")

        with pytest.raises(Exception):  # OSError
            IOUtils.delete_dir(directory)

    def test_path_as_string(self, tmp_path):
        """Test that string paths work correctly"""
        directory = tmp_path / "folder"
        directory.mkdir()
        IOUtils.delete_dir(str(directory))
        assert not directory.exists()


# ============================================================================
# dir_exists tests
# ============================================================================


class TestDirExists:
    """Tests for IOUtils.dir_exists()"""

    def test_existing_directory(self, tmp_path):
        """Test checking existing directory returns True"""
        directory = tmp_path / "folder"
        directory.mkdir()
        assert IOUtils.dir_exists(directory) is True

    def test_nonexistent_directory(self, tmp_path):
        """Test checking non-existent directory returns False"""
        directory = tmp_path / "missing"
        assert IOUtils.dir_exists(directory) is False

    def test_file_instead_of_directory_raises_error(self, tmp_path):
        """Test checking file path raises InvalidPathError"""
        path = tmp_path / "test.txt"
        path.write_text("content")
        with pytest.raises(InvalidPathError):
            IOUtils.dir_exists(path)

    def test_invalid_path(self):
        """Test with None path raises InvalidPathError"""
        with pytest.raises(InvalidPathError):
            IOUtils.dir_exists(None)

    def test_path_as_string(self, tmp_path):
        """Test that string paths work correctly"""
        directory = tmp_path / "folder"
        directory.mkdir()
        assert IOUtils.dir_exists(str(directory)) is True


# ============================================================================
# ensure_dir tests
# ============================================================================


class TestEnsureDir:
    """Tests for IOUtils.ensure_dir()"""

    def test_create_new_directory(self, tmp_path):
        """Test creating new directory"""
        directory = tmp_path / "new_folder"
        assert not directory.exists()
        IOUtils.ensure_dir(directory)
        assert directory.exists() and directory.is_dir()

    def test_create_nested_directories(self, tmp_path):
        """Test creating nested directories"""
        directory = tmp_path / "parent" / "child" / "grandchild"
        assert not directory.exists()
        IOUtils.ensure_dir(directory)
        assert directory.exists() and directory.is_dir()

    def test_ensure_existing_directory(self, tmp_path):
        """Test ensuring existing directory does not raise error"""
        directory = tmp_path / "existing"
        directory.mkdir()
        IOUtils.ensure_dir(directory)  # Should not raise
        assert directory.exists()

    def test_invalid_path(self):
        """Test with None path raises InvalidPathError"""
        with pytest.raises(InvalidPathError):
            IOUtils.ensure_dir(None)

    def test_path_as_string(self, tmp_path):
        """Test that string paths work correctly"""
        directory = str(tmp_path / "new_folder")
        IOUtils.ensure_dir(directory)
        assert Path(directory).exists()


# ============================================================================
# get_path_in_dir tests
# ============================================================================


class TestGetPathInDir:
    """Tests for IOUtils.get_path_in_dir()"""

    def test_get_path_for_file(self, tmp_path):
        """Test getting path for a file inside directory"""
        result = IOUtils.get_path_in_dir(tmp_path, "file.txt")
        assert isinstance(result, Path)
        assert result == tmp_path / "file.txt"

    def test_get_path_for_directory(self, tmp_path):
        """Test getting path for a directory inside directory"""
        result = IOUtils.get_path_in_dir(tmp_path, "subfolder")
        assert isinstance(result, Path)
        assert result == tmp_path / "subfolder"

    def test_path_as_string(self, tmp_path):
        """Test that string paths work correctly"""
        result = IOUtils.get_path_in_dir(str(tmp_path), "file.txt")
        assert isinstance(result, Path)
        assert result == tmp_path / "file.txt"

    def test_invalid_path(self):
        """Test with None path raises InvalidPathError"""
        with pytest.raises(InvalidPathError):
            IOUtils.get_path_in_dir(None, "file.txt")


# ============================================================================
# sanitize_name_to_valid_path tests
# ============================================================================


class TestSanitizeDirname:
    """Tests for IOUtils.sanitize_name_to_valid_path()"""

    def test_valid_dirname_unchanged(self):
        """Test that valid dirname is not changed"""
        name = "my_folder-123"
        assert IOUtils.sanitize_name_to_valid_path(name) == name

    def test_remove_special_characters(self):
        """Test removing special characters"""
        name = 'folder"<>name'
        result = IOUtils.sanitize_name_to_valid_path(name)
        assert result == "folder___name"

    def test_keep_spaces(self):
        """Test keeping spaces"""
        name = "folder with spaces"
        result = IOUtils.sanitize_name_to_valid_path(name)
        assert result == "folder with spaces"

    def test_keep_hyphens_and_underscores(self):
        """Test keeping hyphens and underscores"""
        name = "folder-name_test"
        result = IOUtils.sanitize_name_to_valid_path(name)
        assert result == "folder-name_test"

    def test_keep_digits_and_letters(self):
        """Test keeping digits and letters"""
        name = "folder123ABC"
        result = IOUtils.sanitize_name_to_valid_path(name)
        assert result == "folder123ABC"

    def test_empty_string(self):
        """Test with empty string"""
        name = ""
        result = IOUtils.sanitize_name_to_valid_path(name)
        assert result == ""

    def test_only_special_chars(self):
        """Test string with only special characters"""
        name = '/\\:*?"<>|'
        result = IOUtils.sanitize_name_to_valid_path(name)
        assert result == "_________"


# ============================================================================
# copy_file tests
# ============================================================================


class TestCopyFile:
    """Tests for IOUtils.copy_file()"""

    def test_copy_file_success(self, tmp_path):
        """Test copying a file successfully"""
        src = tmp_path / "source.txt"
        dst = tmp_path / "destination.txt"
        content = "test content"
        src.write_text(content)

        IOUtils.copy_file(src, dst)

        assert dst.exists()
        assert dst.read_text() == content

    def test_copy_file_overwrites_existing(self, tmp_path):
        """Test copying over existing file"""
        src = tmp_path / "source.txt"
        dst = tmp_path / "destination.txt"
        src.write_text("new content")
        dst.write_text("old content")

        IOUtils.copy_file(src, dst)

        assert dst.read_text() == "new content"

    def test_copy_binary_file(self, tmp_path):
        """Test copying a binary file"""
        src = tmp_path / "source.bin"
        dst = tmp_path / "destination.bin"
        data = b"\xff\xd8\xff\xe0binary data"
        src.write_bytes(data)

        IOUtils.copy_file(src, dst)

        assert dst.exists()
        assert dst.read_bytes() == data

    def test_copy_creates_parent_directories(self, tmp_path):
        """Test that copy creates parent directories if needed"""
        src = tmp_path / "source.txt"
        dst = tmp_path / "nested" / "dir" / "destination.txt"
        src.write_text("content")

        IOUtils.copy_file(src, dst)

        assert dst.exists()
        assert dst.read_text() == "content"

    def test_copy_nonexistent_source_raises_error(self, tmp_path):
        """Test copying nonexistent source file raises error"""
        src = tmp_path / "missing.txt"
        dst = tmp_path / "destination.txt"

        with pytest.raises(Exception):  # FileNotFoundCustomError
            IOUtils.copy_file(src, dst)

    def test_copy_source_is_directory_raises_error(self, tmp_path):
        """Test copying from directory raises error"""
        src = tmp_path / "source_dir"
        dst = tmp_path / "destination.txt"
        src.mkdir()

        with pytest.raises(Exception):  # InvalidPathError
            IOUtils.copy_file(src, dst)

    def test_copy_same_source_and_dest_raises_error(self, tmp_path):
        """Test that copying to same path raises error"""
        path = tmp_path / "file.txt"
        path.write_text("content")

        with pytest.raises(InvalidPathError):
            IOUtils.copy_file(path, path)

    def test_copy_as_string_paths(self, tmp_path):
        """Test that string paths work correctly"""
        src = tmp_path / "source.txt"
        dst = tmp_path / "destination.txt"
        src.write_text("content")

        IOUtils.copy_file(str(src), str(dst))

        assert dst.read_text() == "content"


# ============================================================================
# list_files_from_dir tests
# ============================================================================


class TestListFilesFromDir:
    """Tests for IOUtils.list_files_from_dir()"""

    def test_list_files_in_directory(self, tmp_path):
        """Test listing files in directory"""
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        (tmp_path / "file3.txt").write_text("content3")

        files = IOUtils.list_files_from_dir(tmp_path, "*.txt")

        assert len(files) == 3
        assert all(isinstance(f, Path) for f in files)

    def test_list_files_with_glob_pattern(self, tmp_path):
        """Test listing files with specific glob pattern"""
        (tmp_path / "file1.txt").write_text("content")
        (tmp_path / "file2.txt").write_text("content")
        (tmp_path / "file.json").write_text("{}")

        files = IOUtils.list_files_from_dir(tmp_path, "*.txt")

        assert len(files) == 2
        assert all(str(f).endswith(".txt") for f in files)

    def test_list_files_empty_directory_raises_error(self, tmp_path):
        """Test listing files in empty directory raises EmptyDirError"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(Exception):  # EmptyDirError
            IOUtils.list_files_from_dir(empty_dir)

    def test_list_files_no_matches_raises_error(self, tmp_path):
        """Test listing with no matching files raises EmptyDirError"""
        (tmp_path / "file.txt").write_text("content")

        with pytest.raises(Exception):  # EmptyDirError
            IOUtils.list_files_from_dir(tmp_path, "*.json")

    def test_list_files_ignores_directories(self, tmp_path):
        """Test that listing only returns files, not directories"""
        (tmp_path / "file.txt").write_text("content")
        (tmp_path / "subfolder").mkdir()

        files = IOUtils.list_files_from_dir(tmp_path, "*")

        assert len(files) == 1
        assert files[0].name == "file.txt"

    def test_list_files_nested_pattern(self, tmp_path):
        """Test listing with nested glob pattern"""
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (subdir / "file.txt").write_text("content")
        (tmp_path / "file.txt").write_text("content")

        files = IOUtils.list_files_from_dir(tmp_path, "*.txt")

        assert len(files) == 1  # Only top-level files

    def test_list_files_nonexistent_directory_raises_error(self, tmp_path):
        """Test listing from nonexistent directory raises error"""
        nonexistent = tmp_path / "missing"

        with pytest.raises(Exception):  # InvalidPathError
            IOUtils.list_files_from_dir(nonexistent)

    def test_list_files_path_is_file_raises_error(self, tmp_path):
        """Test listing when path is a file raises error"""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        with pytest.raises(Exception):  # InvalidPathError
            IOUtils.list_files_from_dir(file_path)

    def test_list_files_as_string_path(self, tmp_path):
        """Test that string paths work correctly"""
        (tmp_path / "file.txt").write_text("content")

        files = IOUtils.list_files_from_dir(str(tmp_path), "*.txt")

        assert len(files) == 1
