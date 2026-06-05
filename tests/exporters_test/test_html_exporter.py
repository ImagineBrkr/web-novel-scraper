"""
Tests for HTMLExporter
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock
from web_novel_scraper.exporters.html_exporter import HTMLExporter
from web_novel_scraper.models import Chapter, Metadata
from web_novel_scraper.novel_scraper import Novel
from web_novel_scraper.exceptions import (
    ChapterContentNotFoundError,
    ChapterTitleNotFoundError,
    InvalidOutputDirectoryError,
)


class TestHTMLExporterInit:
    """Tests for HTMLExporter initialization"""

    def test_init(self):
        """Test HTMLExporter initialization"""
        exporter = HTMLExporter()
        assert exporter.novel is None
        assert exporter.book_title is None
        assert exporter.html_book is None
        assert exporter.chapters_html is None
        assert exporter._metadata_html is None
        assert exporter._file_extension == ".html"

    def test_file_extension(self):
        """Test file extension constant"""
        assert HTMLExporter._file_extension == ".html"


class TestHTMLExporterCreateMetadataHtml:
    """Tests for _create_metadata_html method"""

    def test_create_metadata_with_author_and_description(self):
        """Test creating metadata HTML with both author and description"""
        exporter = HTMLExporter()

        novel = Mock(spec=Novel)
        novel.metadata = Metadata(author="John Doe", description="An awesome story")
        exporter.novel = novel

        exporter._create_metadata_html()

        assert "John Doe" in exporter._metadata_html
        assert "An awesome story" in exporter._metadata_html
        assert "<strong>Author:" in exporter._metadata_html
        assert "<strong>Description:" in exporter._metadata_html

    def test_create_metadata_with_author_only(self):
        """Test creating metadata HTML with author only"""
        exporter = HTMLExporter()

        novel = Mock(spec=Novel)
        novel.metadata = Metadata(author="Jane Smith")
        exporter.novel = novel

        exporter._create_metadata_html()

        assert "Jane Smith" in exporter._metadata_html
        assert "Author" in exporter._metadata_html
        assert "Description" not in exporter._metadata_html

    def test_create_metadata_with_description_only(self):
        """Test creating metadata HTML with description only"""
        exporter = HTMLExporter()

        novel = Mock(spec=Novel)
        novel.metadata = Metadata(description="A great novel")
        exporter.novel = novel

        exporter._create_metadata_html()

        assert "A great novel" in exporter._metadata_html
        assert "Description" in exporter._metadata_html
        assert "Author" not in exporter._metadata_html

    def test_create_metadata_empty(self):
        """Test creating metadata HTML with no author or description"""
        exporter = HTMLExporter()

        novel = Mock(spec=Novel)
        novel.metadata = Metadata()
        exporter.novel = novel

        exporter._create_metadata_html()

        assert exporter._metadata_html == ""

    def test_create_metadata_escapes_html(self):
        """Test that metadata properly escapes HTML special characters"""
        exporter = HTMLExporter()

        novel = Mock(spec=Novel)
        novel.metadata = Metadata(
            author="Author & Co.", description="<script>alert('xss')</script>"
        )
        exporter.novel = novel

        exporter._create_metadata_html()

        assert "&amp;" in exporter._metadata_html
        assert "&lt;" in exporter._metadata_html
        assert "&gt;" in exporter._metadata_html
        assert "<script>" not in exporter._metadata_html


class TestHTMLExporterAddChapterToHtml:
    """Tests for _add_chapter_to_chapters_html method"""

    def test_add_chapter_success(self):
        """Test successfully adding a chapter"""
        exporter = HTMLExporter()
        exporter.chapters_html = ""

        chapter = Chapter(
            chapter_url="http://example.com/chapter1",
            chapter_title="Chapter 1",
            chapter_content="<p>Chapter content</p>",
        )

        exporter._add_chapter_to_chapters_html(chapter)

        assert "Chapter 1" in exporter.chapters_html
        assert "<p>Chapter content</p>" in exporter.chapters_html
        assert "active" in exporter.chapters_html

    def test_add_first_chapter_is_active(self):
        """Test that first chapter gets active class"""
        exporter = HTMLExporter()
        exporter.chapters_html = ""

        chapter = Chapter(
            chapter_url="http://example.com/chapter1",
            chapter_title="Chapter 1",
            chapter_content="Content",
        )

        exporter._add_chapter_to_chapters_html(chapter)

        assert 'class="chapter active"' in exporter.chapters_html

    def test_add_second_chapter_not_active(self):
        """Test that second chapter doesn't get active class"""
        exporter = HTMLExporter()
        exporter.chapters_html = '<div class="chapter active">Ch1</div>'

        chapter = Chapter(
            chapter_url="http://example.com/chapter2",
            chapter_title="Chapter 2",
            chapter_content="Content 2",
        )

        exporter._add_chapter_to_chapters_html(chapter)

        # Second chapter should not have active class
        lines = exporter.chapters_html.split("\n")
        chapters_div_lines = [line for line in lines if 'class="chapter' in line]
        assert 'class="chapter"' in chapters_div_lines[1]
        assert 'class="chapter active"' not in chapters_div_lines[1]

    def test_add_chapter_missing_title(self):
        """Test that ChapterTitleNotFoundError is raised when title is missing"""
        exporter = HTMLExporter()
        exporter.chapters_html = ""

        chapter = Chapter(
            chapter_url="http://example.com/chapter1", chapter_content="Content"
        )

        with pytest.raises(ChapterTitleNotFoundError):
            exporter._add_chapter_to_chapters_html(chapter)

    def test_add_chapter_missing_content(self):
        """Test that ChapterContentNotFoundError is raised when content is missing"""
        exporter = HTMLExporter()
        exporter.chapters_html = ""

        chapter = Chapter(
            chapter_url="http://example.com/chapter1", chapter_title="Chapter 1"
        )

        with pytest.raises(ChapterContentNotFoundError):
            exporter._add_chapter_to_chapters_html(chapter)

    def test_add_chapter_escapes_title(self):
        """Test that chapter title is properly escaped"""
        exporter = HTMLExporter()
        exporter.chapters_html = ""

        chapter = Chapter(
            chapter_url="http://example.com/chapter1",
            chapter_title="<script>alert('xss')</script>",
            chapter_content="Safe content",
        )

        exporter._add_chapter_to_chapters_html(chapter)

        assert "&lt;script&gt;" in exporter.chapters_html
        assert "<script>" not in exporter.chapters_html


