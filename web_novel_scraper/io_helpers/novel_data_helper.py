from pathlib import Path
from datetime import datetime, timezone
# import unicodedata

from web_novel_scraper.logger_manager import create_logger
from web_novel_scraper.io_helpers.utils import IOUtils
from web_novel_scraper.exceptions import (
    IOUtilsError,
    ChapterFileNotFoundError,
    LoadNovelDataError,
    DeleteNovelDataError,
    SaveNovelDataError,
    InvalidNovelDataError,
    TOCFragmentNotFoundError,
    EmptyDirError,
    CoverImageNotFoundError,
    FileNotFoundCustomError,
    EmptyFileError,
    ChapterFileIsEmptyError,
    CoverImageFileIsEmptyError,
    TOCFragmentFileIsEmptyError,
    NovelDataNotFoundError,
    InvalidNovelDataDirError,
)

NOVEL_JSON_FILENAME = "main.json"
NOVEL_COVER_FILENAME = "cover.jpg"

logger = create_logger(__name__)


class NovelDataHelper:
    """
    Helper Class with functions for handling novel-related file operations.

    Manages all file operations related to novels including chapters, table of contents,
    cover images, and metadata.

    Attributes:
        novel_base_dir (Path): Base directory for the novel
        novel_data_dir (Path): Directory for novel data
        novel_chapters_dir (Path): Directory for chapters
        novel_toc_dir (Path): Directory for table of contents
        novel_json_file (Path): Main JSON file
        novel_cover_file (Path): Cover image file
    """

    novel_base_dir: Path
    novel_data_dir: Path
    novel_chapters_dir: Path
    novel_toc_dir: Path
    novel_toc_metadata_file: Path

    novel_json_file: Path
    novel_cover_file: Path

    def __init__(self, novel_base_dir: Path | str):

        try:
            self.novel_base_dir = IOUtils._normalize_path(novel_base_dir)
            self.novel_data_dir = self.novel_base_dir / "data"
            self.novel_chapters_dir = self.novel_data_dir / "chapters"
            self.novel_toc_dir = self.novel_data_dir / "toc"
            self.novel_toc_metadata_file = self.novel_toc_dir / "metadata.json"
            self.novel_json_file = self.novel_data_dir / NOVEL_JSON_FILENAME
            self.novel_cover_file = self.novel_data_dir / NOVEL_COVER_FILENAME

            logger.debug(
                f"Initializing data directories for Novel Base Dir {novel_base_dir}"
            )

            IOUtils.ensure_dir(self.novel_base_dir)
            IOUtils.ensure_dir(self.novel_data_dir)
            IOUtils.ensure_dir(self.novel_chapters_dir)
            IOUtils.ensure_dir(self.novel_toc_dir)

        except IOUtilsError as e:
            raise InvalidNovelDataDirError(e) from e

    @staticmethod
    def load_novel_data(novel_base_dir: Path | str) -> dict:
        try:
            novel_data_dir_path = IOUtils.get_path_in_dir(novel_base_dir, "data")
            novel_data_file_path = IOUtils.get_path_in_dir(
                novel_data_dir_path, "main.json"
            )
        except IOUtilsError as e:
            raise InvalidNovelDataError(f"Invalid Novel Base Dir: {e}") from e

        logger.debug(f"Trying to load Novel Data from File {novel_data_file_path}")

        try:
            novel_data = IOUtils.read_json_file(path=novel_data_file_path, type=dict)
            logger.debug(f"Loaded Novel Data from file {novel_data_file_path}")
        except EmptyFileError:
            raise NovelDataNotFoundError(
                f"Novel Data File is empty: {novel_data_file_path}"
            )
        except FileNotFoundCustomError:
            raise NovelDataNotFoundError(
                f"Novel Data File not found: {novel_data_file_path}"
            )
        except IOUtilsError as e:
            raise LoadNovelDataError(
                f"Could not load Novel Data File {novel_data_file_path}: {str(e)}"
            ) from e

        return novel_data

    def save_novel_data(self, novel_data: dict) -> None:

        if not isinstance(novel_data, dict):
            raise InvalidNovelDataError(
                f"Novel data is in invalid format, expected dictionary, got {type(novel_data).__name__}"
            )

        try:
            IOUtils.save_json_file(self.novel_json_file, novel_data)
            logger.info(f'Novel Data saved to file "{self.novel_json_file}".')
        except IOUtilsError as e:
            raise SaveNovelDataError(
                f"Could not save Novel Data to File {self.novel_json_file}: {str(e)}"
            ) from e

    # CHAPTERS

    def save_chapter_html(self, chapter_file: str, content: str) -> None:

        full_path = self.novel_chapters_dir / chapter_file
        logger.debug(f"Saving Chapter HTML to {full_path}")

        try:
            # content = unicodedata.normalize('NFKC', content)
            IOUtils.save_text_file(full_path, content)
        except IOUtilsError as e:
            raise SaveNovelDataError(
                f"Error saving Chapter HTML to File {chapter_file}: {str(e)}"
            ) from e

    def chapter_file_exists(self, chapter_file: str) -> bool:
        full_path = self.novel_chapters_dir / chapter_file
        return full_path.exists()

    def load_chapter_html(self, chapter_file: str) -> str:

        full_path = self.novel_chapters_dir / chapter_file
        try:
            chapter_content = IOUtils.read_text_file(full_path)

        except EmptyFileError:
            raise ChapterFileIsEmptyError(f"Chapter file is empty: {full_path}")

        except FileNotFoundCustomError:
            raise ChapterFileNotFoundError(f"Chapter file not found: {full_path}")

        except IOUtilsError as e:
            raise LoadNovelDataError(
                f"Couldn't load Chapter HTML from file {full_path}: {str(e)}"
            ) from e

        return chapter_content

    def delete_chapter_html(self, chapter_file: str) -> None:
        full_path = self.novel_chapters_dir / chapter_file

        try:
            IOUtils.delete_file(full_path)

        except IOUtilsError as e:
            raise DeleteNovelDataError(
                f"Error deleting Chapter HTML File {chapter_file}: {str(e)}"
            ) from e

    # COVER IMAGE

    def save_novel_cover(self, source_cover_path: str) -> None:

        try:
            IOUtils.copy_file(source_cover_path, self.novel_cover_file)
        except IOUtilsError as e:
            raise SaveNovelDataError(
                f"Error copying novel cover from {source_cover_path} to {self.novel_cover_file}: {str(e)}"
            ) from e

    def load_novel_cover(self) -> bytes:

        try:
            cover_image = IOUtils.read_binary_file(self.novel_cover_file)

        except EmptyFileError:
            raise CoverImageFileIsEmptyError(
                f"Cover image file is empty: {self.novel_cover_file}"
            )

        except FileNotFoundCustomError:
            raise CoverImageNotFoundError(
                f"Cover image not found in file {self.novel_cover_file}"
            )

        except IOUtilsError as e:
            raise LoadNovelDataError(
                f"Error loading novel cover image from file {self.novel_cover_file}: {str(e)}"
            ) from e

        return cover_image

    ## TOC API

    def add_toc_fragment(self, html_content: str) -> None:
        next_idx = self._latest_toc_idx() + 1
        toc_path = self.novel_toc_dir / f"toc_{next_idx}.html"

        self._add_toc_fragment_file(toc_path, html_content)
        logger.debug(f"Added TOC Fragment #{next_idx} to file {toc_path}")

    def delete_toc_fragment(self, idx: int) -> None:
        toc_path = self.novel_toc_dir / f"toc_{idx}.html"
        if not toc_path.exists():
            logger.warning(
                f"Tried to delete TOC Fragment from file {toc_path} but it does not exist."
            )
            return
        try:
            IOUtils.delete_file(toc_path)
        except IOUtilsError as e:
            raise DeleteNovelDataError(
                f"Error deleting TOC Fragment {toc_path}: {str(e)}"
            ) from e

        logger.debug(f"Deleted TOC Fragment #{idx} from file {toc_path}")

    def delete_all_toc_fragments(self) -> None:
        latest_idx = self._latest_toc_idx()

        if latest_idx == -1:
            logger.debug(f"No TOC Fragments to delete on {self.novel_toc_dir}")
            return

        for idx in range(0, latest_idx + 1):
            self.delete_toc_fragment(idx=idx)

    def delete_latest_toc_fragment(self) -> None:
        latest_idx = self._latest_toc_idx()
        if latest_idx == -1:
            logger.debug(f"No TOC Fragments to delete on {self.novel_toc_dir}")
            return

        self.delete_toc_fragment(idx=latest_idx)

    def get_toc_fragment(self, idx: int) -> str:

        toc_path = self.novel_toc_dir / f"toc_{idx}.html"
        return self._get_toc_fragment_content_from_file(toc_path)

    def get_all_toc_fragments(self) -> list[str]:

        contents: list[str] = []
        next_idx = self._latest_toc_idx() + 1
        if next_idx == 0:
            logger.debug(f"No TOC Fragments to retrieve on {self.novel_toc_dir}")
            return contents

        for idx in range(0, next_idx):
            toc_file = self.novel_toc_dir / f"toc_{idx}.html"
            html = self._get_toc_fragment_content_from_file(toc_file)
            contents.append(html)

        return contents

    def get_toc_last_updated(self) -> str | None:

        try:
            metadata = IOUtils.read_json_file(self.novel_toc_metadata_file, dict)
        except EmptyFileError or FileNotFoundCustomError:
            metadata = {}
        except IOUtilsError as e:
            logger.warning(f"Could not retrieve TOC Metadata file: {str(e)}")
            metadata = {}

        last_updated = metadata.get("last_updated")
        if not isinstance(last_updated, str):
            logger.warning(
                f"TOC Metadata File {self.novel_toc_metadata_file} is invalid"
            )
            return None
        return metadata.get("last_updated")

    def _add_toc_fragment_file(self, toc_file: Path, html_content: str) -> None:
        try:
            IOUtils.save_text_file(toc_file, html_content)
        except IOUtilsError as e:
            raise SaveNovelDataError(
                f"Error adding TOC fragment to {toc_file}: {str(e)}"
            ) from e

        self._update_toc_metadata()

    def _get_toc_fragment_content_from_file(self, toc_file: Path) -> str:
        try:
            toc_fragment_content = IOUtils.read_text_file(toc_file)

        except EmptyFileError:
            raise TOCFragmentFileIsEmptyError(f"TOC Fragment File is empty {toc_file}")

        except FileNotFoundCustomError:
            raise TOCFragmentNotFoundError(f"TOC Fragment not found: {toc_file}")

        except IOUtilsError as e:
            raise LoadNovelDataError(
                f"Error loading TOC Fragment Content from file {toc_file}: {str(e)}"
            ) from e

        return toc_fragment_content

    def _latest_toc_idx(self) -> int:
        try:
            toc_fragments = IOUtils.list_files_from_dir(
                self.novel_toc_dir, "toc_*.html"
            )
        except EmptyDirError:
            toc_fragments = []
        except IOUtilsError as e:
            raise LoadNovelDataError(
                f"Error accessing TOC directory {self.novel_toc_dir}"
            ) from e

        toc_idx = [int(p.stem.split("_")[1]) for p in toc_fragments]

        return max(toc_idx, default=-1)

    def _update_toc_metadata(self) -> None:
        now_iso = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        metadata = {"last_updated": now_iso}

        try:
            IOUtils.save_json_file(self.novel_toc_metadata_file, metadata)
        except IOUtilsError as e:
            logger.warning(f"Failed to update TOC Metadata: {str(e)}")
