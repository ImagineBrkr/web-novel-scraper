import click

import custom_logger
from output_file import OutputFiles
from novel_scrapper import *

@click.group()
def cli():
    """CLI Tool for web novel scraping"""
    pass

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
def create_novel(title, novel_link, author, start_year, end_year, language, description, tags, cover):
    """Create a new novel"""
    novel = load_novel(title)
    if novel:
        click.confirm(f'A novel with the title {title} already exists, do you want to replace it?', abort=True)
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
        
@cli.command()
@click.option('-t', '--title', type=str, required=True, help='Novel title')
def scrap_novel(title):
    novel = load_novel(title)
    if not novel:
        click.echo(message='Novel with that title not exists', err=True)
        return
    if not novel.toc_links_list:
        novel.update_chapter_list()
    novel.scrap_all_chapters()
    novel.save_novel_to_epub()

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
@click.option('--toc-html', type=click.File(), required=True, help='Novel TOC custom HTML')
def set_custom_toc_html(title, toc_html):
    novel = load_novel(title)
    if not novel:
        click.echo(message='Novel with that title not exists', err=True)
        return
    html_content = toc_html.read()
    novel.set_custom_toc(html_content)

@cli.command()
def version():
    """Show program version"""
    click.echo('Versión 1.0.0')

if __name__ == '__main__':
    cli()
