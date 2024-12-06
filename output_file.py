import os
import json
from pathlib import Path
import shutil
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
    toc_preffix: str = "toc"

    def __init__(self,
                 main_dir: str,
                 novel_location: str = None):
        self.main_dir = main_dir
        if novel_location:
            self.novel_location = novel_location
        self.novel_dir = f'{self.novel_location}/{self.main_dir}'
        self.tmp_dir = f'{self.novel_dir}/tmp'
        self.output_dir = f'{self.novel_dir}/output'
        self.main_json_filename = f'{self.novel_dir}/main.json'
        os.makedirs(self.novel_dir, exist_ok=True)
        os.makedirs(self.tmp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

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
                    logger.debug(f'Content loaded from file: {full_path}')
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

    def save_novel_json(self, main_data: dict):
        try:
            with open(self.main_json_filename, 'w', encoding='UTF-16') as file:
                json.dump(main_data, file, ensure_ascii=False, indent=4)
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

    def save_cover_img(self, img_path: str):
        filename = os.path.basename(img_path)
        destination_path = os.path.join(self.novel_dir, filename)
        try:
            # Copy the cover image
            shutil.copy(img_path, destination_path)
            return filename
        except Exception as e:
            logger.error(f'Error copying the cover image: {e}')
            return None

    def load_cover_img(self, img_path: str):
        cover_img_path = Path(self.novel_dir) / img_path
        try:
            with open(cover_img_path, 'rb') as file:
                content = file.read()
                return content
        except Exception as e:
            logger.error(f'Error loading cover image: {e}')
            return None

    def get_output_dir(self):
        return self.output_dir

    def clear_toc(self):
        toc_pos = 0
        toc_exists = True
        while toc_exists:
            toc_filename = f"{self.toc_preffix}_{toc_pos}.html"
            toc_path = Path(self.tmp_dir) / toc_filename
            toc_exists = toc_path.exists()
            if toc_exists:
                toc_path.unlink()
                toc_pos += 1
                
                
    def add_toc(self, content: str):
        toc_pos = 0
        toc_exists = True
        while toc_exists:
            toc_filename = f"{self.toc_preffix}_{toc_pos}.html"
            toc_path = Path(self.tmp_dir) / toc_filename
            toc_exists = toc_path.exists()
            if toc_exists:
                toc_pos += 1
        try:
            with open(toc_path, 'w', encoding='UTF-16') as file:
                file.write(content)
        except Exception as e:
            logger.error(f'Error saving text file: {e}')

    def get_toc(self, pos_idx: int):
        toc_filename = f"{self.toc_preffix}_{pos_idx}.html"
        return self.load_from_temp_file(toc_filename)

    def get_all_toc(self):
        pos = 0
        tocs = []
        while True:
            toc_content = self.get_toc(pos)
            if toc_content:
                tocs.append(toc_content)
                pos += 1
            else:
                return tocs
