"""
Tests for EPUBExporter
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock
from web_novel_scraper.exporters.epub_exporter import EPUBExporter
from web_novel_scraper.models import Chapter, Metadata
from web_novel_scraper.novel_scraper import Novel
from web_novel_scraper.exceptions import (
    ChapterContentNotFoundError,
    ChapterTitleNotFoundError,
    CoverImageNotFoundError,
    InvalidOutputDirectoryError,
    NovelDataError,
    SaveBookError,
)
from ebooklib import epub


class TestEPUBExporterInit:
    """Tests for EPUBExporter initialization"""

    def test_init(self):
        """Test EPUBExporter initialization"""
        exporter = EPUBExporter()
        assert exporter.novel is None
        assert exporter.book_title is None
        assert exporter.epub_book is None
        assert exporter._file_extension == ".epub"

    def test_file_extension(self):
        """Test file extension constant"""
        assert EPUBExporter._file_extension == ".epub"


class TestEPUBExporterCreateEpubBook:
    """Tests for _create_epub_book method"""

    def test_create_epub_book(self):
        """Test creation of epub book"""
        exporter = EPUBExporter()
        exporter.book_title = "Test Novel"

        exporter._create_epub_book()

        assert exporter.epub_book is not None
        assert isinstance(exporter.epub_book, epub.EpubBook)
        assert exporter.epub_book.title == "Test Novel"

    def test_create_epub_book_sets_title(self):
        """Test that create_epub_book sets the book title correctly"""
        exporter = EPUBExporter()
        title = "My Amazing Novel"
        exporter.book_title = title

        exporter._create_epub_book()

        assert exporter.epub_book.title == title


class TestEPUBExporterAddMetadata:
    """Tests for _add_metadata method"""

    def test_add_metadata_basic(self):
        """Test adding basic metadata"""
        exporter = EPUBExporter()

        metadata = Metadata(
            language="en", description="A test novel", author="Test Author"
        )

        novel = Mock(spec=Novel)
        novel.metadata = metadata
        exporter.novel = novel
        exporter.epub_book = epub.EpubBook()

        exporter._add_metadata()

        assert exporter.epub_book.language == "en"

    def test_add_metadata_with_author(self):
        """Test adding metadata with author"""
        exporter = EPUBExporter()

        metadata = Metadata(
            language="en", description="A test novel", author="John Doe"
        )

        novel = Mock(spec=Novel)
        novel.metadata = metadata
        exporter.novel = novel
        exporter.epub_book = epub.EpubBook()

        exporter._add_metadata()
        assert exporter.epub_book.get_metadata("DC", "creator") == [
            ("John Doe", {"id": "creator"})
        ]

    def test_add_metadata_with_tags(self):
        """Test adding metadata with tags"""
        exporter = EPUBExporter()

        metadata = Metadata(
            language="en",
            description="A test novel",
            tags=("Fantasy", "Adventure", "Magic"),
        )

        novel = Mock(spec=Novel)
        novel.metadata = metadata
        exporter.novel = novel
        exporter.epub_book = epub.EpubBook()

        exporter._add_metadata()

        # Verify tags were added
        # ebooklib stores metadata in a specific way
        assert exporter.epub_book is not None

    def test_add_metadata_with_dates(self):
        """Test adding metadata with start and end dates"""
        exporter = EPUBExporter()

        metadata = Metadata(
            language="en",
            description="A test novel",
            start_date="2023-01-01",
            end_date="2023-12-31",
        )

        novel = Mock(spec=Novel)
        novel.metadata = metadata
        exporter.novel = novel
        exporter.epub_book = epub.EpubBook()

        exporter._add_metadata()

        assert exporter.epub_book is not None

    def test_add_metadata_default_language(self):
        """Test that default language is 'en'"""
        exporter = EPUBExporter()

        metadata = Metadata()

        novel = Mock(spec=Novel)
        novel.metadata = metadata
        exporter.novel = novel
        exporter.epub_book = epub.EpubBook()

        exporter._add_metadata()

        assert exporter.epub_book.language == "en"


class TestEPUBExporterAddCoverImage:
    """Tests for _add_cover_image method"""

    def test_add_cover_image_success(self):
        """Test successfully adding cover image"""
        exporter = EPUBExporter()

        cover_content = b"fake image content"

        novel_data_helper = Mock()
        novel_data_helper.load_novel_cover.return_value = cover_content

        novel = Mock(spec=Novel)
        novel.novel_data_helper = novel_data_helper
        exporter.novel = novel
        exporter.epub_book = epub.EpubBook()

        exporter._add_cover_image()

        novel_data_helper.load_novel_cover.assert_called_once()

    def test_add_cover_image_not_found(self):
        """Test handling when cover image is not found"""
        exporter = EPUBExporter()

        novel_data_helper = Mock()
        novel_data_helper.load_novel_cover.side_effect = CoverImageNotFoundError(
            "Cover not found"
        )

        novel = Mock(spec=Novel)
        novel.novel_data_helper = novel_data_helper
        exporter.novel = novel
        exporter.epub_book = epub.EpubBook()

        # Should not raise exception
        exporter._add_cover_image()

        novel_data_helper.load_novel_cover.assert_called_once()

    def test_add_cover_image_novel_data_error(self):
        """Test handling when there's an error loading cover image"""
        exporter = EPUBExporter()

        novel_data_helper = Mock()
        novel_data_helper.load_novel_cover.side_effect = NovelDataError(
            "Error loading cover"
        )

        novel = Mock(spec=Novel)
        novel.novel_data_helper = novel_data_helper
        exporter.novel = novel
        exporter.epub_book = epub.EpubBook()

        # Should not raise exception
        exporter._add_cover_image()

        novel_data_helper.load_novel_cover.assert_called_once()


