from pathlib import Path
from datetime import datetime

import click

from .config_manager import ScraperConfig
from .novel_scraper import Novel
from .models import Chapter
from .utils import ValidationError, ScraperError, NetworkError, DecodeError, FileManagerError
from .version import __version__

CURRENT_DIR = Path(__file__).resolve().parent


def global_options(f):
    f = click.option('-nb', '--novel-base-dir', type=click.Path(), required=False,
                     help="Alternative directory for this novel.")(f)
    f = click.option('--config-file', type=click.Path(), required=False, help="Path to config file.")(f)
    f = click.option('--base-novels-dir', type=click.Path(), required=False,
                     help="Alternative base directory for all novels.")(f)
    f = click.option('--decode-guide-file', type=click.Path(), required=False,
                     help="Path to alternative decode guide file.")(f)
    return f


@click.group()
@global_options
@click.pass_context
def cli(ctx, **kwargs):
    """CLI Tool for web novel scraping."""
    ctx.obj = kwargs


def obtain_novel(title, ctx_opts, allow_missing=False):
    cfg = ScraperConfig(parameters=ctx_opts)
    try:
        return Novel.load(title, cfg, ctx_opts.get("novel_base_dir"))
    except ValidationError:
        if allow_missing:
            return None
        click.echo("Novel not found.", err=True)
        exit(1)


def validate_date(ctx, param, value):
    """Validate the date format."""
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
        except ValueError as exc:
            raise click.BadParameter(
                'Date should be a valid date and must be in the format YYYY-MM-DD, YYYY-MM or YYYY') from exc
    return value


# COMMON ARGUMENTS
title_option = click.option(
    '-t', '--title', type=str, required=True, envvar='SCRAPER_NOVEL_TITLE',
    help='Title of the novel, this server as the identifier.')
novel_base_dir_option = click.option(
    '-nb', '--novel-base-dir', type=str, help='Alternative base directory for the novel files.')

# Metadata:
metadata_author_option = click.option(
    '--author', type=str, help='Name of the novel author.')
metadata_language_option = click.option(
    '--language', type=str, help='Language of the novel.')
metadata_description_option = click.option(
    '--description', type=str, help='Description of the novel.')
metadata_start_date_option = click.option(
    '--start-date', callback=validate_date, type=str,
    help='Start date of the novel, should be in the format YYYY-MM-DD, YYYY-MM or YYYY.')
metadata_end_date_option = click.option(
    '--end-date', callback=validate_date, type=str,
    help='End date of the novel, should be in the format YYYY-MM-DD, YYYY-MM or YYYY.')

# TOC options
toc_main_url_option = click.option(
    '--toc-main-url', type=str, help='Main URL of the TOC, required if not loading from file.')
sync_toc_option = click.option('--sync-toc', is_flag=True, default=False, show_default=True,
                               help='Reload the TOC before requesting chapters.')


def create_toc_html_option(required: bool = False):
    return click.option(
        '--toc-html',
        type=click.File(encoding='utf-8'),
        required=required,
        help=(
            'Novel TOC HTML loaded from file.' if required else 'Novel TOC HTML loaded from file (required if not loading from URL)')
    )


host_option = click.option(
    '--host', type=str, help='Host used for decoding, optional if toc-main-url is provided.')

# Scraper behavior options
save_title_to_content_option = click.option('--save-title-to-content', is_flag=True, show_default=True,
                                            default=False, help='Add the chapter title to the content.')
auto_add_host_option = click.option('--auto-add-host', is_flag=True, show_default=True,
                                    default=False, help='Automatically add the host to chapter URLs.')
force_flaresolver_option = click.option('--force-flaresolver', is_flag=True, show_default=True,
                                        default=False, help='Force the use of FlareSolver for requests.')


# Novel creation and data management commands

