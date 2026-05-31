from web_novel_scraper.novel_scraper import Novel
from web_novel_scraper.models import Chapter
from web_novel_scraper.exporters.exporter import BaseExporter
from html import escape
from pathlib import Path

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title}</title>

<style>
    body {{
        font-family: Arial, sans-serif;
        max-width: 850px;
        margin: auto;
        padding: 20px;
        line-height: 1.8;
        background: #111;
        color: #eee;
    }}

    h1 {{
        margin-bottom: 5px;
    }}

    .meta {{
        color: #aaa;
        margin-bottom: 25px;
    }}

    .controls {{
        display: flex;
        gap: 10px;
        margin-bottom: 25px;
        flex-wrap: wrap;
    }}

    button {{
        padding: 8px 14px;
        border: none;
        cursor: pointer;
        background: #333;
        color: white;
        border-radius: 4px;
    }}

    button:hover {{
        background: #555;
    }}

    .chapter {{
        display: none;
    }}

    .chapter.active {{
        display: block;
    }}

    .continuous .chapter {{
        display: block;
        margin-bottom: 60px;
    }}

    h2 {{
        margin-top: 40px;
    }}

    p {{
        white-space: pre-wrap;
    }}
</style>
</head>

<body>

<h1>{title}</h1>

<div class="meta">
    {author_html}
    {description_html}
</div>

<div class="controls">
    <button onclick="setPagedMode()">Modo capítulos</button>
    <button onclick="setContinuousMode()">Modo continuo</button>
    <button onclick="prevChapter()">Anterior</button>
    <button onclick="nextChapter()">Siguiente</button>
</div>

<div id="book">
{chapters_html}
</div>

<script>
    const chapters = document.querySelectorAll(".chapter");
    const book = document.getElementById("book");

    let current = 0;
    let continuous = false;

    function showChapter(index) {{
        chapters.forEach(ch => ch.classList.remove("active"));

        if (chapters[index]) {{
            chapters[index].classList.add("active");
            current = index;

            localStorage.setItem("currentChapter", current);
        }}
    }}

    function nextChapter() {{
        if (continuous) return;

        if (current < chapters.length - 1) {{
            showChapter(current + 1);
            window.scrollTo(0, 0);
        }}
    }}

    function prevChapter() {{
        if (continuous) return;

        if (current > 0) {{
            showChapter(current - 1);
            window.scrollTo(0, 0);
        }}
    }}

    function setContinuousMode() {{
        continuous = true;
        book.classList.add("continuous");

        localStorage.setItem("readingMode", "continuous");
    }}

    function setPagedMode() {{
        continuous = false;
        book.classList.remove("continuous");

        showChapter(current);

        localStorage.setItem("readingMode", "paged");
    }}

    const savedChapter = localStorage.getItem("currentChapter");
    const savedMode = localStorage.getItem("readingMode");

    if (savedChapter !== null) {{
        current = parseInt(savedChapter);
    }}

    if (savedMode === "continuous") {{
        setContinuousMode();
    }} else {{
        setPagedMode();
    }}

    showChapter(current);
</script>

</body>
</html>
"""


class HTMLExporter(BaseExporter):
    def export_novel(
        novel: Novel,
        chapters: list[Chapter],
        output_path: str | Path,
    ) -> None:
        output_path = Path(str(output_path) + ".html")

        html = HTMLExporter._generate_novel_html(
            novel=novel,
            chapters=chapters,
        )

        output_path.write_text(
            html,
            encoding="utf-8",
        )

        return output_path

    @staticmethod
    def _chapter_to_html(
        chapter: Chapter,
        active: bool = False,
    ) -> str:
        return f"""
        <div class="chapter {"active" if active else ""}">
            <h2>{escape(chapter.chapter_title)}</h2>
            <p>{escape(chapter.chapter_content)}</p>
        </div>
        """

    @staticmethod
    def _generate_novel_html(
        novel: Novel,
        chapters: list[Chapter],
    ) -> str:
        chapters_html = "\n".join(
            HTMLExporter._chapter_to_html(
                chapter,
                active=(i == 0),
            )
            for i, chapter in enumerate(chapters)
        )

        description_html = ""

        if novel.metadata.description:
            description_html = (
                f"<div><strong>Descripción:</strong> {escape(novel.description)}</div>"
            )

        author_html = ""
        if novel.metadata.author:
            author_html = (
                f"<div><strong>Autor:</strong> {escape(novel.metadata.author)}</div>"
            )

        return HTML_TEMPLATE.format(
            title=escape(novel.title),
            author_html=author_html,
            description_html=description_html,
            chapters_html=chapters_html,
        )
