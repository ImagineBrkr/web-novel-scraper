import json
from datetime import datetime

import pytest

from web_novel_scraper.exceptions import (
    ChapterFileIsEmptyError,
    ChapterFileNotFoundError,
    CoverImageFileIsEmptyError,
    CoverImageNotFoundError,
    LoadNovelDataError,
    NovelDataNotFoundError,
    SaveNovelDataError,
    TOCFragmentNotFoundError,
)
from web_novel_scraper.novel_scraper import Novel
from web_novel_scraper.persistence.novel_repository import NovelRepository


@pytest.fixture
def temp_novel_dir(tmp_path):
    return tmp_path / "novel"


@pytest.fixture
def novel_repository(temp_novel_dir):
    repository = NovelRepository(temp_novel_dir)
    repository.initialize_directories()
    return repository


@pytest.fixture
def sample_novel():
    return Novel(
        title="Test Novel",
        toc_main_url="https://example.com/novel/toc",
        host="example.com",
    )


@pytest.fixture
def sample_html_content():
    return """
	<html>
		<body>
			<ul>
				<li><a href=\"/chapter/1\">Chapter 1</a></li>
				<li><a href=\"/chapter/2\">Chapter 2</a></li>
			</ul>
		</body>
	</html>
	"""


@pytest.fixture
def sample_cover_image(tmp_path):
    cover_path = tmp_path / "sample_cover.jpg"
    cover_path.write_bytes(b"\xff\xd8\xff\xe0" + b"fake jpg data")
    return cover_path


class TestNovelRepositoryConstructor:
    def test_constructor_does_not_create_directories_by_default(self, temp_novel_dir):
        repository = NovelRepository(temp_novel_dir)

        assert repository.novel_base_dir.exists() is False
        assert repository.novel_data_dir.exists() is False
        assert repository.novel_chapters_dir.exists() is False
        assert repository.novel_toc_dir.exists() is False

    def test_initialize_directories_creates_directories(self, temp_novel_dir):
        repository = NovelRepository(temp_novel_dir)

        repository.initialize_directories()

        assert repository.novel_base_dir.exists()
        assert repository.novel_data_dir.exists()
        assert repository.novel_chapters_dir.exists()
        assert repository.novel_toc_dir.exists()


