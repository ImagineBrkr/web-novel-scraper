import os
import json
from pathlib import Path

import click

import custom_logger
from output_file import OutputFiles
from novel_scrapper import *

CURRENT_DIR = Path(__file__).resolve().parent
CONTEXT_SETTINGS = dict(default_map={
    "NOVEL_LOCATION": ".",
    "FLARESOLVER_URL": "http://localhost:8191/v1"
})


@click.group()
def cli():
    """CLI Tool for web novel scraping"""


def load_config(ctx, param, value):
    if value and os.path.exists(value):
        with open(value, 'r') as f:
            config = json.load(f)
        ctx.default_map = ctx.default_map or {}
        ctx.default_map.update(config)
    return value


def load_novel(novel_title: str) -> Novel:
    output_file = OutputFiles(novel_title)
    novel_json = output_file.load_novel_json()
    if novel_json:
        novel = Novel.from_json(novel_json)
        return novel


@cli.command()
@click.option('-t', '--title', type=str, required=True, help='Novel title')
@click.option('--novel-link', type=str, required=True, help='Main link of the TOC')
@click.option('--author', type=str, help='Novel author')
@click.option('--start-year', type=str, help='Novel start year')
@click.option('--end-year', type=str, help='Novel end year')
@click.option('--language', type=str, help='Novel language')
@click.option('--description', type=str, help='Novel description')
@click.option('-t', '--tag', 'tags', type=str, help='Novel tag', multiple=True)
@click.option('--cover', type=str, help='Novel cover path')
@click.option('--save-title-to-content', type=bool, help='Set if the title of the chapter should be added to the content')
def create_novel(title, novel_link, author, start_year, end_year, language, description, tags, cover, save_title_to_content):
    """Create a new novel"""
    novel = load_novel(title)
    if novel:
        click.confirm(f'A novel with the title {
                      title} already exists, do you want to replace it?', abort=True)
    novel = Novel(title, toc_main_link=novel_link)
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
    if save_title_to_content is not None:
        novel.set_save_title_to_content(save_title_to_content)


@cli.command()
@click.option('-t', '--title', type=str, required=True, help='Novel title')
@click.option('--update-chapters', type=bool, default=False, required=False, help='Update the existing chapters info by checking the html')
@click.option('--update-html', type=bool, default=False, required=False, help='Update the existing chapters html by doing a new request')
def scrap_novel(title, update_chapters, update_html):
    novel = load_novel(title)
    if not novel:
        click.echo(message='Novel with that title not exists', err=True)
        return
    if not novel.toc_links_list:
        novel.update_chapter_list()
    novel.save_novel_to_epub()


@cli.command()
@click.option('-t', '--title', type=str, required=True, help='Novel title')
@click.option('--save-title-to-content', type=bool, required=True, help='Set if the title of the chapter should be added to the content')
def set_save_title_to_content(title, save_title_to_content):
    novel = load_novel(title)
    if not novel:
        click.echo(message='Novel with that title not exists', err=True)
        return
    novel.set_save_title_to_content(save_title_to_content)


@cli.command()
@click.option('-t', '--title', type=str, required=True, help='Novel title')
@click.option('--toc-link', type=str, required=True, help='New TOC link')
def set_toc(title, toc_link):
    novel = load_novel(title)
    if not novel:
        click.echo(message='Novel with that title not exists', err=True)
        return
    novel.set_toc_main_link(toc_link)


@cli.command()
@click.option('-t', '--title', type=str, required=True, help='Novel title')
@click.option('--tag', type=str, required=True, help='New Tag')
def add_tag(title, tag):
    novel = load_novel(title)
    if not novel:
        click.echo(message='Novel with that title not exists', err=True)
        return
    novel.add_tag(tag)


@cli.command()
@click.option('-t', '--title', type=str, required=True, help='Novel title')
@click.option('--tag', type=str, required=True, help='New Tag')
def remove_tag(title, tag):
    novel = load_novel(title)
    if not novel:
        click.echo(message='Novel with that title not exists', err=True)
        return
    novel.remove_tag(tag)


@cli.command()
@click.option('-t', '--title', type=str, required=True, help='Novel title')
@click.option('--cover-image-file', type=str, required=True, help='Filepath of the cover image')
def set_cover_image(title, cover_image_file):
    novel = load_novel(title)
    if not novel:
        click.echo(message='Novel with that title not exists', err=True)
        return
    novel.set_cover_image(cover_image_file)


@cli.command()
@click.option('-t', '--title', type=str, required=True, help='Novel title')
@click.option('--toc-link', type=str, required=False, help='New TOC link')
def update_toc(title, toc_link):
    novel = load_novel(title)
    if not novel:
        click.echo(message='Novel with that title not exists', err=True)
        return
    if toc_link:
        novel.set_toc_main_link(toc_link)
    else:
        novel.update_toc_links_list()


@cli.command()
@click.option('-t', '--title', type=str, required=True, help='Novel title')
@click.option('--toc-html', type=click.File(), required=True, help='Novel TOC custom HTML')
def set_custom_toc_html(title, toc_html):
    novel = load_novel(title)
    if not novel:
        click.echo(message='Novel with that title not exists', err=True)
        return
    html_content = toc_html.read()
    novel.set_custom_toc(html_content)


@cli.command()
@click.option('-t', '--title', type=str, required=True, help='Novel title')
def clean_files(title):
    novel = load_novel(title)
    if not novel:
        click.echo(message='Novel with that title not exists', err=True)
        return
    novel.clean_chapters_html_files()


@cli.command()
@click.option('--test', default="test2")
def version(test):
    """Show program version"""
    click.echo(f'Versión {test}')


def load_settings():
    try:
        settings_filepath = Path(CURRENT_DIR) / 'settings.json'
        with open(settings_filepath) as json_file:
            settings = json.load(json_file)
            return settings
    finally:
        return


if __name__ == '__main__':
    settings = load_settings()
    if not settings:
        settings = CONTEXT_SETTINGS
    cli(default_map=settings)
