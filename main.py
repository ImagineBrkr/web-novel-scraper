import requests
import json
import os
import logging
import re

from bs4 import BeautifulSoup
from ebooklib import epub
import custom_logger

# logging.basicConfig(level=logging.DEBUG, format = '%(name)s - %(levelname)s - %(message)s')
URL = 'https://novelusb.com/novel-book/keyboard-immortal-novel-novel/chapter-2'
FLARESOLVER_URL = 'http://localhost:8191/v1'
# docker run -d   --name=flaresolverr   -p 8191:8191   -e LOG_LEVEL=info   --restart unless-stopped   ghcr.io/flaresolverr/flaresolverr:latest
OUTPUT_PATH = 'output'
TMP_PATH = 'tmp'
MAX_RETRIES = 5
N_CHAPS = 100

custom_logger.set_process("Web scrapping")
# LOGGER = custom_logger.create_logger("WEB SCRAPING")


with open('decode_guide.json', 'r') as f:
    DECODE_GUIDE = json.load(f)


def obtain_host(url: str):
    try:
        host = url.split(':')[1]
    except Exception:
        pass
    while host.startswith('/'):
        host = host[1:]

    host = host.split('/')[0].replace('www.', '')

    return host


def find_elements(soup, element=None, _id=None, _class=None, select=None):

    # Build the CSS selector based on the provided parameters
    selector = ''
    if element:
        selector += element
    if _id:
        selector += f'#{_id}'
    if _class is not None:
        if _class == '':
            selector += ':not([class])'
        else:
            selector += f'.{_class}'

    if select:
        selector = select
    # Find elements based on the selector
    elements = soup.select(selector)

    for el in elements:
        if el.has_attr('style'):
            del el['style']

        ### TEMP
        for h in el.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            h.decompose()
        ###

    return elements


def get_html_content(url: str):
        logger = custom_logger.create_logger('GET HTML CONTENT')

        response = requests.get(url, timeout=20)
        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f'Correct response from {url}')
            return response.text

        flare_headers = {'Content-Type': 'application/json'}
        response = requests.post(FLARESOLVER_URL, headers=flare_headers, json={
                                'cmd': 'request.get', 'url': url, 'maxTimeout': 60000})

        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f'Correct response with FlareSolver from {url}')
            response_json = response.json()
            return response_json['solution']['response']
        logger.warning(f'Error with request {response.status_code}')



def get_element_by_key(json_data, key, value):
    for item in json_data:
        if item[key] == value:
            return item
    return json_data[0]


def decode_chapter(html_content: str, host: str = None):
    logger = custom_logger.create_logger("DECODING CHAPTER")

    if not html_content:
        logger.exception('No html found')
        return

    soup = BeautifulSoup(html_content, 'html.parser')
    logger.info(f'Getting decoding strategy for {host}')

    decoding = get_element_by_key(DECODE_GUIDE, 'host', host)
    if decoding['host'] != host:
        logger.warning(f'{host} not found, using default decoding')

    chapter = {'content': '', 'title': None}
    title_decoding = decoding['title']

    title = find_elements(soup, element=title_decoding['element'],
                          _id=title_decoding['id'],
                          _class=title_decoding['class'])
    if title:
        title = title[0].get_text()
        chapter['title'] = title

        
        chapter['content'] += f'<h4>{title}</h4>'
        logger.info(f'Chapter title: {title}')

    else:
        logger.warning('No title found')

    content_decoding = decoding['content']
    paragraphs = find_elements(soup, element=content_decoding['element'],
                               _id=content_decoding['id'],
                               _class=content_decoding['class'])

    if paragraphs:
        logger.info(f'{len(paragraphs)} paragraphs found')
        for paragraph in paragraphs:
            chapter['content'] += str(paragraph)

    else:
        logger.exception('No paragraphs found')
        return

    return chapter


def custom_placeholder_title(book: epub.EpubBook):
    book_title = book.title
    n_vol = book_title.split(' ').pop()
    n_vol = n_vol.split('.')[0]
    try:
        n_vol = int(n_vol) - 1
    except ValueError:
        n_vol = 0
    n_chap = n_vol * N_CHAPS
    spine = book.spine
    try:
        spine.remove('nav')
        spine.remove('cover')
    except ValueError:
        pass

    title = f'{book_title} {n_vol}_{n_chap + len(spine)}'
    return title


