from web_novel_scraper.novel_scraper import Novel
from web_novel_scraper.models import Chapter
from web_novel_scraper.exporters.base_exporter import BaseExporter
from web_novel_scraper.exceptions import (
    ChapterContentNotFoundError,
    ChapterTitleNotFoundError,
    InvalidOutputDirectoryError,
    InvalidPathError,
    IOUtilsError,
    SaveBookError,
)
from web_novel_scraper.logger_manager import create_logger
from web_novel_scraper.io_helpers.utils import IOUtils
from html import escape
from pathlib import Path

logger = create_logger(__name__)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title}</title>

<style>
    :root{{
        --font-size:16px;
    }}

    body{{
        font-family:Arial,sans-serif;
        max-width:850px;
        margin:auto;
        padding:20px;
        line-height:1.8;
        background:#111;
        color:#eee;
        font-size:var(--font-size);
    }}

h1{{margin-bottom:5px;}}

.meta{{
    color:#aaa;
    margin-bottom:25px;
}}

.controls{{
    display:flex;
    gap:8px;
    margin-bottom:20px;
    flex-wrap:wrap;
    align-items:center;
}}

.chapter-nav{{
    display:flex;
    gap:8px;
}}

.font-size-buttons{{
    display:flex;
    gap:5px;
    margin-left:auto;
}}

button{{
    padding:8px 12px;
    border:none;
    cursor:pointer;
    background:#333;
    color:white;
    border-radius:4px;
    font-size:.9em;
}}

button:hover{{
    background:#555;
}}

button.active{{
    background:#0066cc;
}}

.chapter{{
    display:none;
}}

.chapter.active{{
    display:block;
}}

.continuous .chapter{{
    display:block;
    margin-bottom:60px;
}}

.continuous .chapter-nav{{
    display:none;
}}

h2{{
    margin-top:40px;
}}

p{{
    white-space:pre-wrap;
}}

/* TOC */
.toc{{
    display:none;
    background:#1a1a1a;
    border:1px solid #333;
    padding:15px;
    margin-bottom:20px;
    border-radius:6px;
}}

.toc.open{{
    display:block;
}}

.toc h3{{
    margin-top:0;
}}

.toc ul{{
    list-style:none;
    padding:0;
    margin:0;
}}

.toc li{{
    margin:6px 0;
}}

.toc a{{
    color:#66b3ff;
    text-decoration:none;
}}

.toc a:hover{{
    text-decoration:underline;
}}

/* Mobile */
@media (max-width:768px){{
    body{{
        padding:10px;
    }}

    .controls{{
        gap:5px;
    }}

    button{{
        padding:6px 10px;
        font-size:.8rem;
    }}

    h1{{
        font-size:1.4rem;
    }}

    h2{{
        font-size:1.2rem;
    }}

    .font-size-buttons{{
        margin-left:0;
    }}
}}
</style>
</head>

<body>

<h1>{title}</h1>

<div class="meta">
    {metadata_html}
</div>

<div class="controls">
    <button onclick="toggleTOC()">☰ TOC</button>

    <button onclick="setPagedMode()">Chapters</button>
    <button onclick="setContinuousMode()">Continuous</button>

    <div class="chapter-nav">
        <button onclick="prevChapter()">◀</button>
        <button onclick="nextChapter()">▶</button>
    </div>

    <div class="font-size-buttons">
        <button onclick="setFontSize('small')" id="btn-small">A−</button>
        <button onclick="setFontSize('medium')" id="btn-medium">A</button>
        <button onclick="setFontSize('large')" id="btn-large">A+</button>
    </div>
</div>

<div id="toc" class="toc">
    <h3>Índice</h3>
    <ul id="toc-list"></ul>
</div>

<div id="book">
{chapters_html}
</div>

<script>
const chapters = document.querySelectorAll(".chapter");
const book = document.getElementById("book");

let current = 0;
let continuous = false;

function showChapter(index){{
    chapters.forEach(ch => ch.classList.remove("active"));

    if(chapters[index]){{
        chapters[index].classList.add("active");
        current = index;
        localStorage.setItem("currentChapter", current);
    }}
}}

function nextChapter(){{
    if(continuous) return;

    if(current < chapters.length - 1){{
        showChapter(current + 1);
        window.scrollTo(0,0);
    }}
}}

function prevChapter(){{
    if(continuous) return;

    if(current > 0){{
        showChapter(current - 1);
        window.scrollTo(0,0);
    }}
}}

function setContinuousMode(){{
    continuous = true;
    book.classList.add("continuous");
    localStorage.setItem("readingMode","continuous");
}}

function setPagedMode(){{
    continuous = false;
    book.classList.remove("continuous");
    showChapter(current);
    localStorage.setItem("readingMode","paged");
}}

