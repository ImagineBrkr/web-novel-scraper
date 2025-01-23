from .file_manager import FileManager
from . import request_manager
import hashlib
from urllib.parse import urlparse
import re
import unicodedata


def generate_file_name_from_url(url: str) -> str:
    # Parsea URL
    parsed_url = urlparse(url)
    # Delete slash
    path = parsed_url.path.strip('/')
    path_parts = path.split('/')
    last_two_parts = path_parts[-2:] if len(path_parts) >= 2 else path_parts
    base_name = '_'.join(last_two_parts) if last_two_parts else 'index'

    # Replace not allowed characters
    safe_base_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', base_name)
    # Limit the path length
    if len(safe_base_name) > 50:
        safe_base_name = safe_base_name[:50]
    # Hash if neccesary
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:8]
    filename = f"{safe_base_name}_{url_hash}.html"
    return filename


def generate_epub_file_name_from_title(title: str) -> str:
    normalized_title = unicodedata.normalize(
        'NFKD', title).encode('ASCII', 'ignore').decode('ASCII')
    normalized_title = normalized_title.lower()
    normalized_title = re.sub(r'[\s\-]+', '_', normalized_title)
    sanitized_title = re.sub(r'[^a-zA-Z0-9_]', '', normalized_title)
    title_hash = hashlib.md5(sanitized_title.encode('utf-8')).hexdigest()[:8]

    max_length = 50
    if len(sanitized_title) > max_length:
        sanitized_title = sanitized_title[:max_length]
    if not sanitized_title:
        sanitized_title = 'chapter'

    filename = f"{sanitized_title}_{title_hash}.xhtml"
    return filename

def delete_duplicates(str_list: list[str]) -> list[str]:
    return list(dict.fromkeys(str_list))

def obtain_host(url: str):
    host = url.split(':')[1]
    # try:
    #     host = url.split(':')[1]
    # except Exception as e:
    #     pass
    while host.startswith('/'):
        host = host[1:]

    host = host.split('/')[0].replace('www.', '')

    return host

def check_exclusive_params(param1: any, param2: any) -> bool:
    return (param1 is None) != (param2 is None)

def create_volume_id(n: int):
    return f'v{n:02}'
