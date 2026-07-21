import pytest

from web_novel_scraper.exceptions import (
    InvalidNovelDefinitionError,
    InvalidNovelDefinitionInRegistryFileError,
    NovelNotFoundInNovelsRootDirError,
)
from web_novel_scraper.persistence.novel_registry import NovelRegistry


@pytest.fixture
def novels_root_dir(tmp_path):
    return tmp_path / "novels"


@pytest.fixture
def registry_file(novels_root_dir):
    novels_root_dir.mkdir(parents=True, exist_ok=True)
    return novels_root_dir / "meta.json"


@pytest.fixture
def novel_registry(novels_root_dir):
    return NovelRegistry(novels_root_dir)


class TestNovelRegistryList:
    def test_list_returns_empty_when_registry_file_does_not_exist(self, novel_registry):
        result = novel_registry.list()

        assert result == []

    def test_list_returns_only_allocated_novel_base_dirs(self, novel_registry):
        novel_one_base_dir = novel_registry.allocate_from_title("Novel 1")
        novel_two_base_dir = novel_registry.allocate_from_title("Novel 2")
        result = novel_registry.list()

        assert set(result) == {novel_one_base_dir, novel_two_base_dir}


class TestNovelRegistryFindByTitle:
    def test_find_by_title_returns_allocated_novel_base_dir(self, novel_registry):
        novel_base_dir = novel_registry.allocate_from_title("My Novel")
        result = novel_registry.find_by_title("My Novel")

        assert result == novel_base_dir

    def test_find_by_title_raises_when_title_does_not_exist(self, novel_registry):
        novel_registry.allocate_from_title("Other Novel")
        with pytest.raises(NovelNotFoundInNovelsRootDirError) as exc_info:
            novel_registry.find_by_title("Missing Novel")

        assert "Missing Novel" in str(exc_info.value)
        assert "meta.json" in str(exc_info.value)

    def test_find_by_title_raises_for_invalid_novel_definition(
        self, registry_file, novel_registry
    ):
        registry_file.write_text(
            '{"My Novel": {"novel_base_dir": ""}}', encoding="utf-8"
        )
        with pytest.raises(InvalidNovelDefinitionInRegistryFileError) as exc_info:
            novel_registry.find_by_title("My Novel")

        assert "novel_base_dir" in str(exc_info.value)


class TestNovelRegistryAllocateFromTitle:
    def test_allocate_from_title_creates_registry_file_and_registers_entry(
        self, novel_registry, novels_root_dir
    ):
        novel_base_dir = novel_registry.allocate_from_title("Saved Novel")

        meta_file = novels_root_dir / "meta.json"
        assert meta_file.exists()
        assert novel_registry.find_by_title("Saved Novel") == novel_base_dir
        assert novel_base_dir == str(novels_root_dir / "Saved Novel")

    def test_allocate_from_title_overwrites_existing_entry_when_base_dir_already_exists(
        self, novel_registry, novels_root_dir
    ):
        first_novel_base_dir = novel_registry.allocate_from_title("Novel")
        (novels_root_dir / "Novel").mkdir(parents=True, exist_ok=True)

        second_novel_base_dir = novel_registry.allocate_from_title("Novel")

        assert second_novel_base_dir == str(novels_root_dir / "Novel_1")
        assert second_novel_base_dir != first_novel_base_dir
        assert novel_registry.find_by_title("Novel") == second_novel_base_dir

    def test_allocate_from_title_raises_for_empty_title(self, novel_registry):
        with pytest.raises(InvalidNovelDefinitionError) as exc_info:
            novel_registry.allocate_from_title("   ")

        assert "title" in str(exc_info.value)
