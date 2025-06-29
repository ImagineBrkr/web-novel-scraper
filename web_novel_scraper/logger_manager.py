import logging
import os
from dotenv import load_dotenv

load_dotenv()
logging_levels = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
    "DEFAULT": logging.CRITICAL + 1
}
LOGGING_LEVEL = os.getenv('SCRAPER_LOGGING_LEVEL', 'INFO').upper()
LOGGING_FILE = os.getenv('SCRAPER_LOGGING_FILE', None)

if LOGGING_LEVEL in logging_levels:
    LOGGING_LEVEL = logging_levels[LOGGING_LEVEL]
else:
    LOGGING_LEVEL = logging_levels['DEFAULT']

process = "main"

class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    green = "\x1b[32;20m"
    reset = "\x1b[0m"
    format_str = f"%(asctime)s - %(levelname)s {reset}- %(operation)s - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: green + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def format(self, record):
        if LOGGING_FILE:
            log_fmt = self.format_str.replace(self.reset, '')
        else:
            log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def create_logger(operation):
    logger = logging.getLogger(process)
    logger.setLevel(LOGGING_LEVEL)

    if not logger.handlers:
        if LOGGING_FILE:
            lh = logging.FileHandler(LOGGING_FILE, encoding='utf-8')
        else:
            lh = logging.StreamHandler()
        lh.setLevel(LOGGING_LEVEL)
        lh.setFormatter(CustomFormatter())
        logger.addHandler(lh)

    extra = {'operation': operation}
    logger = logging.LoggerAdapter(logger, extra)

    return logger


def set_process(new_process):
    global process
    process = new_process
