import os
import json

from appdirs import AppDirs
from pathlib import Path
import shutil
from dotenv import load_dotenv
from ebooklib import epub

import custom_logger

load_dotenv()

app_author = "ImagineBrkr"
app_name = "web-novel-scrapper"

dirs = AppDirs(app_name, app_author)

CURRENT_DIR = Path(__file__).resolve().parent

SCRAPPER_BASE_CONFIG_DIR = os.getenv(
    'SCRAPPER_BASE_CONFIG_DIR', dirs.user_config_dir)
SCRAPPER_BASE_DATA_DIR = os.getenv(
    'SCRAPPER_BASE_DATA_DIR', dirs.user_data_dir)

logger = custom_logger.create_logger('FILE MANAGER')

class FileManager:
    novel_base_dir: Path
    novel_data_dir: Path
    novel_config_dir: Path
    novel_chapters_dir: Path

    novel_json_filepath: Path
    novel_cover_filepath: Path

    novel_json_filename: str = "main.json"
    novel_cover_filename: str = "cover.jpg"
    toc_preffix: str = "toc"

    def __init__(self,
                 novel_title: str,
                 novel_base_dir: str = None,
                 novel_config_dir: str = None):
        novel_base_dir = novel_base_dir if novel_base_dir else f'{
            SCRAPPER_BASE_DATA_DIR}/{novel_title}'
        novel_config_dir = novel_config_dir if novel_config_dir else f'{
            SCRAPPER_BASE_CONFIG_DIR}/{novel_title}'

        self.novel_base_dir = _create_path_if_not_exists(novel_base_dir)
        self.novel_data_dir = _create_path_if_not_exists(
            f'{novel_base_dir}/data')

        self.novel_chapters_dir = _create_path_if_not_exists(
            f'{novel_base_dir}/data/chapters')

        self.novel_config_dir = _create_path_if_not_exists(novel_config_dir)

        self.novel_json_filepath = self.novel_data_dir / self.novel_json_filename
        self.novel_cover_filepath = self.novel_data_dir / self.novel_cover_filename

    def save_chapter_html(self, filename: str, content: str):
        full_path = self.novel_chapters_dir / filename
        _save_content_to_file(full_path, content)

    def load_chapter_html(self, filename: str):
        full_path = self.novel_chapters_dir / filename
        if full_path.exists():
            return _read_content_from_file(full_path)
        return None

    def delete_chapter_html(self, filename: str):
        full_path = self.novel_chapters_dir / filename

        if full_path.exists():
            _delete_file(full_path)

    def save_novel_json(self, novel_data: dict):
        _save_content_to_file(self.novel_json_filepath, novel_data, json=True)

    def load_novel_json(self):
        if self.novel_json_filepath.exists():
            return _read_content_from_file(self.novel_json_filepath)

    def save_novel_cover(self, source_cover_path: str):
        source_cover_path = Path(source_cover_path)
        if source_cover_path.exists():
            _copy_file(source_cover_path, self.novel_cover_filepath)

    def load_novel_cover(self):
        if self.novel_cover_filepath.exists():
            return _read_content_from_file(self.novel_cover_filepath, bytes=True)

    def clear_toc(self):
        toc_pos = 0
        toc_exists = True
        while toc_exists:
            toc_filename = f"{self.toc_preffix}_{toc_pos}.html"
            toc_path = self.novel_data_dir / toc_filename
            toc_exists = toc_path.exists()
            if toc_exists:
                _delete_file(toc_path)

    def add_toc(self, content: str):
        toc_pos = 0
        toc_exists = True
        while toc_exists:
            toc_filename = f"{self.toc_preffix}_{toc_pos}.html"
            toc_path = self.novel_data_dir / toc_filename
            toc_exists = toc_path.exists()
            if toc_exists:
                toc_pos += 1
        _save_content_to_file(toc_path, content)

    def get_toc(self, pos_idx: int):
        toc_filename = f"{self.toc_preffix}_{pos_idx}.html"
        toc_path = self.novel_data_dir / toc_filename
        return _read_content_from_file(toc_path)

    def get_all_toc(self):
        pos = 0
        tocs = []
        while True:
            toc_content = self.get_toc(pos)
            if toc_content:
                tocs.append(toc_content)
                pos += 1
            else:
                return tocs

    def save_book(self, book: epub.EpubBook, filename: str) -> bool:
        book_path = self.novel_base_dir / filename
        try:            
            # Write epub file
            epub.write_epub(str(book_path), book)
            logger.info(f'Book saved successfully to {book_path}')
            return True
            
        except PermissionError as e:
            logger.error(f'Permission denied when saving book to {book_path}: {e}')
            return False
        except OSError as e:
            logger.error(f'OS error when saving book to {book_path}: {e}')
            return False
        except Exception as e:
            logger.error(f'Unexpected error saving book to {book_path}: {e}', 
                        exc_info=True)
            return False

def _create_path_if_not_exists(dir_path: str) -> Path:
    try:
        dir_path = Path(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    except OSError as e:
        logger.error(f"Error with directory creation: {e}")
        # Change this to raise for debugging
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise


def _save_content_to_file(filepath: Path, content: str | dict, json: bool = False) -> None:
    try:
        if json:
            with open(filepath, 'w', encoding='utf-16') as file:
                json.dump(content, file, indent=2, ensure_ascii=False)
        else:
            with open(filepath, 'w', encoding='UTF-16') as file:
                file.write(content)
        logger.info(f'File saved successfully: {filepath}')
    except (OSError, IOError) as e:
        logger.error(f'Error saving file "{filepath}": {e}')
    except Exception as e:
        logger.error(f'Unexpected error saving file "{
                     filepath}": {e}', exc_info=True)


def _read_content_from_file(filepath: Path, bytes: bool = False) -> str:
    try:
        # Read the file
        read_mode = 'rb' if bytes else 'r'
        with open(filepath, read_mode, encoding='UTF-16') as file:
            content = file.read()
        logger.info(f'File read successfully: {filepath}')
        return content
    except FileNotFoundError as e:
        # Log if the file doesn't exist
        logger.error(f'File not found: "{filepath}": {e}')
    except (OSError, IOError) as e:
        logger.error(f'Error reading file "{filepath}": {e}')
    except Exception as e:
        # Log for unexpected errors
        logger.error(f'Unexpected error reading file "{
                     filepath}": {e}', exc_info=True)


def _delete_file(filepath: Path) -> None:
    try:
        # Delete the file
        filepath.unlink()  # Remove the file
        logger.info(f'File deleted successfully: {filepath}')
    except FileNotFoundError as e:
        # Log if the file doesn't exist
        logger.error(f'File not found for deletion: "{filepath}": {e}')
    except (OSError, IOError) as e:
        # Log errors related to file system operations
        logger.error(f'Error deleting file "{filepath}": {e}')
    except Exception as e:
        # Log any unexpected errors
        logger.error(f'Unexpected error deleting file "{
                     filepath}": {e}', exc_info=True)


def _copy_file(source: Path, destination: Path) -> None:
    try:
        # Copy the file
        shutil.copy(source, destination)
        logger.info(f'File copied successfully from {source} to {destination}')

    except FileNotFoundError:
        logger.error(f'Source file not found: {source}')
    except PermissionError as e:
        logger.error(f'Permission denied when copying file: {e}')
    except shutil.SameFileError:
        logger.warning(f'Source and destination are the same file: {source}')
    except Exception as e:
        logger.error(f'Unexpected error copying file from {source} to {destination}: {e}',
                     exc_info=True)