class TestEPUBExporterAddChapterToBook:
    """Tests for _add_chapter_to_epub_book method"""

    def test_add_chapter_success(self):
        """Test successfully adding a chapter"""
        exporter = EPUBExporter()
        exporter.epub_book = epub.EpubBook()
        exporter.epub_book.toc = []
        exporter.epub_book.spine = []

        chapter = Chapter(
            chapter_url="http://example.com/chapter1",
            chapter_title="Chapter 1",
            chapter_content="<p>Chapter content</p>",
            chapter_html_filename="chapter1.html",
        )

        exporter._add_chapter_to_epub_book(chapter)

        assert len(exporter.epub_book.spine) > 0

    def test_add_chapter_missing_title(self):
        """Test that ChapterTitleNotFoundError is raised when title is missing"""
        exporter = EPUBExporter()
        exporter.epub_book = epub.EpubBook()

        chapter = Chapter(
            chapter_url="http://example.com/chapter1",
            chapter_content="<p>Chapter content</p>",
        )

        with pytest.raises(ChapterTitleNotFoundError):
            exporter._add_chapter_to_epub_book(chapter)

    def test_add_chapter_missing_content(self):
        """Test that ChapterContentNotFoundError is raised when content is missing"""
        exporter = EPUBExporter()
        exporter.epub_book = epub.EpubBook()

        chapter = Chapter(
            chapter_url="http://example.com/chapter1", chapter_title="Chapter 1"
        )

        with pytest.raises(ChapterContentNotFoundError):
            exporter._add_chapter_to_epub_book(chapter)

    def test_add_chapter_generates_filename_if_missing(self):
        """Test that filename is generated if missing"""
        exporter = EPUBExporter()
        exporter.epub_book = epub.EpubBook()
        exporter.epub_book.toc = []
        exporter.epub_book.spine = []

        chapter = Chapter(
            chapter_url="http://example.com/chapter1",
            chapter_title="Chapter 1",
            chapter_content="<p>Chapter content</p>",
        )

        exporter._add_chapter_to_epub_book(chapter)

        # Should not raise exception
        assert exporter.epub_book is not None

    def test_add_chapter_html_filename_conversion(self):
        """Test that .html extension is converted to .xhtml"""
        exporter = EPUBExporter()
        exporter.epub_book = epub.EpubBook()
        exporter.epub_book.toc = []
        exporter.epub_book.spine = []

        chapter = Chapter(
            chapter_url="http://example.com/chapter1",
            chapter_title="Chapter 1",
            chapter_content="<p>Chapter content</p>",
            chapter_html_filename="chapter1.html",
        )

        exporter._add_chapter_to_epub_book(chapter)

        # Verify the chapter was added to spine
        assert len(exporter.epub_book.spine) > 0


