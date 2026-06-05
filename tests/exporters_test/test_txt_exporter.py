"""
Tests for TXTExporter
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock
from web_novel_scraper.exporters.txt_exporter import TXTExporter
from web_novel_scraper.models import Chapter, Metadata
from web_novel_scraper.novel_scraper import Novel
from web_novel_scraper.exceptions import (
    ChapterContentNotFoundError,
    ChapterTitleNotFoundError,
    InvalidOutputDirectoryError,
)


class TestTXTExporterInit:
    """Tests for TXTExporter initialization"""

    def test_init(self):
        """Test TXTExporter initialization"""
        exporter = TXTExporter()
        assert exporter.novel is None
        assert exporter.book_title is None
        assert exporter.txt_book == ""
        assert exporter._file_extension == ".txt"

    def test_file_extension(self):
        """Test file extension constant"""
        assert TXTExporter._file_extension == ".txt"


class TestTXTExporterCreateTxtBook:
    """Tests for _create_txt_book method"""

    def test_create_txt_book_with_all_metadata(self):
        """Test creating TXT book with title, description, and author"""
        exporter = TXTExporter()

        novel = Mock(spec=Novel)
        novel.title = "Test Novel"
        novel.metadata = Metadata(
            description="A test novel description", author="Test Author"
        )
        exporter.novel = novel
        exporter.txt_book = ""

        exporter._create_txt_book()

        assert "Title: Test Novel" in exporter.txt_book
        assert "Description: A test novel description" in exporter.txt_book
        assert "Author: Test Author" in exporter.txt_book

    def test_create_txt_book_title_required(self):
        """Test that title is always included"""
        exporter = TXTExporter()

        novel = Mock(spec=Novel)
        novel.title = "Novel Title"
        novel.metadata = Metadata()
        exporter.novel = novel
        exporter.txt_book = ""

        exporter._create_txt_book()

        assert "Title: Novel Title" in exporter.txt_book

    def test_create_txt_book_with_author_only(self):
        """Test creating TXT book with author only"""
        exporter = TXTExporter()

        novel = Mock(spec=Novel)
        novel.title = "Novel"
        novel.metadata = Metadata(author="Author Name")
        exporter.novel = novel
        exporter.txt_book = ""

        exporter._create_txt_book()

        assert "Author: Author Name" in exporter.txt_book
        assert "Description:" not in exporter.txt_book

    def test_create_txt_book_with_description_only(self):
        """Test creating TXT book with description only"""
        exporter = TXTExporter()

        novel = Mock(spec=Novel)
        novel.title = "Novel"
        novel.metadata = Metadata(description="Novel description")
        exporter.novel = novel
        exporter.txt_book = ""

        exporter._create_txt_book()

        assert "Description: Novel description" in exporter.txt_book
        assert "Author:" not in exporter.txt_book

    def test_create_txt_book_no_metadata(self):
        """Test creating TXT book with no metadata"""
        exporter = TXTExporter()

        novel = Mock(spec=Novel)
        novel.title = "Minimal Novel"
        novel.metadata = Metadata()
        exporter.novel = novel
        exporter.txt_book = ""

        exporter._create_txt_book()

        assert "Title: Minimal Novel" in exporter.txt_book
        # Only title should be there
        lines = exporter.txt_book.strip().split("\n")
        assert len(lines) >= 1

    def test_create_txt_book_formatting(self):
        """Test that metadata is properly formatted with spacing"""
        exporter = TXTExporter()

        novel = Mock(spec=Novel)
        novel.title = "Title"
        novel.metadata = Metadata(description="Description", author="Author")
        exporter.novel = novel
        exporter.txt_book = ""

        exporter._create_txt_book()

        # Check for proper spacing
        assert "\n\n" in exporter.txt_book


class TestTXTExporterAddChapterToBook:
    """Tests for _add_chapter_to_txt_book method"""

    def test_add_chapter_success(self):
        """Test successfully adding a chapter"""
        exporter = TXTExporter()
        exporter.txt_book = ""

        chapter = Chapter(
            chapter_url="http://example.com/chapter1",
            chapter_title="Chapter 1",
            chapter_content="This is the chapter content.",
        )

        exporter._add_chapter_to_txt_book(chapter)

        assert "Chapter 1" in exporter.txt_book
        assert "This is the chapter content." in exporter.txt_book
        assert "---" in exporter.txt_book

    def test_add_chapter_separator(self):
        """Test that chapters are separated by dashes"""
        exporter = TXTExporter()
        exporter.txt_book = ""

        chapter = Chapter(
            chapter_url="http://example.com/chapter1",
            chapter_title="Chapter 1",
            chapter_content="Content",
        )

        exporter._add_chapter_to_txt_book(chapter)

        assert "\n---\n" in exporter.txt_book

    def test_add_multiple_chapters(self):
        """Test adding multiple chapters"""
        exporter = TXTExporter()
        exporter.txt_book = ""

        for i in range(1, 4):
            chapter = Chapter(
                chapter_url=f"http://example.com/chapter{i}",
                chapter_title=f"Chapter {i}",
                chapter_content=f"Content {i}",
            )
            exporter._add_chapter_to_txt_book(chapter)

        assert "Chapter 1" in exporter.txt_book
        assert "Chapter 2" in exporter.txt_book
        assert "Chapter 3" in exporter.txt_book
        # Should have separators
        assert exporter.txt_book.count("---") >= 3

    def test_add_chapter_missing_title(self):
        """Test that ChapterTitleNotFoundError is raised when title is missing"""
        exporter = TXTExporter()
        exporter.txt_book = ""

        chapter = Chapter(
            chapter_url="http://example.com/chapter1", chapter_content="Content"
        )

        with pytest.raises(ChapterTitleNotFoundError):
            exporter._add_chapter_to_txt_book(chapter)

    def test_add_chapter_missing_content(self):
        """Test that ChapterContentNotFoundError is raised when content is missing"""
        exporter = TXTExporter()
        exporter.txt_book = ""

        chapter = Chapter(
            chapter_url="http://example.com/chapter1", chapter_title="Chapter 1"
        )

        with pytest.raises(ChapterContentNotFoundError):
            exporter._add_chapter_to_txt_book(chapter)

    def test_add_chapter_formatting(self):
        """Test that chapter is properly formatted"""
        exporter = TXTExporter()
        exporter.txt_book = ""

        chapter = Chapter(
            chapter_url="http://example.com/chapter1",
            chapter_title="Chapter Title",
            chapter_content="Chapter content here",
        )

        exporter._add_chapter_to_txt_book(chapter)

        # Check spacing
        assert "\n\n" in exporter.txt_book


class TestTXTExporterSaveTxtBook:
    """Tests for _save_txt_book method"""

    def test_save_txt_book_success(self):
        """Test successfully saving TXT book"""
        exporter = TXTExporter()
        exporter.book_title = "Test Book"
        exporter.txt_book = "Title: Test\nContent here"

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_book.txt"
            exporter._save_txt_book(output_path)

            assert output_path.exists()
            content = output_path.read_text()
            assert "Title: Test" in content
            assert "Content here" in content

    def test_save_txt_book_overwrites_existing(self):
        """Test that existing file is overwritten"""
        exporter = TXTExporter()
        exporter.book_title = "Test Book"

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_book.txt"

            # Create first file
            exporter.txt_book = "First content"
            exporter._save_txt_book(output_path)

            # Overwrite with second file
            exporter.txt_book = "Second content"
            exporter._save_txt_book(output_path)

            content = output_path.read_text()
            assert "Second content" in content
            assert "First content" not in content

    def test_save_txt_book_preserves_formatting(self):
        """Test that formatting is preserved when saving"""
        exporter = TXTExporter()
        exporter.book_title = "Test"
        exporter.txt_book = "Line 1\n\nLine 2\n---\nLine 3"

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.txt"
            exporter._save_txt_book(output_path)

            content = output_path.read_text()
            assert content == exporter.txt_book


class TestTXTExporterExportNovelToBook:
    """Tests for export_novel_to_book method"""

    def test_export_novel_to_book_success(self):
        """Test successfully exporting novel to TXT book"""
        exporter = TXTExporter()

        novel = Mock(spec=Novel)
        novel.title = "Test Novel"
        novel.metadata = Metadata(author="Test Author", description="Test Description")

        chapters = [
            Chapter(
                chapter_url="http://example.com/chapter1",
                chapter_title="Chapter 1",
                chapter_content="Content 1",
            ),
            Chapter(
                chapter_url="http://example.com/chapter2",
                chapter_title="Chapter 2",
                chapter_content="Content 2",
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            exporter.export_novel_to_book(
                novel=novel,
                chapters=chapters,
                book_title="Test Novel Export",
                output_directory=output_dir,
            )

            expected_file = output_dir / "Test Novel Export.txt"
            assert expected_file.exists()

            content = expected_file.read_text()
            assert "Title: Test Novel" in content
            assert "Author: Test Author" in content
            assert "Description: Test Description" in content
            assert "Chapter 1" in content
            assert "Chapter 2" in content

    def test_export_novel_to_book_invalid_output_directory(self):
        """Test that InvalidOutputDirectoryError is raised for invalid directory"""
        exporter = TXTExporter()

        novel = Mock(spec=Novel)
        chapters = []
        with tempfile.TemporaryFile() as tmpfile:
            with pytest.raises(InvalidOutputDirectoryError):
                exporter.export_novel_to_book(
                    novel=novel,
                    chapters=chapters,
                    book_title="Test Novel",
                    output_directory=tmpfile,
                )

    def test_export_novel_to_book_empty_chapters(self):
        """Test exporting novel with no chapters"""
        exporter = TXTExporter()

        novel = Mock(spec=Novel)
        novel.title = "Empty Novel"
        novel.metadata = Metadata(author="Author")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            exporter.export_novel_to_book(
                novel=novel,
                chapters=[],
                book_title="Empty Novel",
                output_directory=output_dir,
            )

            expected_file = output_dir / "Empty Novel.txt"
            assert expected_file.exists()

            content = expected_file.read_text()
            assert "Title: Empty Novel" in content

    def test_export_novel_to_book_no_metadata(self):
        """Test exporting novel with minimal metadata"""
        exporter = TXTExporter()

        novel = Mock(spec=Novel)
        novel.title = "Minimal Novel"
        novel.metadata = Metadata()

        chapters = [
            Chapter(
                chapter_url="http://example.com/ch1",
                chapter_title="Chapter 1",
                chapter_content="Content",
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            exporter.export_novel_to_book(
                novel=novel,
                chapters=chapters,
                book_title="Minimal",
                output_directory=output_dir,
            )

            expected_file = output_dir / "Minimal.txt"
            assert expected_file.exists()

    def test_export_novel_to_book_multiple_chapters(self):
        """Test exporting novel with multiple chapters"""
        exporter = TXTExporter()

        novel = Mock(spec=Novel)
        novel.title = "Multi Chapter Novel"
        novel.metadata = Metadata(author="Author", description="A novel")

        chapters = [
            Chapter(
                chapter_url=f"http://example.com/chapter{i}",
                chapter_title=f"Chapter {i}",
                chapter_content=f"Content of chapter {i}",
            )
            for i in range(1, 6)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            exporter.export_novel_to_book(
                novel=novel,
                chapters=chapters,
                book_title="Multi Chapter Novel",
                output_directory=output_dir,
            )

            expected_file = output_dir / "Multi Chapter Novel.txt"
            assert expected_file.exists()

            content = expected_file.read_text()
            for i in range(1, 6):
                assert f"Chapter {i}" in content

    def test_export_novel_to_book_with_path_object(self):
        """Test exporting with output_directory as Path object"""
        exporter = TXTExporter()

        novel = Mock(spec=Novel)
        novel.title = "Novel"
        novel.metadata = Metadata()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            exporter.export_novel_to_book(
                novel=novel, chapters=[], book_title="Test", output_directory=output_dir
            )

            expected_file = output_dir / "Test.txt"
            assert expected_file.exists()

    def test_export_novel_to_book_with_string_path(self):
        """Test exporting with output_directory as string"""
        exporter = TXTExporter()

        novel = Mock(spec=Novel)
        novel.title = "Novel"
        novel.metadata = Metadata()

        with tempfile.TemporaryDirectory() as tmpdir:
            exporter.export_novel_to_book(
                novel=novel, chapters=[], book_title="Test", output_directory=tmpdir
            )

            expected_file = Path(tmpdir) / "Test.txt"
            assert expected_file.exists()


class TestTXTExporterIntegration:
    """Integration tests for TXTExporter"""

    def test_full_export_workflow(self):
        """Test complete export workflow from start to finish"""
        exporter = TXTExporter()

        novel = Mock(spec=Novel)
        novel.title = "Complete Test Novel"
        novel.metadata = Metadata(
            author="Test Author",
            description="A comprehensive test novel",
        )

        chapters = [
            Chapter(
                chapter_url="http://example.com/prologue",
                chapter_title="Prologue",
                chapter_content="The story begins here...",
            ),
            Chapter(
                chapter_url="http://example.com/chapter1",
                chapter_title="Chapter 1: Introduction",
                chapter_content="Introducing the characters...",
            ),
            Chapter(
                chapter_url="http://example.com/chapter2",
                chapter_title="Chapter 2: Development",
                chapter_content="The plot thickens...",
            ),
            Chapter(
                chapter_url="http://example.com/chapter3",
                chapter_title="Chapter 3: Climax",
                chapter_content="Everything comes to a head...",
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            book_title = "Complete Test Novel - Full Export"

            exporter.export_novel_to_book(
                novel=novel,
                chapters=chapters,
                book_title=book_title,
                output_directory=output_dir,
            )

            expected_file = output_dir / f"{book_title}.txt"
            assert expected_file.exists()

            content = expected_file.read_text()

            # Verify metadata
            assert "Title: Complete Test Novel" in content
            assert "Author: Test Author" in content
            assert "Description: A comprehensive test novel" in content

            # Verify all chapters
            assert "Prologue" in content
            assert "Chapter 1: Introduction" in content
            assert "Chapter 2: Development" in content
            assert "Chapter 3: Climax" in content

            # Verify content
            assert "The story begins here..." in content
            assert "Introducing the characters..." in content

            # Verify file size (should contain substantial text)
            assert expected_file.stat().st_size > 300

    def test_export_large_novel(self):
        """Test exporting a large novel with many chapters"""
        exporter = TXTExporter()

        novel = Mock(spec=Novel)
        novel.title = "Large Novel"
        novel.metadata = Metadata(
            author="Prolific Author", description="A very long novel"
        )

        # Create 50 chapters
        chapters = [
            Chapter(
                chapter_url=f"http://example.com/chapter{i}",
                chapter_title=f"Chapter {i}",
                chapter_content=f"Content of chapter {i}" * 10,
            )
            for i in range(1, 51)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            exporter.export_novel_to_book(
                novel=novel,
                chapters=chapters,
                book_title="Large Novel",
                output_directory=output_dir,
            )

            expected_file = output_dir / "Large Novel.txt"
            assert expected_file.exists()

            content = expected_file.read_text()
            # Verify first and last chapters
            assert "Chapter 1" in content
            assert "Chapter 50" in content

    def test_export_maintains_state(self):
        """Test that exporter state is properly maintained"""
        exporter = TXTExporter()

        novel = Mock(spec=Novel)
        novel.title = "State Test Novel"
        novel.metadata = Metadata(author="Test")

        chapters = [
            Chapter(
                chapter_url="http://example.com/ch1",
                chapter_title="Ch1",
                chapter_content="Content",
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            book_title = "State Test"

            exporter.export_novel_to_book(
                novel=novel,
                chapters=chapters,
                book_title=book_title,
                output_directory=output_dir,
            )

            assert exporter.novel == novel
            assert exporter.book_title == book_title
            assert exporter.txt_book != ""
            assert "Title: State Test Novel" in exporter.txt_book

    def test_export_with_special_characters(self):
        """Test export with special characters in content"""
        exporter = TXTExporter()

        novel = Mock(spec=Novel)
        novel.title = "Novel with & Special chars <>"
        novel.metadata = Metadata(
            author="Author's Name", description="Description with 'quotes' & symbols"
        )

        chapters = [
            Chapter(
                chapter_url="http://example.com/chapter1",
                chapter_title="Chapter 1 - The <Beginning>",
                chapter_content="A tale & adventure with symbols: @ # $ %",
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            exporter.export_novel_to_book(
                novel=novel,
                chapters=chapters,
                book_title="Special Chars",
                output_directory=output_dir,
            )

            expected_file = output_dir / "Special Chars.txt"
            assert expected_file.exists()

            content = expected_file.read_text()
            # Special characters should be preserved in TXT
            assert "&" in content
            assert "%" in content

    def test_export_with_multiline_content(self):
        """Test export with multiline chapter content"""
        exporter = TXTExporter()

        novel = Mock(spec=Novel)
        novel.title = "Multiline Novel"
        novel.metadata = Metadata()

        chapters = [
            Chapter(
                chapter_url="http://example.com/chapter1",
                chapter_title="Chapter 1",
                chapter_content="Line 1\nLine 2\nLine 3\nLine 4",
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            exporter.export_novel_to_book(
                novel=novel,
                chapters=chapters,
                book_title="Multiline",
                output_directory=output_dir,
            )

            expected_file = output_dir / "Multiline.txt"
            assert expected_file.exists()

            content = expected_file.read_text()
            assert "Line 1" in content
            assert "Line 2" in content
            assert "Line 3" in content
            assert "Line 4" in content