class TestHTMLExporterCreateHtmlBook:
    """Tests for _create_html_book method"""

    def test_create_html_book(self):
        """Test HTML book creation"""
        exporter = HTMLExporter()

        novel = Mock(spec=Novel)
        novel.title = "Test Novel"
        exporter.novel = novel
        exporter.book_title = "Test Novel"
        exporter._metadata_html = "<div>Metadata</div>"
        exporter.chapters_html = "<div class='chapter active'>Chapter 1</div>"

        exporter._create_html_book()

        assert exporter.html_book is not None
        assert "Test Novel" in exporter.html_book
        assert "Metadata" in exporter.html_book
        assert "Chapter 1" in exporter.html_book
        assert "<!DOCTYPE html>" in exporter.html_book

    def test_create_html_book_escapes_title(self):
        """Test that novel title is escaped in HTML"""
        exporter = HTMLExporter()

        novel = Mock(spec=Novel)
        novel.title = "<b>Novel Title</b>"
        exporter.novel = novel
        exporter._metadata_html = ""
        exporter.chapters_html = ""

        exporter._create_html_book()

        assert "&lt;b&gt;" in exporter.html_book
        assert "<b>Novel Title</b>" not in exporter.html_book

    def test_create_html_book_contains_controls(self):
        """Test that HTML book contains interactive controls"""
        exporter = HTMLExporter()

        novel = Mock(spec=Novel)
        novel.title = "Novel"
        exporter.novel = novel
        exporter._metadata_html = ""
        exporter.chapters_html = ""

        exporter._create_html_book()

        # Check for JavaScript functions and UI elements
        assert "setPagedMode" in exporter.html_book
        assert "setContinuousMode" in exporter.html_book
        assert "setFontSize" in exporter.html_book
        assert "button" in exporter.html_book
        assert "localStorage" in exporter.html_book


class TestHTMLExporterSaveHtmlBook:
    """Tests for _save_html_book method"""

    def test_save_html_book_success(self):
        """Test successfully saving HTML book"""
        exporter = HTMLExporter()
        exporter.book_title = "Test Book"
        exporter.html_book = "<html><body>Test Content</body></html>"

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_book.html"
            exporter._save_html_book(output_path)

            assert output_path.exists()
            content = output_path.read_text()
            assert "Test Content" in content

    def test_save_html_book_overwrites_existing(self):
        """Test that existing file is overwritten"""
        exporter = HTMLExporter()
        exporter.book_title = "Test Book"

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_book.html"

            # Create first file
            exporter.html_book = "<html><body>First Content</body></html>"
            exporter._save_html_book(output_path)

            # Overwrite with second file
            exporter.html_book = "<html><body>Second Content</body></html>"
            exporter._save_html_book(output_path)

            content = output_path.read_text()
            assert "Second Content" in content
            assert "First Content" not in content


