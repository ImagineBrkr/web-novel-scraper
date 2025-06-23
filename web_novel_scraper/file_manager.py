import json

from pathlib import Path
from ebooklib import epub
from typing import Optional, Dict
import unicodedata

from .logger_manager import create_logger
from .utils import _normalize_dirname, FileOps, now_iso, FileManagerError

NOVEL_JSON_FILENAME = 'main.json'
NOVEL_COVER_FILENAME = 'cover.jpg'

logger = create_logger('FILE MANAGER')


class FileManager:
    novel_base_dir: Path
    novel_data_dir: Path
    novel_chapters_dir: Path
    novel_toc_dir: Path

    novel_json_file: Path
    novel_cover_file: Path = None

    def __init__(self,
                 title: str,
                 base_novels_dir: str,
                 novel_base_dir: str = None,
                 read_only: bool = False):
        logger.debug(f'Initializing FileManager for novel: {title}')
        self.novel_base_dir = self._get_novel_base_dir(title, base_novels_dir, novel_base_dir)
        logger.debug(f'Novel base dir: {self.novel_base_dir}')
        self.novel_data_dir = self.novel_base_dir / 'data'
        self.novel_chapters_dir = self.novel_data_dir / 'chapters'
        self.novel_toc_dir = self.novel_data_dir / "toc"
        self.novel_json_file = self.novel_data_dir / NOVEL_JSON_FILENAME
        self.novel_cover_file = self.novel_data_dir / NOVEL_COVER_FILENAME

        if not read_only:
            FileOps.ensure_dir(self.novel_base_dir)
            if novel_base_dir is None:
                self._store_novel_base_dir(title, self.novel_base_dir, base_novels_dir)
            FileOps.ensure_dir(self.novel_data_dir)
            FileOps.ensure_dir(self.novel_chapters_dir)
            FileOps.ensure_dir(self.novel_toc_dir)

    def save_chapter_html(self, chapter_filename: str, content: str) -> None:
        full_path = self.novel_chapters_dir / chapter_filename
        logger.debug(f'Saving chapter to {full_path}')
        content = unicodedata.normalize('NFKC', content)
        FileOps.save_text(full_path, content)

    def chapter_file_exists(self, chapter_filename: str) -> bool:
        full_path = self.novel_chapters_dir / chapter_filename
        return full_path.exists()

    def load_chapter_html(self, chapter_filename: str) -> Optional[str]:
        full_path = self.novel_chapters_dir / chapter_filename
        logger.debug(f'Loading chapter from {full_path}')
        chapter_content = FileOps.read_text(full_path)
        if not chapter_content:
            logger.debug(f'Chapter content not found: {chapter_filename}')
        return chapter_content

    def delete_chapter_html(self, chapter_filename: str) -> None:
        full_path = self.novel_chapters_dir / chapter_filename
        logger.debug(f'Attempting to delete chapter: {chapter_filename}')
        FileOps.delete(full_path)

    def save_novel_json(self, novel_data: dict) -> None:
        logger.debug(f'Saving novel data to {self.novel_json_file}')
        FileOps.save_json(self.novel_json_file, novel_data)

    def load_novel_json(self) -> Optional[str]:
        logger.debug(f'Loading novel data from {self.novel_json_file}')
        novel_json = FileOps.read_text(self.novel_json_file)
        if novel_json is None:
            logger.debug('Could not read novel JSON file')
        return novel_json

    def save_novel_cover(self, source_cover_path: str) -> None:
        source_cover_path = Path(source_cover_path)
        logger.debug(f'Attempting to save cover from {source_cover_path}')
        if not source_cover_path.exists():
            logger.critical(f'No cover found on {source_cover_path}')
            raise ValueError(f'No cover found on {source_cover_path}')
        FileOps.copy(source_cover_path, self.novel_cover_file)

    def load_novel_cover(self) -> Optional[bytes]:
        if self.novel_cover_file is None:
            logger.debug(f'No cover found')
            return None
        logger.debug(f'Loading cover from {self.novel_cover_file}')
        cover = FileOps.read_binary(self.novel_cover_file)
        if cover is None:
            logger.debug(f'Could not read cover from {self.novel_cover_file}')
        return cover

    ## TOC API

    def add_toc(self, html: str) -> int:
        """Add a new TOC fragment, return its index."""
        idx = self._next_toc_idx()
        toc_path = self.novel_toc_dir / f"toc_{idx}.html"
        FileOps.save_text(toc_path, html)

        toc_index = self._load_toc_index()
        toc_index["entries"].append({"file": toc_path.name, "updated": now_iso()})
        self._store_toc_index(toc_index)

        logger.debug(f"Added TOC #{idx} → {toc_path}")
        return idx

    def update_toc(self, idx: int, html: str) -> None:
        toc_path = self.novel_toc_dir / f"toc_{idx}.html"
        if not toc_path.exists():
            raise FileManagerError(f"TOC #{idx} not found")

        FileOps.save_text(toc_path, html)

        toc_index = self._load_toc_index()
        for entry in toc_index["entries"]:
            if entry["file"] == toc_path.name:
                entry["updated"] = now_iso()
                break
        self._store_toc_index(toc_index)
        logger.debug(f"Updated TOC #{idx}")

    def delete_toc(self, idx: Optional[int] = None) -> None:
        """Delete a single TOC by index or all if *idx* is None."""
        toc_index = self._load_toc_index()

        def _delete(path: Path) -> None:
            FileOps.delete(path)
            logger.debug(f"Deleted {path}")

        if idx is None:  # delete all
            for entry in toc_index["entries"]:
                _delete(self.novel_toc_dir / entry["file"])
            toc_index["entries"] = []
        else:
            toc_path = self.novel_toc_dir / f"toc_{idx}.html"
            _delete(toc_path)
            toc_index["entries"] = [
                e for e in toc_index["entries"] if e["file"] != toc_path.name
            ]
        self._store_toc_index(toc_index)

    def get_toc(self, idx: int) -> Optional[str]:
        """Return TOC HTML content or None."""
        return FileOps.read_text(self.novel_toc_dir / f"toc_{idx}.html")

    def get_all_toc(self) -> list[str]:
        """Return all TOC fragments in order."""
        toc_index = self._load_toc_index()
        contents: list[str] = []
        for entry in toc_index["entries"]:
            html = FileOps.read_text(self.novel_toc_dir / entry["file"])
            if html is not None:
                contents.append(html)
        return contents

    def save_book(self, book: epub.EpubBook, filename: str) -> bool:
        book_path = self.novel_base_dir / filename
        logger.debug(f'Attempting to save book to {book_path}')
        try:
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
            logger.critical(f'Unexpected error saving book to {book_path}: {e}')
            return False

    def _load_toc_index(self) -> dict:
        """Return the toc.json structure (creates a blank one if missing)."""
        idx = FileOps.read_json(self.novel_toc_dir / "toc.json") or {
            "updated": now_iso(),
            "entries": [],
        }
        return idx

    def _store_toc_index(self, idx: dict) -> None:
        """Persist toc.json with a fresh root timestamp."""
        idx["updated"] = now_iso()
        FileOps.save_json(self.novel_toc_dir / "toc.json", idx)

    def _next_toc_idx(self) -> int:
        existing = (
            int(p.stem.split("_")[1]) for p in self.novel_toc_dir.glob("toc_*.html")
        )
        return max(existing, default=-1) + 1

    @staticmethod
    def _get_novel_base_dir(
            title: str,
            base_novels_dir: str,
            novel_base_dir: str | None = None
    ) -> Path:
        """
        Resolve the base directory for *title* without creating any directories.

        Priority:
        1. Explicit *novel_base_dir* argument.
        2. Stored value in <base_novels_dir>/meta.json.
        3. New path derived from normalized title, recorded back to meta.json.
        """
        base_dir_path = Path(base_novels_dir)
        if not base_dir_path.exists():
            raise FileManagerError(f"Base novels directory does not exist: {base_dir_path}")

        # — 1. If the caller supplied a path, return it
        if novel_base_dir:
            return Path(novel_base_dir)

        # — 2. Try to read meta.json
        meta_path = base_dir_path / "meta.json"
        if meta_path.exists():
            try:
                meta: Dict[str, Dict[str, str]] = FileOps.read_json(meta_path)
                if title in meta and meta[title].get("novel_base_dir"):
                    return Path(meta[title]["novel_base_dir"])
            except Exception as exc:  # malformed JSON → ignore
                logger.warning(f"Failed to read {meta_path}: {exc}")

        # — 3. Fallback, generate a new directory name
        clean_title = _normalize_dirname(title)

        return base_dir_path / clean_title

    @staticmethod
    def _store_novel_base_dir(
            title: str,
            resolved_path: Path,
            base_novels_dir: str,
    ) -> None:
        """
        Persist <title, resolved_path> in <base_novels_dir>/meta.json.
        """
        meta_path = Path(base_novels_dir) / "meta.json"
        try:
            # Load existing metadata (ignore errors, start fresh on corruption)
            meta: Dict[str, Dict[str, str]] = {}
            if meta_path.exists():
                try:
                    meta = FileOps.read_json(meta_path)
                except Exception as exc:
                    logger.warning(f"meta.json corrupted, regenerating: {exc}")

            # Skip write if up to date
            current = meta.get(title, {}).get("novel_base_dir")
            if current == str(resolved_path):
                logger.debug(f"meta.json already has correct path for '{title}'; no update needed.")
                return

            # Update and persist
            meta.setdefault(title, {})["novel_base_dir"] = str(resolved_path)
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info(f"Recorded/updated novel dir in {meta_path}: {resolved_path}")

        except Exception as exc:
            logger.warning(f"Unable to update {meta_path}: {exc}")