@cli.command()
@click.pass_context
@title_option
@toc_main_url_option
@create_toc_html_option()
@host_option
@metadata_author_option
@metadata_start_date_option
@metadata_end_date_option
@metadata_language_option
@metadata_description_option
@click.option('--tag', 'tags', type=str, help='Novel tag, you can add multiple of them.', multiple=True)
@click.option('--cover', type=str, help='Path of the image to be used as cover.')
@save_title_to_content_option
@auto_add_host_option
@force_flaresolver_option
def create_novel(ctx, title, toc_main_url, toc_html, host, author, start_date, end_date, language, description, tags,
                 cover, save_title_to_content, auto_add_host, force_flaresolver):
    """Creates a new novel and saves it."""
    novel = obtain_novel(title, ctx.obj, allow_missing=True)
    if novel:
        click.confirm(f'A novel with the title {title} already exists, do you want to replace it?', abort=True)
        novel.delete_toc()
    if toc_main_url and toc_html:
        click.echo(
            'You must provide either a TOC URL or a TOC HTML file, not both.', err=True)
        return

    if not toc_main_url and not toc_html:
        click.echo(
            'You must provide either a TOC URL or a TOC HTML file.', err=True)
        return

    if not host and not toc_main_url:
        click.echo(
            'You must provide a host if you are not providing a TOC URL.', err=True)
        return
    toc_html_content = None
    if toc_html:
        toc_html_content = toc_html.read()
    config = ScraperConfig(parameters=ctx.obj)

    novel = Novel.new(title=title,
                      cfg=config,
                      host=host,
                      toc_main_url=toc_main_url,
                      toc_html=toc_html_content)
    novel.set_config(cfg=config,
                     novel_base_dir=ctx.obj.get('novel_base_dir'))
    novel.set_metadata(author=author,
                       start_date=start_date,
                       end_date=end_date,
                       language=language,
                       description=description)
    novel.set_scraper_behavior(save_title_to_content=save_title_to_content,
                               auto_add_host=auto_add_host,
                               force_flaresolver=force_flaresolver)

    if tags:
        for tag in tags:
            novel.add_tag(tag)

    if cover:
        if not novel.set_cover_image(cover):
            click.echo('Error saving the novel cover image.', err=True)
    novel.save_novel()
    click.echo('Novel saved successfully.')


@cli.command()
@click.pass_context
@title_option
def show_novel_info(ctx, title):
    """Show information about a novel."""
    novel = obtain_novel(title, ctx.obj)
    click.echo(novel)


@cli.command()
@click.pass_context
@title_option
@metadata_author_option
@metadata_start_date_option
@metadata_end_date_option
@metadata_language_option
@metadata_description_option
def set_metadata(ctx, title, author, start_date, end_date, language, description):
    """Set metadata for a novel."""
    novel = obtain_novel(title, ctx.obj)
    novel.set_metadata(author=author, start_date=start_date,
                       end_date=end_date, language=language, description=description)
    novel.save_novel()
    click.echo('Novel metadata saved successfully.')
    click.echo(novel.metadata)


@cli.command()
@click.pass_context
@title_option
def show_metadata(ctx, title):
    """Show metadata of a novel."""
    novel = obtain_novel(title, ctx.obj)
    click.echo(novel.metadata)


@cli.command()
@click.pass_context
@title_option
@click.option('--tag', 'tags', type=str, help='Tag to be added', multiple=True)
def add_tags(ctx, title, tags):
    """Add tags to a novel."""
    novel = obtain_novel(title, ctx.obj)
    for tag in tags:
        if not novel.add_tag(tag):
            click.echo(f'Tag {tag} already exists', err=True)
    novel.save_novel()
    click.echo(f'Tags: {", ".join(novel.metadata.tags)}')


@cli.command()
@click.pass_context
@title_option
@click.option('--tag', 'tags', type=str, help='Tag to be removed.', multiple=True)
def remove_tags(ctx, title, tags):
    """Remove tags from a novel."""
    novel = obtain_novel(title, ctx.obj)
    for tag in tags:
        if not novel.remove_tag(tag):
            click.echo(f'Tag {tag} does not exist.', err=True)
    novel.save_novel()
    click.echo(f'Tags: {", ".join(novel.metadata.tags)}')


@cli.command()
@click.pass_context
@title_option
def show_tags(ctx, title):
    """Show tags of a novel."""
    novel = obtain_novel(title, ctx.obj)
    click.echo(f'Tags: {", ".join(novel.metadata.tags)}')


@cli.command()
@click.pass_context
@title_option
@click.option('--cover-image', type=str, required=True, help='Filepath of the cover image.')
def set_cover_image(ctx, title, cover_image):
    """Set the cover image for a novel."""
    novel = obtain_novel(title, ctx.obj)
    novel.set_cover_image(cover_image)
    click.echo(f'Cover image saved successfully.')


