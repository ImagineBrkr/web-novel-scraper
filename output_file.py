import os
from pathlib import Path
import custom_logger
from dotenv import load_dotenv

load_dotenv()

CURRENT_DIR = Path(__file__).resolve().parent

NOVEL_LOCATION = os.getenv('NOVEL_LOCATION', F'{CURRENT_DIR}')

logger = custom_logger.create_logger('GET OUTPUT OR TEMP FILE')

class OutputFiles:
    main_dir: str
    novel_location: str = NOVEL_LOCATION
    novel_dir: str
    tmp_dir: str
    main_json_filename: str

    def __init__(self,
                 main_dir: str,
                 novel_location: str = None):
        self.main_dir = main_dir
        if novel_location:
            self.novel_location = novel_location
        self.novel_dir = f'{self.novel_location}/{self.main_dir}'
        self.tmp_dir = f'{self.novel_dir}/tmp'
        self.main_json_filename = f'{self.novel_dir}/main.json'
        os.makedirs(self.novel_dir, exist_ok=True)
        os.makedirs(self.tmp_dir, exist_ok=True)


    def save_to_temp_file(self, path: str, content):
        full_path = Path(self.tmp_dir) / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(full_path, 'w', encoding='UTF-16') as file:
                file.write(content)
        except Exception as e:
            logger.error(f'Error saving text file: {e}')
    

    def load_from_temp_file(self, path: str):
        full_path = Path(self.tmp_dir) / path
        try:
            if full_path.exists():
                with open(full_path, 'r', encoding='UTF-16') as file:
                    logger.info(f'Content loaded from file: {full_path}')
                    return file.read()
        except Exception as e:
            logger.error(f'Error loading temp file: {e}')
        return None

    def clean_temp_file(self, path: str):
        full_path = Path(self.tmp_dir) / path
        try:
            if full_path.exists():
                full_path.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f'Error cleaning temp file: {e}')
            
    def save_novel_json(self, main_json: str):
        try:
            with open(self.main_json_filename, 'w', encoding='UTF-16') as file:
                file.write(main_json)
        except Exception as e:
            logger.error(f'Error saving main json file: {e}')
            
    def load_novel_json(self):
        full_path = Path(self.main_json_filename)
        try:
            if full_path.exists():
                with open(full_path, 'r', encoding='UTF-16') as file:
                    main_json = file.read()
                    return main_json
        except Exception as e:
            logger.error(f'Error loading main json file: {e}')
        return None