class TestHTMLExporterExportNovelToBook:
    """Tests for export_novel_to_book method"""

    def test_export_novel_to_book_success(self):
        """Test successfully exporting novel to HTML book"""
        exporter = HTMLExporter()

        novel = Mock(spec=Novel)
        novel.title = "Test Novel"
        novel.metadata = Metadata(author="Test Author", description="Test Description")

        chapters = [
            Chapter(
                chapter_url="http://example.com/chapter1",
                chapter_title="Chapter 1",
                chapter_content="<p>Content 1</p>",
            ),
            Chapter(
                chapter_url="http://example.com/chapter2",
                chapter_title="Chapter 2",
                chapter_content="<p>Content 2</p>",
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

            expected_file = output_dir / "Test Novel Export.html"
            assert expected_file.exists()

            content = expected_file.read_text(encoding="utf-8")
            assert "Test Novel" in content
            assert "Test Author" in content
            assert "Chapter 1" in content
            assert "Chapter 2" in content

    def test_export_novel_to_book_invalid_output_directory(self):
        """Test that InvalidOutputDirectoryError is raised for invalid directory"""
        exporter = HTMLExporter()

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
        exporter = HTMLExporter()

        novel = Mock(spec=Novel)
        novel.title = "Empty Novel"
        novel.metadata = Metadata(author="Test Author")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            exporter.export_novel_to_book(
                novel=novel,
                chapters=[],
                book_title="Empty Novel",
                output_directory=output_dir,
            )

            expected_file = output_dir / "Empty Novel.html"
            assert expected_file.exists()

    def test_export_novel_to_book_multiple_chapters(self):
        """Test exporting novel with multiple chapters"""
        exporter = HTMLExporter()

        novel = Mock(spec=Novel)
        novel.title = "Multi Chapter Novel"
        novel.metadata = Metadata(
            author="Author Name", description="A novel with many chapters"
        )

        chapters = [
            Chapter(
                chapter_url=f"http://example.com/chapter{i}",
                chapter_title=f"Chapter {i}",
                chapter_content=f"<p>Content of chapter {i}</p>",
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

            expected_file = output_dir / "Multi Chapter Novel.html"
            assert expected_file.exists()

            content = expected_file.read_text(encoding="utf-8")
            for i in range(1, 6):
                assert f"Chapter {i}" in content


class TestHTMLExporterIntegration:
    """Integration tests for HTMLExporter"""

    def test_full_export_workflow(self):
        """Test complete export workflow from start to finish"""
        exporter = HTMLExporter()

        novel = Mock(spec=Novel)
        novel.title = "Complete Test Novel"
        novel.metadata = Metadata(
            author="Test Author",
            description="A comprehensive test with full features",
        )

        chapters = [
            Chapter(
                chapter_url="http://example.com/prologue",
                chapter_title="Prologue",
                chapter_content="<h3>Prologue</h3><p>The beginning...</p>",
            ),
            Chapter(
                chapter_url="http://example.com/chapter1",
                chapter_title="Chapter 1: Introduction",
                chapter_content="<h3>Chapter 1</h3><p>Introducing the story...</p>",
            ),
            Chapter(
                chapter_url="http://example.com/chapter2",
                chapter_title="Chapter 2: Development",
                chapter_content="<h3>Chapter 2</h3><p>The plot develops...</p>",
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

            expected_file = output_dir / f"{book_title}.html"
            assert expected_file.exists()
            assert expected_file.stat().st_size > 1000

            content = expected_file.read_text(encoding="utf-8")

            # Verify content
            assert "Complete Test Novel" in content
            assert "Test Author" in content
            assert "Prologue" in content
            assert "Chapter 1: Introduction" in content
            assert "Chapter 2: Development" in content

            # Verify it's valid HTML
            assert "<!DOCTYPE html>" in content
            assert "</html>" in content

            # Verify interactive features
            assert "localStorage" in content
            assert "setPagedMode" in content
            assert "setContinuousMode" in content
            assert "setFontSize" in content
            assert "toggleTOC" in content

    def test_export_with_special_characters(self):
        """Test export with special characters and HTML content"""
        exporter = HTMLExporter()

        novel = Mock(spec=Novel)
        novel.title = "Novel & Story <Special>"
        novel.metadata = Metadata(
            author="Author's Name", description="Description with 'quotes' & symbols"
        )

        chapters = [
            Chapter(
                chapter_url="http://example.com/chapter1",
                chapter_title="Chapter 1 - <The Beginning>",
                chapter_content="<p>A tale & adventure</p>",
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            exporter.export_novel_to_book(
                novel=novel,
                chapters=chapters,
                book_title="Special Characters Novel",
                output_directory=output_dir,
            )

            expected_file = output_dir / "Special Characters Novel.html"
            assert expected_file.exists()

            content = expected_file.read_text(encoding="utf-8")
            # Verify escaping
            assert "&amp;" in content or "& " in content
            assert "&lt;" in content or "&#" in content

    def test_export_maintains_state(self):
        """Test that exporter state is properly maintained"""
        exporter = HTMLExporter()

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
            assert exporter.html_book is not None
            assert exporter.chapters_html != ""
            assert exporter._metadata_html != ""
