from web_novel_scraper.io_helpers.utils import IOUtils, IOUtilsError, logger, _get_element_by_key
from web_novel_scraper.utils import ScraperError

class LoadDecodeGuideError(ScraperError):
    pass

def load_decode_guide(path: str, host: str) -> dict:
    """Loads full Decode Guide from a JSON file at *path*. Returns the Decode Guide for the specified *host*."""

    logger.debug(f"Attempting to load Decode Guide File from {path}")

    try:
        decode_guide = IOUtils.read_json_file(path = path, type = list)
        if not decode_guide:
            raise LoadDecodeGuideError(f"Decode Guide File at {path} is empty.")

    except IOUtilsError as e:
        raise LoadDecodeGuideError(e) from e

    logger.debug(f"Successfully loaded Decode Guide File from {path}, loading Decode Guide for Host {host}.")

    host_decode_guide = _get_element_by_key(decode_guide, 'host', host)
    if host_decode_guide is None:
        raise LoadDecodeGuideError(f"No Decode Guide found for Host {host} in {path}.")

    return host_decode_guide