@cli.command()
@click.pass_context
@title_option
@click.option('--save-title-to-content', type=bool,
              help='Toggle the title of the chapter being added to the content (use true or false).')
@click.option('--auto-add-host', type=bool,
              help='Toggle automatic addition of the host to chapter URLs (use true or false).')
@click.option('--force-flaresolver', type=bool, help='Toggle forcing the use of FlareSolver (use true or false).')
@click.option('--hard-clean', type=bool, help='Toggle using a hard clean when cleaning HTML files (use true or false).')
def set_scraper_behavior(ctx, title, save_title_to_content, auto_add_host, force_flaresolver, hard_clean):
    """Set scraper behavior for a novel."""
    novel = obtain_novel(title, ctx.obj)
    novel.set_scraper_behavior(
        save_title_to_content=save_title_to_content,
        auto_add_host=auto_add_host,
        force_flaresolver=force_flaresolver,
        hard_clean=hard_clean
    )
    novel.save_novel()
    click.echo('New scraper behavior added successfully.')


@cli.command()
@click.pass_context
@title_option
def show_scraper_behavior(ctx, title):
    """Show scraper behavior of a novel."""
    novel = obtain_novel(title, ctx.obj)
    click.echo(novel.scraper_behavior)


@cli.command()
@click.pass_context
@title_option
@host_option
def set_host(ctx, title, host):
    """Set the host for a novel."""
    novel = obtain_novel(title, ctx.obj)
    novel.set_host(host)
    novel.save_novel()
    click.echo('New host set successfully.')


# TOC MANAGEMENT COMMANDS

@cli.command()
@click.pass_context
@title_option
@click.option('--toc-main-url', type=str, required=True, help='New TOC main URL (Previous links will be deleted).')
def set_toc_main_url(ctx, title, toc_main_url):
    """Set the main URL for the TOC of a novel."""
    novel = obtain_novel(title, ctx.obj)
    novel.set_toc_main_url(toc_main_url)
    novel.save_novel()


@cli.command()
@click.pass_context
@title_option
@create_toc_html_option(required=True)
@host_option
def add_toc_html(ctx, title, toc_html, host):
    """Add TOC HTML to a novel."""
    novel = obtain_novel(title, ctx.obj)
    html_content = toc_html.read()
    novel.add_toc_html(html_content, host)
    novel.save_novel()


@cli.command()
@click.pass_context
@title_option
@click.option('--reload-files', is_flag=True, required=False, default=False, show_default=True,
              help='Reload the TOC files before sync (only works if using a TOC URL).')
def sync_toc(ctx, title, reload_files):
    """Sync the TOC of a novel."""
    novel = obtain_novel(title, ctx.obj)
    if novel.sync_toc(reload_files):
        click.echo(
            'Table of Contents synced with files, to see the new TOC use the command show-toc.')
    else:
        click.echo(
            'Error with the TOC syncing, please check the TOC files and decoding options.', err=True)
    novel.save_novel()


@cli.command()
@click.pass_context
@title_option
@click.option('--auto-approve', is_flag=True, required=False, default=False, show_default=True, help='Auto approve.')
def delete_toc(ctx, title, auto_approve):
    """Delete the TOC of a novel."""
    novel = obtain_novel(title, ctx.obj)
    if not auto_approve:
        click.confirm(f'Are you sure you want to delete the TOC for {title}?', abort=True)
    novel.delete_toc()
    novel.save_novel()


@cli.command()
@click.pass_context
@title_option
def show_toc(ctx, title):
    """Show the TOC of a novel."""
    novel = obtain_novel(title, ctx.obj)
    click.echo(novel.show_toc())


# CHAPTER MANAGEMENT COMMANDS

@cli.command()
@click.pass_context
@title_option
@click.option('--chapter-url', type=str, required=False, help='Chapter URL to be scrapped.')
@click.option('--chapter-num', type=int, required=False, help='Chapter number to be scrapped.')
@click.option('--update-html', is_flag=True, default=False, show_default=True,
              help='If the chapter HTML is saved, it will be updated.')
