import os
import json
from pathlib import Path
import sys
from datetime import datetime

import click

from file_manager import FileManager
from novel_scrapper import Novel

CURRENT_DIR = Path(__file__).resolve().parent


def validate_date(ctx, param, value):
    if value:
        try:
            if len(value) == 4:
                datetime.strptime(value, '%Y')
            elif len(value) == 7:
                datetime.strptime(value, '%Y-%m')
            elif len(value) == 10:
                datetime.strptime(value, '%Y-%m-%d')
            else:
                raise ValueError
        except ValueError:
            raise click.BadParameter(
                'Date should be a valid date and must be in the format YYYY-MM-DD, YYYY-MM or YYYY')
    return value


@click.group()
def cli():
    """CLI Tool for web novel scraping"""

# COMMON ARGUMENTS


title_option = click.option(
    '-t', '--title', type=str, required=True, help='Novel title')
novel_base_dir_option = click.option(
    '-nb', '--novel-base-dir', type=str, help='Alternative base directory for the novel files')

# Metadata:
metadata_author_option = click.option(
    '--author', type=str, help='Name of the novel author')
metadata_language_option = click.option(
    '--language', type=str, help='Novel language')
metadata_description_option = click.option(
    '--description', type=str, help='Novel description')
metadata_start_date_option = click.option(
    '--start-date', callback=validate_date, type=str, help='Novel start date, should be in the format YYYY-MM-DD, YYYY-MM or YYYY')
metadata_end_date_option = click.option(
    '--end-date', callback=validate_date, type=str, help='Novel end date, should be in the format YYYY-MM-DD, YYYY-MM or YYYY')

# TOC options
toc_main_url_option = click.option(
    '--toc-main-url', type=str, help='Main link of the TOC, required if not loading from file')
sync_toc_option = click.option('--sync-toc', is_flag=True, default=False, show_default=True, help='If the TOC is reloaded before the chapters are requested')

def create_toc_html_option(required: bool = False):
    return click.option(
        '--toc-html',
        type=click.File(encoding='utf-8'),
        required=required,
        help='Novel TOC HTML loaded from file' +
        (' (required if not loading from URL)' if required else '')
    )


host_option = click.option(
    '--host', type=str, help='Host that will be used for decoding, optional if toc-main-url is provided')

# Scrapper behavior options
save_title_to_content_option = click.option('--save-title-to-content', is_flag=True, show_default=True,
                                            default=False, help='Set if the title of the chapter should be added to the content')
auto_add_host_option = click.option('--auto-add-host', is_flag=True, show_default=True,
                                    default=False, help='Set if the host should be automatically added to the chapters urls')
force_flaresolver_option = click.option('--force-flaresolver', is_flag=True, show_default=True,
                                        default=False, help='Set if the requests should be forced to use FlareSolver')


def load_config(ctx, param, value):
    if value and os.path.exists(value):
        with open(value, 'r') as f:
            config = json.load(f)
        ctx.default_map = ctx.default_map or {}
        ctx.default_map.update(config)
    return value


def obtain_novel(novel_title: str, novel_base_dir: str = None, allow_not_exists: bool = True) -> Novel:
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

# Novel creation and data management commands


@cli.command()
@title_option
@novel_base_dir_option
@toc_main_url_option
@create_toc_html_option()
@host_option
@metadata_author_option
@metadata_start_date_option
@metadata_end_date_option
@metadata_language_option
@metadata_description_option
@click.option('--tag', 'tags', type=str, help='Novel tag', multiple=True)
@click.option('--cover', type=str, help='Path of the image to be used as cover')
@save_title_to_content_option
@auto_add_host_option
@force_flaresolver_option
def create_novel(title,
                 novel_base_dir,
                 toc_main_url,
                 toc_html,
                 host,
                 author,
                 start_date,
                 end_date,
                 language,
                 description,
                 tags,
                 cover,
                 save_title_to_content,
                 auto_add_host,
                 force_flaresolver):
    """Create a new novel"""
    novel = obtain_novel(title, novel_base_dir, allow_not_exists=True)
    if novel:
        click.confirm(f'A novel with the title {
                      title} already exists, do you want to replace it?', abort=True)
        novel._clean_toc()
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
                       start_date=start_date,
                       end_date=end_date,
                       language=language,
                       description=description)
    novel.set_scrapper_behavior(save_title_to_content=save_title_to_content,
                                auto_add_host=auto_add_host,
                                force_flaresolver=force_flaresolver)
    if tags:
        for tag in tags:
            novel.add_tag(tag)
    if cover:
        novel.set_cover_image(cover)
    click.echo('Novel saved succesfully')