def save_chapter_book(book: epub.EpubBook, content, host: str = None):
    logger = custom_logger.create_logger('SAVING CHAPTER TO BOOK')

    logger.info(f'Using book: {book.title}')
    logger.debug(f'Host: {host}')
    chapter = decode_chapter(content, host)
    if not chapter:
        logger.exception(f'Failed to decode chapter for {book.title}')
        return

    title = chapter["title"]
    if not title:
        title = custom_placeholder_title(book)
        logger.warning(f'Title not found, using placeholder title: {title}')

    title = title.strip()
    cleaned_title = re.sub(r'[^\w\s]', '', title)
    file_title = cleaned_title.replace(' ', '_').lower()
    
    file_name = f'{file_title}.xhtml'
    logger.debug(f'File title: {file_name}')

    c = epub.EpubHtml(title=title, file_name=file_name)
    c.set_content(chapter['content'])
    book.add_item(c)
    logger.info(f'{title} saved to book')

    link = epub.Link(file_name, title, file_title)
    toc = book.toc
    toc.append(link)
    book.toc = toc

    book.spine.append(c)
    return book


def create_book(title, language='en', author=None, cover_image=None, collection=None, metadata: list = None):

    book = epub.EpubBook()
    book.set_title(title)
    book.set_language(language)
    book.add_metadata('DC', 'subject', 'Novela Web')
    book.add_metadata('DC', 'subject', 'Scrapped')

    if author:
        book.add_author(author)

    if metadata:
        for item in metadata:
            book.add_metadata(item['type'],
                              item['name'],
                              item['value'],
                              item['others'])

    # if collection:
    #     book.add_metadata('OPF', 'meta', collection['num'], {'refines': 'id-3', 'property': 'group-position'})
    #     book.add_metadata('OPF', 'meta', 'series', {'refines': 'id-3', 'property': 'collection-type'})
    #     book.add_metadata('OPF', 'meta', 'test', {'id': 'id-3', 'property': 'belongs-to-collection'})


    if cover_image:
        book.set_cover('cover.jpg', open(f'{cover_image}', 'rb').read())

        book.spine += ['cover']

    book.spine.append('nav')
    return book


def save_chapters_to_epub(title, chapter_list: list[str], language='en', cover_image=None, author=None, n_vol=None):
    logger = custom_logger.create_logger("WEB CHAPTERS TO EPUB")

    book_title = title + (f' Vol {n_vol}' if n_vol else '')
    logger.info(f'Creating Epub: {book_title}')
    if cover_image:
        logger.info(f'With cover at {cover_image}')

    if not os.path.exists(f'{OUTPUT_PATH}/{title}'):
        os.mkdir(f'{OUTPUT_PATH}/{title}')

    output_filepath = f'{OUTPUT_PATH}/{title}/{book_title}.epub'
    if os.path.exists(output_filepath):
        logger.warning(f'{output_filepath} already exists')
        return

    temp_dirpath = f'{TMP_PATH}/{title}/{book_title}'
    if not os.path.exists(temp_dirpath):
        logger.info(f'Creating temp dirpath at {temp_dirpath}')
        os.makedirs(temp_dirpath)

    logger.info(
        f'Starting saving {len(chapter_list)} chapters for {title} at {output_filepath}')

    logger.info(f'Start requesting {len(chapter_list)} chapters')
    for i, chapter_url in enumerate(chapter_list):
        # Check temp path
        n_chap = (4 - len(str(i+1))) * '0' + str(i+1)
        chapter_name = chapter_url.split('/').pop()
        chapter_name = chapter_name.split('.')[0]

        temp_filepath = f'{temp_dirpath}/{n_chap}_{chapter_name}.html'
        logger.info(f'Trying to obtain chapter at: {temp_filepath}')

        if os.path.exists(temp_filepath):
            logger.info(f'Obtained chapter {temp_filepath} from temp')
            continue

        n_try = 1
        content = None
        while not content and n_try < MAX_RETRIES:
            logger.info(f'Trying to get {chapter_url}, try: {n_try}')
            try:
                content = get_html_content(chapter_url)
            except:
                logger.exception('Error, response failure')
                pass
        if not content:
            logger.exception('Error, response failure')
            return

        with open(temp_filepath, 'w', encoding='UTF-16') as f:
            f.write(content)
            logger.info(f'Writed content to {temp_filepath}')
    collection = {'title': title, 'num': n_vol}
    book = create_book(book_title, language=language,
                       author=author, cover_image=cover_image, collection=collection)
    logger.info(f'Epub created: {book_title}')

    with os.scandir(temp_dirpath) as entries:
        logger.info(f'Saving to book {book_title}')

        for i, chapter in enumerate(entries):
            # if i > 1:
            #     continue

            with open(chapter.path, 'r', encoding='UTF-16') as f:
                host = obtain_host(chapter_list[i])
                content = f.read()
                book = save_chapter_book(book, content, host)

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    epub.write_epub(output_filepath, book)

    logger.info(f'{book_title} succesfully saved')
    return output_filepath


