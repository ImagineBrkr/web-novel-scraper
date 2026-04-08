import pytest
import json
from pathlib import Path

from web_novel_scraper.decode import Decoder, HostNotExistsError, TitleInContentOption, DecodeGuideError, \
    ContentExtractionError


@pytest.fixture
def guide_file(tmp_path):
    """
    Create a temporary decode_guide.json file for testing.
    """
    guide = [
        {
            "host": "test.com",
            "title": {
                "element": "h2",
                "extract": {"type": "text"}
            },
            "content": {
                "element": "div",
                "class": "epcontent",
                "array": True
            },
            "index": {
                "selector": "div.eplister ul li a",
                "array": True,
                "extract": {"type": "attr", "key": "href"}
            }
        }
    ]
    path = tmp_path / "decode_guide.json"
    path.write_text(json.dumps(guide))
    return path


@pytest.fixture
def guide_file_title_in_content(tmp_path):
    """
    Create a temporary decode_guide.json file for testing TitleInContentOption.
    """
    guide = [
        {
            "host": "example_default.com"
        },
        {
            "host": "example_yes.com",
            "title_in_content": "YES"
        },
        {
            "host": "example_search.com",
            "title_in_content": "SEARCH"
        },
        {
            "host": "example_no.com",
            "title_in_content": "NO"
        },
        {
            "host": "example_wrong.com",
            "title_in_content": "WRONG"
        }
    ]
    path = tmp_path / "decode_guide_title_in_content_option.json"
    path.write_text(json.dumps(guide))
    return path


@pytest.mark.parametrize("host,expect_error", [
    ("test.com", False),
    ("unknown.com", True),
])
def test_set_host_behavior(guide_file, host, expect_error):
    """
    Test that setting a valid host succeeds and invalid host raises HostNotExistsError.
    """
    if expect_error:
        with pytest.raises(HostNotExistsError):
            Decoder(host=host, decode_guide_file=guide_file, request_config={})
    else:
        decoder = Decoder(host=host, decode_guide_file=guide_file, request_config={})
        assert decoder.host == host


def test_is_index_inverted(guide_file):
    """
    Verify is_index_inverted returns False when not set in Decode Guide.
    """
    decoder = Decoder(host="test.com", decode_guide_file=guide_file, request_config={})
    assert decoder.is_index_inverted() is False


@pytest.mark.parametrize("host,expected_option", [
    ("example_default.com", TitleInContentOption.SEARCH),  # Default Option
    ("example_yes.com", TitleInContentOption.YES),
    ("example_search.com", TitleInContentOption.SEARCH),
    ("example_no.com", TitleInContentOption.NO),
])
def test_title_in_content_variations(guide_file_title_in_content, host, expected_option):
    """
    Verify title_in_content returns the correct enum for each host configuration.
    """
    decoder = Decoder(host=host, decode_guide_file=guide_file_title_in_content, request_config={})
    assert decoder.title_in_content() == expected_option


def test_title_in_content_wrong_option(guide_file_title_in_content):
    """
    Verify title_in_content returns the correct enum for each host configuration.
    """
    decoder = Decoder(host="example_wrong.com", decode_guide_file=guide_file_title_in_content, request_config={})
    with pytest.raises(DecodeGuideError):
        decoder.title_in_content()


def test_get_chapter_urls(guide_file):
    """
    Test extraction of chapter URLs using get_chapter_urls.
    """
    decoder = Decoder(host="test.com", decode_guide_file=guide_file, request_config={})
    html = (
        '<div class="eplister"><ul>'
        '<li><a href="url1">Link1</a></li>'
        '<li><a href="url2">Link2</a></li>'
        '</ul></div>'
    )
    urls = decoder.get_chapter_urls(html)
    assert urls == ["url1", "url2"]


def test_get_chapter_title(guide_file):
    """
    Test extraction of the chapter title using get_chapter_title.
    """
    decoder = Decoder(host="test.com", decode_guide_file=guide_file, request_config={})
    html = '<h2>My Chapter Title</h2>'
    title = decoder.get_chapter_title(html)
    assert title == "My Chapter Title"


def test_no_chapter_title(guide_file):
    """
    Test extraction of the chapter title using get_chapter_title when there is no title.
    """
    decoder = Decoder(host="test.com", decode_guide_file=guide_file, request_config={})
    html = '<h3>My Chapter Title</h3>'
    title = decoder.get_chapter_title(html)
    assert title is None