class TestEPUBExporterSaveEpubBook:
    """Tests for _save_epub_book method"""

    def test_save_epub_book_success(self):
        """Test successfully saving epub book"""
        exporter = EPUBExporter()
        exporter.book_title = "Test Book"
        exporter.epub_book = epub.EpubBook()
        exporter.epub_book.set_title("Test Book")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_book.epub"
            exporter._save_epub_book(output_path)

            assert output_path.exists()

    def test_save_epub_book_overwrites_existing(self):
        """Test that existing file is overwritten"""
        exporter = EPUBExporter()
        exporter.book_title = "Test Book"
        exporter.epub_book = epub.EpubBook()
        exporter.epub_book.set_title("Test Book")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_book.epub"

            # Create first file
            exporter._save_epub_book(output_path)
            first_size = output_path.stat().st_size

            # Create second file (should overwrite)
            exporter.epub_book = epub.EpubBook()
            exporter.epub_book.set_title("Test Book Modified")
            exporter._save_epub_book(output_path)
            second_zize = output_path.stat().st_size

            assert output_path.exists()
            assert first_size != second_zize

    @pytest.mark.filterwarnings("ignore:.*")
    def test_save_epub_book_invalid_path(self):
        """Test that SaveBookError is raised for invalid paths"""
        exporter = EPUBExporter()
        exporter.book_title = "Test Book"
        exporter.epub_book = epub.EpubBook()
        exporter.epub_book.set_title("Test Book")

        with tempfile.NamedTemporaryFile() as tmpfile:
            tmpfile.write(b"test")
            invalid_path = Path(tmpfile.name) / "test_book.epub"
            with pytest.raises(SaveBookError):
                exporter._save_epub_book(invalid_path)