@cli.command()
@title_option
def show_novel_info(title):
    novel = obtain_novel(title)
    click.echo(novel)

@cli.command()
@title_option
@metadata_author_option
@metadata_start_date_option
@metadata_end_date_option
@metadata_language_option
@metadata_description_option
def set_metadata(title, author, start_date, end_date, language, description):
    novel = obtain_novel(title)
    novel.set_metadata(author=author,
                       start_date=start_date,
                       end_date=end_date,
                       language=language,
                       description=description)
    click.echo('Novel metadata saved succesfully')
    click.echo(novel.metadata)


@cli.command()
@title_option
def show_metadata(title):
    novel = obtain_novel(title)
    click.echo(novel.metadata)


@cli.command()
@title_option
@click.option('--tag', type=str, required=True, help='New Tag')
def add_tag(title, tag):
    novel = obtain_novel(title)
    if novel.add_tag(tag):
        click.echo('Tag added succesfully')
    else:
        click.echo('Tag already exists', err=True)
    click.echo(f'Tags: {", ".join(novel.metadata.tags)}')


@cli.command()
@title_option
@click.option('--tag', type=str, required=True, help='Tag to be removed')
def remove_tag(title, tag):
    novel = obtain_novel(title)
    if novel.remove_tag(tag):
        click.echo('Tag removed succesfully')
    else:
        click.echo('Tag does not exist', err=True)
    click.echo(f'Tags: {", ".join(novel.metadata.tags)}')


@cli.command()
@title_option
def show_tags(title):
    novel = obtain_novel(title)
    click.echo(f'Tags: {", ".join(novel.metadata.tags)}')


@cli.command()
@title_option
@click.option('--cover-image', type=str, required=True, help='Filepath of the cover image')
def set_cover_image(title, cover_image):
    novel = obtain_novel(title)
    novel.set_cover_image(cover_image)
    click.echo('New cover image set succesfully')


@cli.command()
@title_option
@click.option('--save-title-to-content', type=bool, help='Toggle the title of the chapter being added to the content')
@click.option('--auto-add-host', type=bool, help='Toggle automatic addition of the host to chapter URLs')
@click.option('--force-flaresolver', type=bool, help='Toggle forcing the use of FlareSolver')
@click.option('--hard-clean', type=bool, help='Toggle using a hard clean when cleaning HTML files')
def set_scrapper_behavior(title, save_title_to_content, auto_add_host, force_flaresolver, hard_clean):
    novel = obtain_novel(title)
    # Pasar los flags como diccionario de argumentos
    novel.set_scrapper_behavior(
        save_title_to_content=save_title_to_content,
        auto_add_host=auto_add_host,
        force_flaresolver=force_flaresolver,
        hard_clean=hard_clean
    )
    click.echo('New Scrapper Behavior added succesfully')


@cli.command()
@title_option
def show_scrapper_behavior(title):
    novel = obtain_novel(title)
    click.echo(novel.scrapper_behavior)


@cli.command()
@title_option
@host_option
def set_host(title, host):
    novel = obtain_novel(title)
    novel.set_host(host)
    click.echo('New host set succesfully')

# TOC MANAGEMENT COMMANDS


@cli.command()
@title_option
@click.option('--toc-main-url', type=str, required=True, help='New TOC main url (Previous links will be deleted)')
def set_toc_main_url(title, toc_main_url):
    novel = obtain_novel(title)
    novel.set_toc_main_url(toc_main_url)


@cli.command()
@title_option
@create_toc_html_option(required=True)
@host_option
def add_toc_html(title, toc_html, host):
    novel = obtain_novel(title)
    html_content = toc_html.read()
    novel.add_toc_html(html_content, host)


