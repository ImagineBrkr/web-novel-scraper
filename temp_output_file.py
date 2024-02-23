import os
from pathlib import Path
import custom_logger
from dotenv import load_dotenv

load_dotenv()

CURRENT_DIR = Path(__file__).resolve().parent

TEMP_FILE_LOCATION = os.getenv('TEMP_FILE_LOCATION', F'{CURRENT_DIR}/tmp')
OUTPUT_FILE_LOCATION = os.getenv('OUTPUT_FILE_LOCATION', F'{CURRENT_DIR}/output')

logger = custom_logger.create_logger('GET OUTPUT OR TEMP FILE')

def save_to_temp_file(path: str, content):
    full_path = Path(TEMP_FILE_LOCATION) / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(full_path, 'w', encoding='UTF-16') as file:
            file.write(content)
    except Exception as e:
        logger.error(f'Error saving text file: {e}')
    

def load_from_temp_file(path: str):
    full_path = Path(TEMP_FILE_LOCATION) / path
    try:
        if full_path.exists():
            with open(full_path, 'r', encoding='UTF-16') as file:
                return file.read()
    except Exception as e:
        logger.error(f'Error loading temp file: {e}')
    return None

def clean_temp_file(path: str):
    full_path = Path(TEMP_FILE_LOCATION) / path
    try:
        if full_path.exists():
            full_path.unlink(missing_ok=True)
    except Exception as e:
        logger.error(f'Error cleaning temp file: {e}')