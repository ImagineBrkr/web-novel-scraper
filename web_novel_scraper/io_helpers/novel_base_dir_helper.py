from typing import Optional
from pathlib import Path

from web_novel_scraper.logger_manager import create_logger
from web_novel_scraper.io_helpers.utils import IOUtils
from web_novel_scraper.exceptions import (
    InvalidNovelBaseDirError,
    InvalidMetaFileError,
    FileNotFoundCustomError,
    IOUtilsError,
    EmptyFileError,
)

logger = create_logger(__name__)


class NovelBaseDirHelper:
    @staticmethod
    def get_novel_base_dir_from_meta(
        title: str,
        base_novels_dir: str,
    ) -> str | None:
        logger.debug(f"Looking for novel {title} in Base Novels Dir {base_novels_dir}")
        meta_data = NovelBaseDirHelper._get_base_novels_dir_meta_data(base_novels_dir)

        if title in meta_data:
            novel_base_dir = meta_data[title].get("novel_base_dir")
            if novel_base_dir is None:
                logger.debug(
                    f'Found "{title}" in Meta.json File but "novel_base_dir" is empty, file may be corrupted.'
                )
                return None

            logger.debug(
                f"Found Novel Directory in Meta.json for novel {title}: {novel_base_dir}"
            )
            return novel_base_dir

        else:
            logger.debug(
                f"Title '{title}' not found in Meta.json file: {base_novels_dir}."
            )
            return None

    def save_novel_dir_to_meta(
        title: str, novel_base_dir: str, base_novels_dir: str
    ) -> None:

        meta_data = NovelBaseDirHelper._get_base_novels_dir_meta_data(base_novels_dir)
        meta_data[title] = {"novel_base_dir": novel_base_dir}

        try:
            IOUtils.ensure_dir(base_novels_dir)

        except IOUtilsError as e:
            raise InvalidNovelBaseDirError(
                f"Failed to create Base Novels Directory: {e}"
            ) from e

        meta_file_path = NovelBaseDirHelper._get_base_novels_dir_meta_data_path(
            base_novels_dir
        )

        try:
            IOUtils.save_json_file(path=meta_file_path, data=meta_data)

        except IOUtilsError as e:
            raise InvalidNovelBaseDirError(
                f"Failed to save novel base directory to meta.json: {e}"
            ) from e

    @staticmethod
    def generate_novel_base_dir(title: str, base_novels_dir: str) -> str:
        clean_title = IOUtils.sanitize_dirname(title)
        try:
            novel_base_dir = str(IOUtils.get_path_in_dir(base_novels_dir, clean_title))
        except IOUtilsError as e:
            raise InvalidNovelBaseDirError(f"Invalid Novel Base Dir: {e}") from e
        return novel_base_dir

    @staticmethod
    def delete_novel_base_dir(novel_base_dir: str) -> None:
        pass

    @staticmethod
    def _get_base_novels_dir_meta_data_path(base_novels_dir: str) -> Path:
        return IOUtils.get_path_in_dir(base_novels_dir, "meta.json")

    @staticmethod
    def _get_base_novels_dir_meta_data(base_novels_dir: str) -> Optional[dict]:
        try:
            if not IOUtils.dir_exists(base_novels_dir):
                logger.debug(f"Base Novels Directory {base_novels_dir} does not exist.")
                return {}

        except IOUtilsError as e:
            raise InvalidNovelBaseDirError(e) from e

        meta_file_path = NovelBaseDirHelper._get_base_novels_dir_meta_data_path(
            base_novels_dir
        )

        try:
            meta_data = IOUtils.read_json_file(path=meta_file_path, type=dict)
            logger.debug(f"Found Meta.json File at {meta_file_path}")
        except EmptyFileError:
            logger.debug(f"Meta.json File is empty: {meta_file_path}")
            return {}
        except FileNotFoundCustomError:
            logger.debug(f"Meta.json file not foun: {meta_file_path}")
            return {}
        except IOUtilsError as e:
            raise InvalidMetaFileError(
                f"Failed to read meta.json File for Base Novels Directory: {e}"
            ) from e

        return meta_data
