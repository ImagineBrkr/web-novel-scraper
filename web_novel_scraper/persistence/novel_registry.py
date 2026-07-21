from pathlib import Path
# import unicodedata

from web_novel_scraper.logger_manager import create_logger
from web_novel_scraper.io_helpers.utils import IOUtils
from web_novel_scraper.exceptions import (
    IOUtilsError,
    InvalidNovelDefinitionError,
    InvalidNovelDefinitionInRegistryFileError,
    InvalidNovelRegistryFileError,
    InvalidNovelsRootDirError,
    NovelNotFoundInNovelsRootDirError,
    FileNotFoundCustomError,
    EmptyFileError,
)

logger = create_logger(__name__)


class NovelRegistry:
    REGISTRY_FILENAME = "meta.json"

    def __init__(self, novels_root_dir: str | Path):
        try:
            self.novels_root_dir = IOUtils._normalize_path(novels_root_dir)
            self.registry_file_path = IOUtils.get_path_in_dir(
                self.novels_root_dir, self.REGISTRY_FILENAME
            )
        except IOUtilsError as e:
            raise InvalidNovelsRootDirError(
                f"Invalid novels root directory '{novels_root_dir}': {str(e)}"
            ) from e

    def list(self) -> list[str]:
        novels_registry = self._load_novels_registry()
        novel_base_dirs: list[str] = []

        for title, novel_definition in novels_registry.items():
            try:
                novel_base_dir = self._get_novel_base_dir_from_definition(
                    novel_definition
                )
            except InvalidNovelDefinitionInRegistryFileError as e:
                logger.warning(
                    f"Invalid definition for title '{title}' in registry file '{self.registry_file_path}': {str(e)}"
                )
                continue

            novel_base_dirs.append(novel_base_dir)

        return novel_base_dirs

    def find_by_title(self, title: str) -> str:
        logger.debug(
            f"Looking for novel '{title}' in novels root dir '{self.novels_root_dir}'"
        )
        novels_registry = self._load_novels_registry()

        if title not in novels_registry:
            raise NovelNotFoundInNovelsRootDirError(
                f"Novel '{title}' not found in novels registry file '{self.registry_file_path}'."
            )

        novel_definition = novels_registry[title]
        novel_base_dir = self._get_novel_base_dir_from_definition(novel_definition)

        logger.debug(f"Found novel base directory for '{title}': {novel_base_dir}")
        return novel_base_dir

    def allocate_from_title(self, title: str) -> str:
        if not title.strip():
            raise InvalidNovelDefinitionError(
                "Cannot save registry entry: title must be a non-empty string."
            )

        novel_base_dir = self._generate_novel_base_dir(title)
        novels_registry = self._load_novels_registry()

        n = 1
        while IOUtils.dir_exists(novel_base_dir):
            novel_base_dir = self._generate_novel_base_dir(f"{title}_{n}")
            n += 1

        if novels_registry.get(title) is not None:
            logger.debug(f"Overwriting existing registry entry for novel '{title}'.")

        novels_registry[title] = {"novel_base_dir": novel_base_dir}
        self._save_novels_registry(novels_registry)
        return novel_base_dir

    def _generate_novel_base_dir(self, title: str) -> str:
        clean_title = IOUtils.sanitize_name_to_valid_path(title)
        try:
            return str(IOUtils.get_path_in_dir(self.novels_root_dir, clean_title))
        except IOUtilsError as e:
            raise InvalidNovelsRootDirError(
                f"Cannot build novel directory for title '{title}' inside '{self.novels_root_dir}': {str(e)}"
            ) from e

    def _save_novels_registry(self, novels_registry: dict) -> None:
        try:
            IOUtils.ensure_dir(self.novels_root_dir)
            IOUtils.save_json_file(path=self.registry_file_path, data=novels_registry)
        except IOUtilsError as e:
            raise InvalidNovelRegistryFileError(
                f"Failed to save novels registry file '{self.registry_file_path}': {str(e)}"
            ) from e

    def _get_novel_base_dir_from_definition(self, novel_definition: dict) -> str:
        if not isinstance(novel_definition, dict):
            raise InvalidNovelDefinitionInRegistryFileError(
                f"Invalid novel registry definition: expected an object, got {type(novel_definition).__name__}."
            )

        novel_base_dir = novel_definition.get("novel_base_dir")
        if not isinstance(novel_base_dir, str) or not novel_base_dir.strip():
            raise InvalidNovelDefinitionInRegistryFileError(
                "Invalid novel registry definition: field 'novel_base_dir' must be a non-empty string."
            )
        return novel_base_dir

    def _load_novels_registry(self) -> dict:
        try:
            if not IOUtils.dir_exists(self.novels_root_dir):
                logger.debug(
                    f"Novels root directory '{self.novels_root_dir}' does not exist."
                )
                return {}
        except IOUtilsError as e:
            raise InvalidNovelsRootDirError(
                f"Cannot access novels root directory '{self.novels_root_dir}': {str(e)}"
            ) from e

        try:
            novels_registry = IOUtils.read_json_file(
                path=self.registry_file_path, type=dict
            )
            logger.debug(f"Found registry file at '{self.registry_file_path}'")
        except EmptyFileError:
            logger.debug(f"Registry file '{self.registry_file_path}' is empty.")
            return {}
        except FileNotFoundCustomError:
            logger.debug(f"Registry file '{self.registry_file_path}' not found.")
            return {}
        except IOUtilsError as e:
            raise InvalidNovelRegistryFileError(
                f"Failed to read registry file '{self.registry_file_path}': {str(e)}"
            ) from e

        return novels_registry