def remove_duplicates_in_list(string_list):
    string_list = string_list[::-1]
    string_list = list(dict.fromkeys(string_list))
    string_list = string_list[::-1]
    return string_list


def decode_index(html_content: str, host: str = None):
    logger = custom_logger.create_logger("DECODING INDEX")

    if not html_content:
        logger.exception('No html found')
        return

    soup = BeautifulSoup(html_content, 'html.parser')
    logger.info(f'Getting decoding strategy for {host}')

    decoding = get_element_by_key(DECODE_GUIDE, 'host', host)
    if decoding['host'] != host:
        logger.warning(f'{host} not found, using default decoding')

    index_decoding = decoding['index']
    searching = index_decoding['pagination']
    links = []
    link_tags = find_elements(soup, select=index_decoding['link'])

    if not link_tags:
        logger.info('No links found')
    else:
        links = [link['href'] for link in link_tags]
        logger.info(f'{len(links)} links found')

    if not searching:
        logger.info('No pagination.')
        next_page = None
    else:
        next_page = find_elements(soup, select=index_decoding['next_page'])
        if not next_page:
            logger.info('No next page found')

    return links, next_page


def check_links(links: list[str], host: str = None):
    logger = custom_logger.create_logger("CHECKING LINKS")

    decoding = get_element_by_key(DECODE_GUIDE, 'host', host)
    if decoding['host'] != host:
        logger.warning(f'{host} not found, using default decoding')

    reverse = decoding['index']['reverse']

    if reverse:

        links.reverse()
        logger.info('List reversed.')

    return links


def search_index(url: str):
    logger = custom_logger.create_logger("SEARCHING INDEX")

    if not url:
        logger.warning('No url provided')
        return

    host = obtain_host(url)

    decoding = get_element_by_key(DECODE_GUIDE, 'host', host)
    if decoding['host'] != host:
        logger.warning(f'{host} not found, using default decoding')

    chapter_list = []

    logger.info(f'Obtaining chapters from {url}')
    with open('toc.html', 'r', encoding='UTF-16') as f:
        content = f.read()
    # content = get_html_content(url)
    links, next_page = decode_index(content, host)
    chapter_list += links

    while next_page:
        logger.info(f'Obtaining chapters from {url}')
        content = get_html_content(next_page)
        links, next_page = decode_index(content, host)
        if not links:
            logger.exception(f'No chapters found at {url}')

        chapter_list += links

    logger.info(f'{len(chapter_list)} chapters found')
    chapter_list = check_links(chapter_list, host)
    return chapter_list


def get_chapter_list(novel_toc_url):
    with open('toc.html', 'r', encoding='UTF-16') as f:
        content = f.read()
    soup = BeautifulSoup(content, 'html.parser')
    chapters = soup.find_all('a')
    chapter_list = []
    for chapter_url in chapters:
        if chapter_url.get('href') == novel_toc_url:
            continue
        if chapter_url.get('href').startswith(novel_toc_url):
            chapter_list.append(chapter_url.get('href'))

    chapter_list = remove_duplicates_in_list(chapter_list)
    return chapter_list


def save_novel_to_epub(novel_title, novel_chapter_list, n_chaps=N_CHAPS, language='en', cover_image=None, author=None):
    vol = 1
    while len(novel_chapter_list) > 0:
        chapters_n_vol = novel_chapter_list[:n_chaps]
        n_vol = ('0' if vol < 10 else '') + str(vol)
        save_chapters_to_epub(novel_title, chapters_n_vol, language=language,
                              cover_image=cover_image, author=author, n_vol=n_vol)
        novel_chapter_list = novel_chapter_list[n_chaps:]
        vol += 1


if __name__ == '__main__':
    #test
    chapters = search_index('https://novelbin.me/novel-book/the-ultimate-support-character')
    save_novel_to_epub('Ultimate Support Character',
                       chapters,
                       cover_image='gmnnv4rfimr.jpg',
                       author='Dyrem')
    print('test')