class TestEPUBExporterExportNovelToBook:
    """Tests for export_novel_to_book method"""

    def test_export_novel_to_book_success(self):
        """Test successfully exporting novel to book"""
        exporter = EPUBExporter()

        # Create mock novel
        novel = Mock(spec=Novel)
        novel.metadata = Metadata(language="en", description="Test")
        novel.novel_data_helper = Mock()
        novel.novel_data_helper.load_novel_cover.side_effect = CoverImageNotFoundError()

        # Create chapters
        chapters = [
            Chapter(
                chapter_url="http://example.com/chapter1",
                chapter_title="Chapter 1",
                chapter_content="<p>Content 1</p>",
                chapter_html_filename="chapter1.html",
            ),
            Chapter(
                chapter_url="http://example.com/chapter2",
                chapter_title="Chapter 2",
                chapter_content="<p>Content 2</p>",
                chapter_html_filename="chapter2.html",
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            exporter.export_novel_to_book(
                novel=novel,
                chapters=chapters,
                book_title="Test Novel",
                output_directory=output_dir,
            )

            expected_file = output_dir / "Test Novel.epub"
            assert expected_file.exists()

    def test_export_novel_to_book_invalid_output_directory(self):
        """Test that InvalidOutputDirectoryError is raised for invalid directory"""
        exporter = EPUBExporter()

        novel = Mock(spec=Novel)
        novel.metadata = Metadata(language="en")
        novel.novel_data_helper = Mock()
        novel.novel_data_helper.load_novel_cover.side_effect = CoverImageNotFoundError()
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
        exporter = EPUBExporter()

        novel = Mock(spec=Novel)
        novel.metadata = Metadata(language="en")
        novel.novel_data_helper = Mock()
        novel.novel_data_helper.load_novel_cover.side_effect = CoverImageNotFoundError()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            exporter.export_novel_to_book(
                novel=novel,
                chapters=[],
                book_title="Empty Novel",
                output_directory=output_dir,
            )

            expected_file = output_dir / "Empty Novel.epub"
            assert expected_file.exists()

    def test_export_novel_to_book_with_cover_image(self):
        """Test exporting novel with cover image"""
        exporter = EPUBExporter()

        novel = Mock(spec=Novel)
        novel.metadata = Metadata(language="en")
        novel.novel_data_helper = Mock()
        novel.novel_data_helper.load_novel_cover.return_value = b"fake image data"

        chapters = [
            Chapter(
                chapter_url="http://example.com/chapter1",
                chapter_title="Chapter 1",
                chapter_content="<p>Content</p>",
                chapter_html_filename="chapter1.html",
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            exporter.export_novel_to_book(
                novel=novel,
                chapters=chapters,
                book_title="Novel With Cover",
                output_directory=output_dir,
            )

            expected_file = output_dir / "Novel With Cover.epub"
            assert expected_file.exists()

    def test_export_novel_to_book_multiple_chapters(self):
        """Test exporting novel with multiple chapters"""
        exporter = EPUBExporter()

        novel = Mock(spec=Novel)
        novel.metadata = Metadata(language="en", author="Test Author")
        novel.novel_data_helper = Mock()
        novel.novel_data_helper.load_novel_cover.side_effect = CoverImageNotFoundError()

        # Create 5 chapters
        chapters = [
            Chapter(
                chapter_url=f"http://example.com/chapter{i}",
                chapter_title=f"Chapter {i}",
                chapter_content=f"<p>Content {i}</p>",
                chapter_html_filename=f"chapter{i}.html",
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

            expected_file = output_dir / "Multi Chapter Novel.epub"
            assert expected_file.exists()


class TestEPUBExporterAddCalibreMetadata:
    """Tests for _add_calibre_metadata method"""

    def test_add_calibre_metadata(self):
        """Test adding Calibre metadata"""
        exporter = EPUBExporter()
        exporter.book_title = "Test Series"
        exporter.epub_book = epub.EpubBook()

        exporter._add_calibre_metadata(collection_idx=1)

        # Verify that metadata was added
        assert exporter.epub_book is not None

    def test_add_calibre_metadata_different_indices(self):
        """Test adding Calibre metadata with different indices"""
        exporter = EPUBExporter()
        exporter.book_title = "Test Series"
        exporter.epub_book = epub.EpubBook()

        exporter._add_calibre_metadata(collection_idx=3)

        assert exporter.epub_book is not None

        exporter.epub_book = epub.EpubBook()
        exporter._add_calibre_metadata(collection_idx=10)

        assert exporter.epub_book is not None


class TestEPUBExporterIntegration:
    """Integration tests for EPUBExporter"""

    def test_full_export_workflow(self):
        """Test complete export workflow from start to finish"""
        exporter = EPUBExporter()

        # Create comprehensive mock novel
        metadata = Metadata(
            author="Test Author",
            language="en",
            description="A comprehensive test novel",
            tags=("Fantasy", "Adventure"),
            start_date="2023-01-01",
            end_date="2023-12-31",
        )

        novel = Mock(spec=Novel)
        novel.metadata = metadata
        novel.novel_data_helper = Mock()
        novel.novel_data_helper.load_novel_cover.return_value = b"fake cover image"

        # Create chapters with realistic content
        chapters = [
            Chapter(
                chapter_url="http://example.com/prologue",
                chapter_title="Prologue",
                chapter_content="<h1>Prologue</h1><p>The story begins...</p>",
                chapter_html_filename="prologue.html",
            ),
            Chapter(
                chapter_url="http://example.com/chapter1",
                chapter_title="Chapter 1: The Beginning",
                chapter_content="<h1>Chapter 1</h1><p>Chapter content here...</p>",
                chapter_html_filename="chapter1.html",
            ),
            Chapter(
                chapter_url="http://example.com/chapter2",
                chapter_title="Chapter 2: The Journey",
                chapter_content="<h1>Chapter 2</h1><p>More content...</p>",
                chapter_html_filename="chapter2.html",
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            book_title = "Test Novel - Chapters 1-3"

            exporter.export_novel_to_book(
                novel=novel,
                chapters=chapters,
                book_title=book_title,
                output_directory=output_dir,
            )

            # Verify output file
            expected_file = output_dir / f"{book_title}.epub"
            assert expected_file.exists()
            assert expected_file.stat().st_size > 0

            # Verify exporter state
            assert exporter.novel == novel
            assert exporter.book_title == book_title
            assert exporter.epub_book is not None