@pytest.mark.parametrize("title_option,html,expected_startswith", [
    (TitleInContentOption.NO,
     '<div class="epcontent">This is the content</div>',
     '<div'),
    (TitleInContentOption.YES,
     '<div class="epcontent">This is the content</div>',
     '<h4>Chapter'),
    (TitleInContentOption.SEARCH,
     '<div class="epcontent">This is the content of the Chapter</div>',
     '<div'),
    (TitleInContentOption.SEARCH,
     '<div class="epcontent">This is the content</div>',
     '<h4>Chapter'),
])
def test_get_chapter_content_variations(guide_file, title_option, html, expected_startswith):
    """
    Parametrized test for get_chapter_content covering NO, YES, and SEARCH options.
    """
    decoder = Decoder(host="test.com", decode_guide_file=guide_file, request_config={})
    content = decoder.get_chapter_content(html, title_option, "Chapter")
    assert content.startswith(expected_startswith)
    assert 'This is the content' in content


def test_get_chapter_content_no_content_raises(guide_file):
    """
    Should raise ContentExtractionError when no content is found.
    """
    decoder = Decoder(host="test.com", decode_guide_file=guide_file, request_config={})
    with pytest.raises(ContentExtractionError):
        decoder.get_chapter_content('<div>No epcontent here</div>', TitleInContentOption.NO, "Chapter")


def test_toc_main_url_process_returns_input_by_default(guide_file):
    """
    When no custom processor is configured, toc_main_url_process should return the input URL.
    """
    decoder = Decoder(host="test.com", decode_guide_file=guide_file, request_config={})
    test_url = "https://test.com/test"
    assert decoder.toc_main_url_process(test_url) == test_url


def test_has_pagination_default_false(guide_file):
    """
    Verify that has_pagination returns False when not set in the Decode Guide.
    """
    decoder = Decoder(host="test.com", decode_guide_file=guide_file, request_config={})
    assert decoder.has_pagination() is False


def test_find_elements_text_extraction():
    """
    Extract text content when no selector is specified (element only).
    """
    from bs4 import BeautifulSoup
    # Text extraction
    html = '<h1>Hello World</h1>'
    soup = BeautifulSoup(html, 'html.parser')
    decoder_cfg = {"element": "h1", "extract": {"type": "text"}}
    result = Decoder._find_elements(soup, decoder_cfg)
    assert result == "Hello World"


def test_find_elements_attr_extraction():
    """
    Extract attribute value from element.
    """
    from bs4 import BeautifulSoup
    html = '<img src="pic.jpg" alt="Pic" />'
    soup = BeautifulSoup(html, 'html.parser')
    decoder_cfg = {"element": "img", "extract": {"type": "attr", "key": "src"}}
    result = Decoder._find_elements(soup, decoder_cfg)
    assert result == "pic.jpg"


def test_find_elements_array_and_text():
    """
    Return list of text from multiple elements when array=True.
    """
    from bs4 import BeautifulSoup
    html = '<ul><li>One</li><li>Two</li><li>Three</li></ul>'
    soup = BeautifulSoup(html, 'html.parser')
    decoder_cfg = {"element": "li", "array": True, "extract": {"type": "text"}}
    result = Decoder._find_elements(soup, decoder_cfg)
    assert result == ["One", "Two", "Three"]


def test_find_elements_selector_priority_and_xor():
    """
    Use custom selector and XOR to pick the first matching non-empty selector.
    """
    from bs4 import BeautifulSoup
    html = '<div>DivContent</div>'
    soup = BeautifulSoup(html, 'html.parser')
    # First selector fails, second ('div') matches
    decoder_cfg = {"selector": "span XOR div", "array": False}
    result = Decoder._find_elements(soup, decoder_cfg)
    assert hasattr(result, 'name') and result.name == 'div'


def test_find_elements_no_match_returns_none():
    """
    When no elements match, should return None.
    """
    from bs4 import BeautifulSoup
    html = '<p>No match here</p>'
    soup = BeautifulSoup(html, 'html.parser')
    decoder_cfg = {"selector": "span", "array": False}
    result = Decoder._find_elements(soup, decoder_cfg)
    assert result is None