def scrap_chapter(ctx, title, chapter_url, chapter_num, update_html):
    """Scrap a chapter of a novel."""
    novel = obtain_novel(title, ctx.obj)
    try:
        if chapter_num is not None:
            chapter_num = chapter_num - 1
        chapter = novel.get_chapter(chapter_index=chapter_num,
                                    chapter_url=chapter_url)
    except ValidationError:
        raise click.UsageError(
            'You must set exactly one: --chapter-url o --chapter-num.')
    except ValueError:
        raise click.UsageError('--chapter-num must be a positive number.')

    if chapter is None:
        if chapter_url is not None:
            click.echo('Chapter not found on novel TOC, will try anyways with chapter url')
            chapter = Chapter(chapter_url=chapter_url)
        else:
            raise click.ClickException('Chapter not found.')

    chapter = novel.scrap_chapter(chapter=chapter,
                                  reload_file=update_html)
    click.echo(chapter)
    click.echo('Content:')
    click.echo(chapter.chapter_content)


@cli.command()
@click.pass_context
@title_option
@sync_toc_option
@click.option('--update-html', is_flag=True, default=False, show_default=True,
              help='If the chapter HTML is saved, it will be updated.')
@click.option('--clean-chapters', is_flag=True, default=False, show_default=True,
              help='If the chapter HTML should be cleaned upon saving.')
def request_all_chapters(ctx, title, sync_toc, update_html, clean_chapters):
    """Request all chapters of a novel."""
    novel = obtain_novel(title, ctx.obj)
    novel.request_all_chapters(
        sync_toc=sync_toc,
        reload_files=update_html,
        clean_chapters=clean_chapters)
    novel.save_novel()
    click.echo('All chapters requested and saved.')


@cli.command()
@click.pass_context
@title_option
def show_chapters(ctx, title):
    """Show chapters of a novel."""
    novel = obtain_novel(title, ctx.obj)
    click.echo(novel.show_chapters())
    click.echo(f'Config file: {ctx.obj["CONFIG_FILE"]}')


@cli.command()
@click.pass_context
@title_option
@sync_toc_option
@click.option('--start-chapter', type=int, default=1, show_default=True,
              help='The start chapter for the books (position in the TOC, may differ from the actual number).')
@click.option('--end-chapter', type=int, default=None, show_default=True,
              help='The end chapter for the books (if not defined, every chapter will be saved).')
@click.option('--chapters-by-book', type=int, default=100, show_default=True,
              help='The number of chapters each book will have.')
def save_novel_to_epub(ctx, title, sync_toc, start_chapter, end_chapter, chapters_by_book):
    """Save the novel to EPUB format."""
    if start_chapter <= 0:
        raise click.BadParameter(
            'Should be a positive number.', param_hint='--start-chapter')
    if end_chapter is not None:
        if end_chapter < start_chapter or end_chapter <= 0:
            raise click.BadParameter(
                'Should be a positive number and bigger than the start chapter.', param_hint='--end-chapter')
    if chapters_by_book is not None:
        if chapters_by_book <= 0:
            raise click.BadParameter(
                'Should be a positive number.', param_hint='--chapters-by-book')

    novel = obtain_novel(title, ctx.obj)
    novel.save_novel_to_epub(sync_toc=sync_toc, start_chapter=start_chapter, end_chapter=end_chapter,
                                chapters_by_book=chapters_by_book)
    click.echo('All books saved.')



# UTILS

@cli.command()
@click.pass_context
@title_option
@click.option('--clean-chapters', is_flag=True, default=False, show_default=True,
              help='If the chapters HTML files are cleaned.')
@click.option('--clean-toc', is_flag=True, default=False, show_default=True, help='If the TOC files are cleaned.')
@click.option('--hard-clean', is_flag=True, default=False, show_default=True,
              help='If the files are more deeply cleaned.')
def clean_files(ctx, title, clean_chapters, clean_toc, hard_clean):
    """Clean files of a novel."""
    if not clean_chapters and not clean_toc:
        click.echo(
            'You must choose at least one of the options: --clean-chapters, --clean-toc.', err=True)
        return
    novel = obtain_novel(title, ctx.obj)
    novel.clean_files(clean_chapters=clean_chapters,
                      clean_toc=clean_toc, hard_clean=hard_clean)


@cli.command()
@click.pass_context
@title_option
def show_novel_dir(ctx, title):
    """Show the directory where the novel is saved."""
    novel = obtain_novel(title, ctx.obj)
    click.echo(novel.show_novel_dir())


@cli.command()
def version():
    """Shows the program version."""
    click.echo(f'Version {__version__}')


if __name__ == '__main__':
    cli()
