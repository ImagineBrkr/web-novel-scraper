import os
import json
from pathlib import Path
import sys

import click

import custom_logger
from file_manager import FileManager
from novel_scrapper import Novel

CURRENT_DIR = Path(__file__).resolve().parent


@click.group()
def cli():
    """CLI Tool for web novel scraping"""

# COMMON ARGUMENTS


title_option = click.option(
    '-t', '--title', type=str, required=True, help='Novel title')
novel_base_dir_option = click.option(
    '-nb', '--novel-base-dir', type=str, help='Alternative base directory for the novel files')


def load_config(ctx, param, value):
    if value and os.path.exists(value):
        with open(value, 'r') as f:
            config = json.load(f)
        ctx.default_map = ctx.default_map or {}
        ctx.default_map.update(config)
    return value


def obtain_novel(novel_title: str, novel_base_dir: str = None, allow_not_exists: bool = False) -> Novel:
    file_manager = FileManager(novel_title=novel_title,
                               novel_base_dir=novel_base_dir)
    novel_json = file_manager.load_novel_json()
    if novel_json:
        try:
            novel = Novel.from_json(novel_json)
            return novel
        except KeyError:
            click.echo(
                'JSON file seems to be manipulated, please check it', err=True)
        except json.decoder.JSONDecodeError:
            click.echo(
                'JSON file seems to be corrupted, please check it', err=True)
    elif allow_not_exists:
        return None
    else:
        click.echo(
            message='Novel with that title not exists or the main data file was deleted', err=True)
    sys.exit(1)


def read_html(html_file: click.File) -> str:
    try:
        content = html_file.read()
    except UnicodeDecodeError as e:
        pass

# Novel creation and data management commands


@cli.command()
@title_option
@novel_base_dir_option
@click.option('--toc-main-url', type=str, help='Main link of the TOC, required if not loading from file')
@click.option('--toc-html', type=click.File(encoding='utf-8'), help='Novel TOC HTML loaded from file, required if not loading from URL')
@click.option('--host', type=str, help='Host that will be used for decoding, optional if toc-main-url is provided')
@click.option('--author', type=str, help='Novel author')
@click.option('--start-year', type=str, help='Novel start year')
@click.option('--end-year', type=str, help='Novel end year')
@click.option('--language', type=str, help='Novel language')
@click.option('--description', type=str, help='Novel description')
@click.option('-t', '--tag', 'tags', type=str, help='Novel tag', multiple=True)
@click.option('--cover', type=str, help='Path of the image to be used as cover')
@click.option('--save-title-to-content', is_flag=True, show_default=True, default=False, help='Set if the title of the chapter should be added to the content')
@click.option('--auto-add-host', is_flag=True, show_default=True, default=False, help='Set if the host should be automatically added to the chapters urls')
def create_novel(title, novel_base_dir, toc_main_url, toc_html, host, author, start_year, end_year, language, description, tags, cover, save_title_to_content, auto_add_host):
    """Create a new novel"""
    novel = obtain_novel(title, novel_base_dir, allow_not_exists=True)
    if novel:
        click.confirm(f'A novel with the title {
                      title} already exists, do you want to replace it?', abort=True)
    novel.clear_toc()
    if toc_main_url and toc_html:
        click.echo(
            message='You must provide either a TOC URL or a TOC HTML file, not both', err=True)
        return

    if not toc_main_url and not toc_html:
        click.echo(
            message='You must provide either a TOC URL or a TOC HTML file', err=True)
        return

    if not host and not toc_main_url:
        click.echo(
            message='You must provide a host if you are not providing a TOC URL', err=True)
        return
    toc_html_content = None
    if toc_html:
        toc_html_content = toc_html.read()

    novel = Novel(title, toc_main_url=toc_main_url,
                  toc_html=toc_html_content,
                  host=host,
                  novel_base_dir=novel_base_dir)
    novel.set_metadata(author=author,
                       start_year=start_year,
                       end_year=end_year,
                       language=language,
                       description=description)
    if tags:
        for tag in tags:
            novel.add_tag(tag)
    if cover:
        novel.set_cover_image(cover)
    if save_title_to_content:
        novel.set_save_title_to_content(save_title_to_content)
    if auto_add_host:
        novel.set_auto_add_host(auto_add_host)


@cli.command()
@title_option
@click.option('--author', type=str, help='Novel author')
@click.option('--start-year', type=str, help='Novel start year')
@click.option('--end-year', type=str, help='Novel end year')
@click.option('--language', type=str, help='Novel language')
@click.option('--description', type=str, help='Novel description')
def set_metadata(title, author, start_year, end_year, language, description):
    novel = obtain_novel(title)
    novel.set_metadata(author=author,
                       start_year=start_year,
                       end_year=end_year,
                       language=language,
                       description=description)


@cli.command()
@title_option
@click.option('--tag', type=str, required=True, help='New Tag')
def add_tag(title, tag):
    novel = obtain_novel(title)
    novel.add_tag(tag)