class TestNovelData:
    def test_save_novel_data_success(self, novel_repository, sample_novel):
        novel_repository.save_novel_data(sample_novel)

        assert novel_repository.novel_json_file.exists()
        with open(novel_repository.novel_json_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        assert saved_data == Novel.to_dict(sample_novel)

    def test_save_novel_data_overwrites_existing(self, novel_repository, sample_novel):
        novel_repository.save_novel_data(sample_novel)

        new_novel = Novel(
            title="New Title",
            toc_main_url="https://example.com/new/toc",
            host="example.com",
        )
        novel_repository.save_novel_data(new_novel)

        with open(novel_repository.novel_json_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        assert saved_data == Novel.to_dict(new_novel)

    def test_load_novel_data_success(self, novel_repository, sample_novel):
        novel_repository.save_novel_data(sample_novel)

        loaded_novel = novel_repository.load_novel_data()
        assert loaded_novel == sample_novel

    def test_load_novel_data_from_existing_file(self, temp_novel_dir, sample_novel):
        novel_data_path = temp_novel_dir / "data"
        novel_data_path.mkdir(parents=True, exist_ok=True)
        json_data_path = novel_data_path / "main.json"
        json_data_path.write_text(
            json.dumps(Novel.to_dict(sample_novel), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        repository = NovelRepository(temp_novel_dir)
        loaded_novel = repository.load_novel_data()
        assert loaded_novel == sample_novel

    def test_load_novel_data_nonexistent_raises_error(self, novel_repository):
        with pytest.raises(NovelDataNotFoundError):
            novel_repository.load_novel_data()

    def test_load_novel_data_empty_file_raises_error(self, novel_repository):
        novel_repository.novel_json_file.write_text("{}", encoding="utf-8")

        with pytest.raises(NovelDataNotFoundError):
            novel_repository.load_novel_data()

    def test_load_novel_data_invalid_json_raises_error(self, novel_repository):
        novel_repository.novel_json_file.write_text(
            "{ invalid json }", encoding="utf-8"
        )

        with pytest.raises(LoadNovelDataError):
            novel_repository.load_novel_data()

    def test_load_novel_data_invalid_format_raises_error(self, novel_repository):
        novel_repository.novel_json_file.write_bytes(b"{ invalid json }")

        with pytest.raises(LoadNovelDataError):
            novel_repository.load_novel_data()


class TestChapterOperations:
    def test_save_chapter_html_success(self, novel_repository):
        chapter_content = "<h1>Chapter 1</h1><p>Content here</p>"
        novel_repository.save_chapter_html("chapter_1.html", chapter_content)

        chapter_path = novel_repository.novel_chapters_dir / "chapter_1.html"
        assert chapter_path.exists()
        assert chapter_path.read_text(encoding="utf-8") == chapter_content

    def test_chapter_file_exists_returns_true_when_exists(self, novel_repository):
        chapter_file = "chapter_1.html"
        novel_repository.save_chapter_html(chapter_file, "<p>Content</p>")

        assert novel_repository.chapter_file_exists(chapter_file) is True

    def test_chapter_file_exists_returns_false_when_not_exists(self, novel_repository):
        assert novel_repository.chapter_file_exists("nonexistent.html") is False

    def test_chapter_file_exists_returns_false_when_invalid(self, novel_repository):
        dir_path = novel_repository.novel_chapters_dir / "invalid_dir"
        dir_path.mkdir(parents=True, exist_ok=True)
        assert novel_repository.chapter_file_exists("invalid_dir") is False

    def test_load_chapter_html_success(self, novel_repository):
        chapter_content = "<h1>Chapter 1</h1><p>Content here</p>"
        novel_repository.save_chapter_html("chapter_1.html", chapter_content)

        loaded_content = novel_repository.load_chapter_html("chapter_1.html")
        assert loaded_content == chapter_content

    def test_load_chapter_html_nonexistent_raises_error(self, novel_repository):
        with pytest.raises(ChapterFileNotFoundError):
            novel_repository.load_chapter_html("nonexistent.html")

    def test_load_empty_chapter_raises_error(self, novel_repository):
        chapter_path = novel_repository.novel_chapters_dir / "empty.html"
        chapter_path.write_text("", encoding="utf-8")

        with pytest.raises(ChapterFileIsEmptyError):
            novel_repository.load_chapter_html("empty.html")

    def test_delete_chapter_html_success(self, novel_repository):
        novel_repository.save_chapter_html("chapter_1.html", "<p>Content</p>")
        novel_repository.delete_chapter_html("chapter_1.html")

        assert not novel_repository.chapter_file_exists("chapter_1.html")

    def test_delete_nonexistent_chapter_does_nothing(self, novel_repository):
        novel_repository.delete_chapter_html("nonexistent.html")

    def test_save_multiple_chapters(self, novel_repository):
        for i in range(1, 6):
            content = f"<p>Chapter {i} content</p>"
            novel_repository.save_chapter_html(f"chapter_{i}.html", content)

        for i in range(1, 6):
            assert novel_repository.chapter_file_exists(f"chapter_{i}.html")


class TestCoverImageOperations:
    def test_save_novel_cover_success(self, novel_repository, sample_cover_image):
        novel_repository.save_novel_cover(str(sample_cover_image))

        assert novel_repository.novel_cover_file.exists()

    def test_load_novel_cover_success(self, novel_repository, sample_cover_image):
        novel_repository.save_novel_cover(str(sample_cover_image))
        loaded_cover = novel_repository.load_novel_cover()

        assert loaded_cover is not None
        assert isinstance(loaded_cover, bytes)
        assert len(loaded_cover) > 0

    def test_load_novel_cover_nonexistent_raises_error(self, novel_repository):
        with pytest.raises(CoverImageNotFoundError):
            novel_repository.load_novel_cover()

    def test_save_cover_from_nonexistent_path_raises_error(self, novel_repository):
        with pytest.raises(SaveNovelDataError):
            novel_repository.save_novel_cover("/nonexistent/path/cover.jpg")

    def test_load_empty_cover_raises_error(self, novel_repository):
        novel_repository.novel_cover_file.write_bytes(b"")
        with pytest.raises(CoverImageFileIsEmptyError):
            novel_repository.load_novel_cover()


class TestTOCFragmentOperations:
    def test_add_toc_fragment_success(self, novel_repository, sample_html_content):
        novel_repository.add_toc_fragment(sample_html_content)

        toc_file = novel_repository.novel_toc_dir / "toc_0.html"
        assert toc_file.exists()
        assert toc_file.read_text(encoding="utf-8") == sample_html_content

    def test_add_multiple_toc_fragments(self, novel_repository, sample_html_content):
        for _ in range(1, 4):
            novel_repository.add_toc_fragment(sample_html_content)

        for i in range(0, 3):
            toc_file = novel_repository.novel_toc_dir / f"toc_{i}.html"
            assert toc_file.exists()

    def test_get_toc_fragment_success(self, novel_repository, sample_html_content):
        novel_repository.add_toc_fragment(sample_html_content)
        retrieved_content = novel_repository.get_toc_fragment(0)

        assert retrieved_content == sample_html_content

    def test_get_toc_fragment_nonexistent_raises_error(self, novel_repository):
        with pytest.raises(TOCFragmentNotFoundError):
            novel_repository.get_toc_fragment(999)

    def test_get_all_toc_fragments_success(self, novel_repository):
        contents = ["<html>Page 1</html>", "<html>Page 2</html>", "<html>Page 3</html>"]

        for content in contents:
            novel_repository.add_toc_fragment(content)

        all_fragments = novel_repository.get_all_toc_fragments()
        assert len(all_fragments) == 3
        assert all_fragments == contents

    def test_get_all_toc_fragments_empty_dir(self, novel_repository):
        all_fragments = novel_repository.get_all_toc_fragments()
        assert all_fragments == []

    def test_delete_toc_fragment_success(self, novel_repository, sample_html_content):
        novel_repository.add_toc_fragment(sample_html_content)
        novel_repository.add_toc_fragment(sample_html_content)

        novel_repository.delete_toc_fragment(1)

        toc_file = novel_repository.novel_toc_dir / "toc_1.html"
        assert not toc_file.exists()

    def test_delete_toc_fragment_nonexistent_does_not_raise(self, novel_repository):
        novel_repository.delete_toc_fragment(999)

    def test_delete_latest_toc_fragment_success(
        self, novel_repository, sample_html_content
    ):
        novel_repository.add_toc_fragment(sample_html_content)
        novel_repository.add_toc_fragment(sample_html_content)
        novel_repository.add_toc_fragment(sample_html_content)

        novel_repository.delete_latest_toc_fragment()

        assert not (novel_repository.novel_toc_dir / "toc_2.html").exists()
        assert (novel_repository.novel_toc_dir / "toc_0.html").exists()
        assert (novel_repository.novel_toc_dir / "toc_1.html").exists()

    def test_delete_latest_toc_fragment_when_only_one_exists(
        self, novel_repository, sample_html_content
    ):
        novel_repository.add_toc_fragment(sample_html_content)
        novel_repository.delete_latest_toc_fragment()

        assert not (novel_repository.novel_toc_dir / "toc_0.html").exists()

    def test_delete_latest_toc_fragment_empty_dir(self, novel_repository):
        novel_repository.delete_latest_toc_fragment()

    def test_delete_all_toc_fragments_success(
        self, novel_repository, sample_html_content
    ):
        novel_repository.add_toc_fragment(sample_html_content)
        novel_repository.add_toc_fragment(sample_html_content)
        novel_repository.add_toc_fragment(sample_html_content)

        novel_repository.delete_all_toc_fragments()

        assert (novel_repository.novel_toc_dir / "toc_0.html").exists() is False
        assert (novel_repository.novel_toc_dir / "toc_1.html").exists() is False
        assert (novel_repository.novel_toc_dir / "toc_2.html").exists() is False

    def test_delete_all_toc_fragments_empty_dir(self, novel_repository):
        novel_repository.delete_all_toc_fragments()


class TestTOCMetadata:
    def test_get_toc_last_updated_after_add(
        self, novel_repository, sample_html_content
    ):
        novel_repository.add_toc_fragment(sample_html_content)

        last_updated = novel_repository.get_toc_last_updated()
        assert last_updated is not None
        assert isinstance(last_updated, str)

        datetime.fromisoformat(last_updated)

    def test_get_toc_last_updated_no_metadata(self, novel_repository):
        last_updated = novel_repository.get_toc_last_updated()
        assert last_updated is None

    def test_metadata_file_is_json(self, novel_repository, sample_html_content):
        novel_repository.add_toc_fragment(sample_html_content)

        metadata_file = novel_repository.novel_toc_metadata_file
        assert metadata_file.exists()

        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        assert "last_updated" in metadata

    def test_metadata_updated_on_multiple_adds(
        self, novel_repository, sample_html_content
    ):
        novel_repository.add_toc_fragment(sample_html_content)
        first_update = novel_repository.get_toc_last_updated()

        novel_repository.add_toc_fragment(sample_html_content)
        second_update = novel_repository.get_toc_last_updated()

        assert datetime.fromisoformat(second_update) >= datetime.fromisoformat(
            first_update
        )


class TestEdgeCases:
    def test_toc_indices_are_sequential(self, novel_repository, sample_html_content):
        for _ in range(1, 6):
            novel_repository.add_toc_fragment(sample_html_content)

        for i in range(0, 5):
            assert (novel_repository.novel_toc_dir / f"toc_{i}.html").exists()

    def test_toc_index_continues_after_deletion(
        self, novel_repository, sample_html_content
    ):
        novel_repository.add_toc_fragment(sample_html_content)
        novel_repository.add_toc_fragment(sample_html_content)
        novel_repository.delete_toc_fragment(0)

        novel_repository.add_toc_fragment(sample_html_content)

        assert (novel_repository.novel_toc_dir / "toc_2.html").exists()
        assert not (novel_repository.novel_toc_dir / "toc_0.html").exists()

    def test_large_html_content_in_toc(self, novel_repository):
        large_content = "<html>" + "<li><a href='#'>Item</a></li>" * 10000 + "</html>"
        novel_repository.add_toc_fragment(large_content)

        retrieved = novel_repository.get_toc_fragment(0)
        assert retrieved == large_content

    def test_special_characters_in_html(self, novel_repository):
        special_content = """
		<html>
			<body>
				<p>Spécial çháracters: 中文 日本語 한국어</p>
				<p>Symbols: © ® ™ € £ ¥</p>
			</body>
		</html>
		"""
        novel_repository.add_toc_fragment(special_content)

        retrieved = novel_repository.get_toc_fragment(0)
        assert retrieved == special_content

    def test_mixed_operations(
        self, novel_repository, sample_novel, sample_cover_image, sample_html_content
    ):
        novel_repository.save_novel_data(sample_novel)
        novel_repository.save_novel_cover(str(sample_cover_image))

        novel_repository.save_chapter_html("ch1.html", "<p>Chapter 1</p>")
        novel_repository.save_chapter_html("ch2.html", "<p>Chapter 2</p>")

        novel_repository.add_toc_fragment(sample_html_content)
        novel_repository.add_toc_fragment(sample_html_content)

        assert novel_repository.novel_json_file.exists()
        assert novel_repository.novel_cover_file.exists()
        assert novel_repository.chapter_file_exists("ch1.html")
        assert novel_repository.chapter_file_exists("ch2.html")
        assert (novel_repository.novel_toc_dir / "toc_0.html").exists()
        assert (novel_repository.novel_toc_dir / "toc_1.html").exists()