@cli.command()
@title_option
@click.option('--reload-files', is_flag=True, required=False, default=False, show_default=True, help='Reload the toc files before sync (only works if using a toc url)')
def sync_toc(title, reload_files):
    novel = obtain_novel(title)
    novel.sync_toc(reload_files)


@cli.command()
@title_option
@click.option('--auto-approve', is_flag=True, required=False, default=False, show_default=True, help='Auto approve')
def delete_toc(title, auto_approve):
    novel = obtain_novel(title)
    if not auto_approve:
        click.confirm(f'Are you sure you want to delete the toc for {
                      title}', abort=True)
    novel.clear_toc()


@cli.command()
@title_option
def show_toc(title):
    novel = obtain_novel(title)
    click.echo(novel.show_toc())

# CHAPTER MANAGEMENT COMMANDS


@cli.command()
@title_option
@click.option('--chapter-url', type=str, required=False, help='Chapter URL to be scrapped')
@click.option('--chapter-num', type=int, required=False, help='Chapter number to be scrapped')
@click.option('--update-html', is_flag=True, default=False, show_default=True, help='If the chapter html is saved, it will be updated')
def scrap_chapter(title, chapter_url, chapter_num, update_html):
    novel = obtain_novel(title)
    if not chapter_url and not chapter_num:
        click.echo('Chapter url or chapter num should be setted', err=True)
    if chapter_num and chapter_url:
        click.echo('It should be either chapter url or chapter num', err=True)
    if chapter_num <= 0 or chapter_num > len(novel.chapters):
        raise click.BadParameter(message='Chapter number should be positive and an existing chapter', param_hint='--chapter-num')
    chapter, content = novel.scrap_chapter(
        chapter_url=chapter_url, chapter_idx=chapter_num - 1, update_html=update_html)
    if not chapter or not content:
        click.echo('Chapter num or url not found.', err=True)
    click.echo(chapter)
    click.echo('Content:')
    click.echo(content)


@cli.command()
@title_option
@sync_toc_option
@click.option('--update-html', is_flag=True, default=False, show_default=True, help='If the chapter html is saved, it will be updated')
@click.option('--clean-chapters', is_flag=True, default=False, show_default=True, help='If the chapter html should be cleaned upon saving')
def request_all_chapters(title, sync_toc, update_html, clean_chapters):
    novel = obtain_novel(title)
    novel.request_all_chapters(
        sync_toc=sync_toc, update_html=update_html, clean_chapters=clean_chapters)
    click.echo('All chapters requested and saved.')

@cli.command()
@title_option
def show_chapters(title):
    novel = obtain_novel(title)
    click.echo(novel.show_chapters())

@cli.command()
@title_option
@sync_toc_option
@click.option('--start-chapter', type=int, default=1, show_default=True, help='The start chapter for the books (position in the toc, may differ from the actual number)')
@click.option('--end-chapter', type=int, default=None, show_default=True, help='The end chapter for the books (if not defined, every chapter will be saved)')
@click.option('--chapters-by-book', type=int, default=100, show_default=True, help='The number of chapters each book will have')
def save_novel_to_epub(title, sync_toc, start_chapter, end_chapter, chapters_by_book):
    if start_chapter <= 0:
        raise click.BadParameter(
            'Should be a positive number', param_hint='--start-chapter')
    if end_chapter is not None:
        if end_chapter < start_chapter or end_chapter <= 0:
            raise click.BadParameter(
                'Should be a positive number and bigger than the start chapter', param_hint='--end-chapter')
    if chapters_by_book is not None:
        if chapters_by_book <= 0:
            raise click.BadParameter(
                'Should be a positive number', param_hint='--chapters-by-book')

    novel = obtain_novel(title)
    novel.save_novel_to_epub(sync_toc=sync_toc,
                             start_chapter=start_chapter,
                             end_chapter=end_chapter,
                             chapters_by_book=chapters_by_book)
    click.echo('All books saved.')


# UTILS

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
def version():
    """Show program version"""
    click.echo('Versión 0.0.1')


if __name__ == '__main__':
    cli()