@cli.command()
@title_option
@click.option('--tag', type=str, required=True, help='Tag to be removed')
def remove_tag(title, tag):
    novel = obtain_novel(title)
    novel.remove_tag(tag)


@cli.command()
@title_option
@click.option('--cover-image', type=str, required=True, help='Filepath of the cover image')
def set_cover_image(title, cover_image):
    novel = obtain_novel(title)
    novel.set_cover_image(cover_image)


@cli.command()
@title_option
@click.option('--save-title-to-content', type=bool, required=True, help='Set if the title of the chapter should be added to the content')
def set_save_title_to_content(title, save_title_to_content):
    novel = obtain_novel(title)
    novel.set_save_title_to_content(save_title_to_content)


@cli.command()
@title_option
@click.option('--host', type=str, required=True, help='Host to be used for decoding')
def set_host(title, host):
    novel = obtain_novel(title)
    novel.set_host(host)


# TOC MANAGEMENT COMMANDS


@cli.command()
@title_option
@click.option('--toc-main-url', type=str, required=True, help='New TOC main url (Previous links will be deleted)')
def set_toc_main_url(title, toc_main_url):
    novel = obtain_novel(title)
    novel.set_toc_main_url(toc_main_url)


@cli.command()
@title_option
@click.option('--toc-html', type=click.File(encoding='utf-8'), required=True, help='New TOC HTML file (if a toc_main_url is set, it will be deleted)')
@click.option('--host', type=str, required=False, help='Host to be used for decoding')
def add_toc_html(title, toc_html, host):
    novel = obtain_novel(title)
    html_content = toc_html.read()
    novel.add_toc_html(html_content, host)


@cli.command()
@title_option
@click.option('--hard-reload', is_flag=True, required=False, default=False, show_default=True, help='Host to be used for decoding')
def reload_toc(title, hard_reload):
    novel = obtain_novel(title)
    novel.reload_toc(hard_reload)


@cli.command()
@title_option
@click.option('--update-chapters', type=bool, default=False, required=False, help='Update the existing chapters info by checking the html')
@click.option('--update-html', type=bool, default=False, required=False, help='Update the existing chapters html by doing a new request')
def scrap_novel(title, update_chapters, update_html):
    novel = obtain_novel(title)
    if not novel.toc_links_list:
        novel.get_links_from_toc()
    novel.save_novel_to_epub()


@cli.command()
@title_option
@click.option('--toc-link', type=str, required=False, help='New TOC link')
def update_toc(title, toc_link):
    novel = obtain_novel(title)
    if toc_link:
        novel.set_toc_main_link(toc_link)
    else:
        novel.update_toc_links_list()


# CHAPTER MANAGEMENT COMMANDS


@cli.command()
@title_option
@click.option('--chapter-url', type=str, required=True, help='Chapter URL to be scrapped')
@click.option('--update-html', is_flag=True, default=False, show_default=True, help='If the chapter html is saved, it will be updated')
def scrap_chapter(title, chapter_url, update_html):
    novel = obtain_novel(title)
    chapter, content = novel.scrap_chapter(
        chapter_url=chapter_url, update_html=update_html)
    click.echo(chapter)
    click.echo('Content:')
    click.echo(content)


@cli.command()
@title_option
@click.option('--reload-toc', is_flag=True, default=False, show_default=True, help='If the TOC is reloaded before the chapters are requested')
@click.option('--update-html', is_flag=True, default=False, show_default=True, help='If the chapter html is saved, it will be updated')
def request_all_chapters(title, reload_toc, update_html):
    novel = obtain_novel(title)
    novel.request_all_chapters(reload_toc=reload_toc, update_html=update_html)
    click.echo('All chapters requested and saved.')


@cli.command()
@title_option
@click.option('--reload-toc', is_flag=True, default=False, show_default=True, help='If the TOC is reloaded before the chapters are requested')
@click.option('--chapters-by-book', type=int, default=100, show_default=True, help='The number of chapters each book will have')
def save_novel_to_epub(title, reload_toc, chapters_by_book):
    novel = obtain_novel(title)
    novel.save_novel_to_epub(reload_toc=reload_toc,
                             chapters_by_book=chapters_by_book)
    click.echo('All books saved.')


@cli.command()
@title_option
@click.option('--clean-chapters', is_flag=True, default=False, show_default=True, help='If the chapters html files are cleaned')
@click.option('--clean-toc', is_flag=True, default=False, show_default=True, help='If the toc files are cleaned')
@click.option('--hard-clean', is_flag=True, default=False, show_default=True, help='If the files are more deeply cleaned')
def clean_files(title, clean_chapters, clean_toc, hard_clean):
    if not clean_chapters and not clean_toc:
        click.echo(
            'You must choose at least one of the options: --clean-chapters, --clean-toc', err=True)
        return
    novel = obtain_novel(title)
    novel.clean_files(clean_chapters=clean_chapters,
                      clean_toc=clean_toc, hard_clean=hard_clean)


@cli.command()
@click.option('--test', default="test2")
def version(test):
    """Show program version"""
    click.echo(f'Versión {test}')


if __name__ == '__main__':
    cli()