function setFontSize(size){{

    const sizes = {{
        small:'14px',
        medium:'16px',
        large:'18px'
    }};

    document.documentElement.style.setProperty('--font-size', sizes[size]);
    localStorage.setItem("fontSize", size);

    updateFontSizeButtons(size);
}}

function updateFontSizeButtons(size){{

    document.getElementById('btn-small').classList.remove('active');
    document.getElementById('btn-medium').classList.remove('active');
    document.getElementById('btn-large').classList.remove('active');

    document.getElementById('btn-' + size).classList.add('active');
}}

function toggleTOC(){{
    document.getElementById("toc").classList.toggle("open");
}}

/* Build TOC automatically */
const tocList = document.getElementById("toc-list");

chapters.forEach((chapter,index)=>{{

    const title =
        chapter.querySelector("h2")?.innerText ||
        `Chapter ${{index + 1}}`;

    const li = document.createElement("li");
    const link = document.createElement("a");

    link.href = "#";
    link.textContent = title;

    link.onclick = (e)=>{{
        e.preventDefault();

        if(continuous){{
            chapter.scrollIntoView({{
                behavior:"smooth"
            }});
        }}else{{
            showChapter(index);
        }}
    }};

    li.appendChild(link);
    tocList.appendChild(li);
}});

const savedChapter = localStorage.getItem("currentChapter");
const savedMode = localStorage.getItem("readingMode");
const savedFontSize = localStorage.getItem("fontSize") || "medium";

if(savedChapter !== null){{
    current = parseInt(savedChapter);
}}

if(savedMode === "continuous"){{
    setContinuousMode();
}}else{{
    setPagedMode();
}}

setFontSize(savedFontSize);
showChapter(current);
</script>

</body>
</html>
"""


class HTMLExporter(BaseExporter):
    _file_extension: str = ".html"

    def __init__(self):
        self.novel = None
        self.book_title = None

        self.html_book = None
        self.chapters_html = None
        self._metadata_html = None

    def export_novel_to_book(
        self,
        novel: Novel,
        chapters: list[Chapter],
        book_title: str,
        output_directory: str | Path,
    ) -> None:
        try:
            IOUtils.ensure_dir(output_directory)
            output_path = IOUtils.get_path_in_dir(
                output_directory, book_title + HTMLExporter._file_extension
            )
        except InvalidPathError as e:
            raise InvalidOutputDirectoryError(
                f'The Output Directory "{output_directory}" is invalid: {str(e)}'
            )
        logger.debug(f"Output path for the book: '{output_path}'")
        self.book_title = book_title
        self.novel = novel

        self._create_metadata_html()
        self.chapters_html = ""
        for chapter in chapters:
            self._add_chapter_to_chapters_html(chapter)

        self._create_html_book()
        self._save_html_book(output_path)

    def _create_html_book(self) -> None:
        self.html_book = HTML_TEMPLATE.format(
            title=escape(self.novel.title),
            metadata_html=self._metadata_html,
            chapters_html=self.chapters_html,
        )

    def _create_metadata_html(self) -> None:
        metadata_parts = []

        if self.novel.metadata.description:
            metadata_parts.append(
                f"<div><strong>Description: </strong> {escape(self.novel.metadata.description)}</div>"
            )

        if self.novel.metadata.author:
            metadata_parts.append(
                f"<div><strong>Author: </strong> {escape(self.novel.metadata.author)}</div>"
            )

        self._metadata_html = "".join(metadata_parts)

    def _add_chapter_to_chapters_html(self, chapter: Chapter) -> None:
        if chapter.chapter_content is None:
            raise ChapterContentNotFoundError(
                f'Chapter with url "{chapter.chapter_url}" has no content or has not been scrapped yet.'
            )
        if chapter.chapter_title is None:
            raise ChapterTitleNotFoundError(
                f'Chapter with url "{chapter.chapter_url} has no title or has not been scrapped yet.'
            )

        # The first chapter will be active by default.
        active = False
        if self.chapters_html == "":
            active = True

        self.chapters_html += f"""
        <div class="chapter{" active" if active else ""}">
            <h2>{escape(chapter.chapter_title)}</h2>
            <p>{chapter.chapter_content}</p>
        </div>
        """
        logger.debug(f"Chapter with URL '{chapter.chapter_url}' added to the book.")

    def _save_html_book(self, output_path: Path):
        logger.debug(f"Trying to save book to {output_path}...")
        if output_path.exists():
            logger.warning(
                f"The file '{output_path}' already exists and will be overwritten."
            )
        try:
            IOUtils.save_text_file(output_path, self.html_book)
            logger.info(f"Book '{self.book_title}' saved to file '{output_path}'.")
        except IOUtilsError as e:
            raise SaveBookError(f"Could not Save Book to {output_path}: {e}") from e
