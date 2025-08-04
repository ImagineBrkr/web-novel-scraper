import json
import pytest
from pathlib import Path

DECODE_GUIDE_PATH = Path(__file__).parent.parent / "web_novel_scraper/decode_guide/decode_guide.json"

assert DECODE_GUIDE_PATH.exists(), f"Decode guide file not found at {DECODE_GUIDE_PATH}"
with open(DECODE_GUIDE_PATH, 'r', encoding='utf-8') as f:
    decode_guide_entries = json.load(f)
assert isinstance(decode_guide_entries, list), "Decode guide root must be a list"

# Allowed title_in_content values
TITLE_OPTIONS = {"YES", "NO", "SEARCH"}
# Allowed extract types
EXTRACT_TYPES = {"text", "attr"}

OPTIONAL_BOOLEAN_FLAGS = ('toc_main_url_processor', 'has_pagination', 'add_host_to_chapter')
REQUIRED_SECTIONS = ('title', 'content', 'index')
OPTIONAL_SECTIONS = ('next_page')


@pytest.mark.parametrize("entry", decode_guide_entries, ids=lambda e: e.get('host', '<unknown>'))
def test_decode_guide_entry_schema(entry):
    """
    Validate that each Decode Guide entry follows the required schema.
    """
    # Required top-level key: host
    assert 'host' in entry and isinstance(entry['host'], str) and entry['host'], \
        "Each entry must have a non-empty 'host' string"

    # Optional boolean flags
    for bool_key in OPTIONAL_BOOLEAN_FLAGS:
        if bool_key in entry:
            assert isinstance(entry[bool_key], bool), f"'{bool_key}' must be boolean if present"

    # Optional title_in_content
    if 'title_in_content' in entry:
        assert entry['title_in_content'] in TITLE_OPTIONS, \
            f"'title_in_content' must be one of {TITLE_OPTIONS}"

    # Optional request_config
    if 'request_config' in entry:
        rc = entry['request_config']
        assert isinstance(rc, dict), "'request_config' must be a dictionary"
        # Validate each optional request_config field
        if 'force_flaresolver' in rc:
            assert isinstance(rc['force_flaresolver'], bool), "'force_flaresolver' must be boolean"
        if 'request_timeout' in rc:
            assert isinstance(rc['request_timeout'], (int, float)) and rc['request_timeout'] > 0, \
                "'request_timeout' must be a number > 0"
        if 'request_time_between_retries' in rc:
            assert isinstance(rc['request_time_between_retries'], (int, float)) and rc[
                'request_time_between_retries'] >= 0, \
                "'request_time_between_retries' must be a number >= 0"
        if 'request_retries' in rc:
            assert isinstance(rc['request_retries'], int) and rc['request_retries'] > 1, \
                "'request_retries' must be an integer > 1"

    def validate_section(sec_cfg, name):
        """
        Validate individual section config dict.
        """
        assert isinstance(sec_cfg, dict), f"{name} must be a dict"
        # use_custom_processor exclusivity
        if sec_cfg.get('use_custom_processor'):
            # Must be the only key
            other_keys = set(sec_cfg.keys()) - {'use_custom_processor'}
            assert not other_keys, f"When 'use_custom_processor' is true in {name}, no other keys are allowed"
            return
        # Otherwise, must have selector or at least one of element, id, class
        has_selector = 'selector' in sec_cfg and isinstance(sec_cfg['selector'], str)
        has_parts = any(k in sec_cfg for k in ('element', 'id', 'class'))
        assert has_selector or has_parts, \
            f"{name} must have 'selector' or one of 'element', 'id', 'class' when not using custom processor"
        # Validate optional basic keys
        for key in ('element', 'id', 'class', 'selector', 'attributes'):
            if key in sec_cfg and sec_cfg[key] is not None:
                assert isinstance(sec_cfg[key], str), f"'{key}' in {name} must be a string or null"
        if 'array' in sec_cfg:
            assert isinstance(sec_cfg['array'], bool), f"'array' in {name} must be boolean"
        if 'inverted' in sec_cfg:
            assert isinstance(sec_cfg['inverted'], bool), f"'inverted' in {name} must be boolean"
        # Validate extract
        if 'extract' in sec_cfg:
            ex = sec_cfg['extract']
            assert isinstance(ex, dict), f"'extract' in {name} must be an object"
            assert 'type' in ex and ex['type'] in EXTRACT_TYPES, \
                f"'extract.type' in {name} must be one of {EXTRACT_TYPES}"
            if ex['type'] == 'attr':
                assert 'key' in ex and isinstance(ex['key'], str) and ex['key'], \
                    f"'extract.key' in {name} must be a non-empty string when type is 'attr'"

    # Required sections
    for section in REQUIRED_SECTIONS:
        assert section in entry and isinstance(entry[section], dict), f"Each entry must have a '{section}' dictionary"
        validate_section(entry[section], section)

    # Optional sections
    for section in OPTIONAL_SECTIONS:
        if section in entry:
            assert isinstance(entry[section], dict), f"{section} must be an dictionary if present"
            validate_section(entry[section], section)
