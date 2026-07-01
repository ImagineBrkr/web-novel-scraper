import pytest
from pathlib import Path
from web_novel_scraper.decode import Decoder
from web_novel_scraper.config_manager import ScraperConfig
from web_novel_scraper.request_helper import RequestHelper

# Path to the decode_guide.json
DECODE_GUIDE_PATH = (
    Path(__file__).parent.parent.parent
    / "web_novel_scraper"
    / "decode_guide"
    / "decode_guide.json"
)

# For every Host we validate
# For a sample chapter URL, the title and a content sample.
# For the TOC, we validate:
# - The URL of the first chapter in the TOC
# - The URL of a chapter at a fixed index
# - If the novel has pagination:
# -- The amount of chapter URLs in a single page
# -- The next page URL
# - If the novel does not have pagination:
# -- A minimum amount of chapter URLs (may have increased)


HOSTS_TEST_DATA = {
    "fanmtl.com": {
        "enabled": True,
        "sample_novel_url": "https://www.fanmtl.com/novel/shadow-slave.html",
        "sample_chapter_url": "https://fanmtl.com/novel/shadow-slave_30.html",
        "fixed_chapter_index": 30,
        "expected": {
            "chapter_title": "30 Starless Void",
            "chapter_content_sample": "<p>With a soft sigh, he habitually looked for his shadow. However, due to the total darkness that surrounded him, it couldn't really be seen. He just barely felt its presence. </p>",
            "chapter_urls_count": 100,
            "first_chapter_url": "https://fanmtl.com/novel/shadow-slave_1.html",
            "fixed_chapter_url": "https://fanmtl.com/novel/shadow-slave_31.html",
            "next_toc_page_url": "https://www.fanmtl.com/e/extend/fy.php?page=1&wjm=shadow-slave",
        },
    },
    "freewebnovel.com": {
        "enabled": True,
        "sample_novel_url": "https://freewebnovel.com/novel/shadow-slave",
        "sample_chapter_url": "https://freewebnovel.com/novel/shadow-slave/chapter-40",
        "fixed_chapter_index": 19,
        "expected": {
            "chapter_title": "Chapter 40: Weak Point",
            "chapter_content_sample": "Sunny counted the monsters: one, two, three... five...",
            "chapter_urls_count": 200,
            "first_chapter_url": "https://freewebnovel.com/novel/shadow-slave/chapter-1",
            "fixed_chapter_url": "https://freewebnovel.com/novel/shadow-slave/chapter-20",
            "next_toc_page_url": "https://freewebnovel.com/novel/shadow-slave?ajax=chapters&page=2&pageSize=200",
        },
    },
    "novellive.net": {
        "enabled": True,
        "sample_novel_url": "https://novellive.net/book/shadow-slave",
        "sample_chapter_url": "https://novellive.net/book/shadow-slave/chapter17-three-simple-words",
        "fixed_chapter_index": 36,
        "expected": {
            "chapter_title": "Chapter 17 Three Simple Words",
            "chapter_content_sample": "unny stared at these three simple words, feeling like there was a bottomless abyss opening right beneath his feet.",
            "chapter_urls_count": 40,
            "first_chapter_url": "https://novellive.net/book/shadow-slave/chapter1-nightmare-begins",
            "fixed_chapter_url": "https://novellive.net/book/shadow-slave/chapter37-getting-to-know-each-other",
            "next_toc_page_url": "https://novellive.net/book/shadow-slave/2",
        },
    },
    "royalroad.com": {
        "enabled": True,
        "sample_novel_url": "https://www.royalroad.com/fiction/65609/rapturous-rhapsody",
        "sample_chapter_url": "https://www.royalroad.com/fiction/65609/rapturous-rhapsody/chapter/1145463/isolation-4",
        "fixed_chapter_index": 18,
        "expected": {
            "chapter_title": "Isolation 4",
            "chapter_content_sample": "To him, it had been almost a year.",
            "chapter_urls_count_threshold": 113,
            "first_chapter_url": "https://www.royalroad.com/fiction/65609/rapturous-rhapsody/chapter/1137229/volume-1-confinement-1",
            "fixed_chapter_url": "https://www.royalroad.com/fiction/65609/rapturous-rhapsody/chapter/1152834/desolation-4",
        },
    },
    "novelbin.me": {
        "enabled": False,
        "sample_novel_url": "https://novelbin.me/novel-book/shadow-slave",
        "sample_chapter_url": "https://novelbin.me/novel-book/shadow-slave/chapter-1332-splinters",
        "fixed_chapter_index": 56,
        "expected": {
            "chapter_title": "Chapter 1332 Splinters",
            "chapter_content_sample": "The steering oar... was gone. There was only the piece Nephis was holding and a scattering of wet splinters on the deck. The rest of it had shattered, and was washed away by the raging current.",
            "chapter_urls_count_threshold": 3024,
            "first_chapter_url": "https://novelbin.me/novel-book/shadow-slave/chapter-1-nightmare-begins",
            "fixed_chapter_url": "https://novelbin.me/novel-book/shadow-slave/chapter-57-use-of-weapons",
        },
    },
    "novelbin.com": {
        "enabled": False,
        "sample_novel_url": "https://novelbin.com/novel-book/shadow-slave",
        "sample_chapter_url": "https://novelbin.com/b/shadow-slave/chapter-1190-battle-of-the-black-skull-4",
        "fixed_chapter_index": 125,
        "expected": {
            "chapter_title": "Chapter 1190 Battle of the Black Skull (4)",
            "chapter_content_sample": "Their eyes met for a moment, and then, the Ascended lunged into an attack. ",
            "chapter_urls_count_threshold": 3026,
            "first_chapter_url": "https://novelbin.me/novel-book/shadow-slave/chapter-1-nightmare-begins",
            "fixed_chapter_url": "https://novelbin.me/novel-book/shadow-slave/chapter-126-effie",
        },
    },
    "hiraethtranslation.com": {
        "enabled": True,
        "sample_novel_url": "https://hiraethtranslation.com/novel/survival-strategy-for-weak-territories/",
        "sample_chapter_url": "https://hiraethtranslation.com/novel/survival-strategy-for-weak-territories/chapter-40/",
        "fixed_chapter_index": 4,
        "expected": {
            "chapter_title": "Chapter 40 - 26th, Multiple Choice Question",
            "chapter_content_sample": "Since there are a certain number of nobles in vestments who do not own lands in the capital, several families are of higher rank.",
            "chapter_urls_count_threshold": 22,
            "first_chapter_url": "https://hiraethtranslation.com/novel/survival-strategy-for-weak-territories/chapter-29/",
            "fixed_chapter_url": "https://hiraethtranslation.com/novel/survival-strategy-for-weak-territories/chapter-33/",
        },
    },
    "hostednovel.com": {
        "enabled": True,
        "sample_novel_url": "https://hostednovel.com/novel/shuras-wrath",
        "sample_chapter_url": "https://hostednovel.com/novel/shuras-wrath/chapter-799",
        "fixed_chapter_index": 63,
        "expected": {
            "chapter_title": "Chapter 799 – Birthday (3)",
            "chapter_content_sample": '"Eh? Personally carved¦ by Aunty Gu?"',
            "chapter_urls_count": 100,
            "first_chapter_url": "https://hostednovel.com/novel/shuras-wrath/chapter-0",
            "fixed_chapter_url": "https://hostednovel.com/novel/shuras-wrath/chapter-63",
            "next_toc_page_url": "https://hostednovel.com/novel/shuras-wrath?page=2#chapters",
        },
    },
    "scribblehub.com": {
        "enabled": True,
        "sample_novel_url": "https://www.scribblehub.com/series/622545/rapturous-rhapsody/",
        "sample_chapter_url": "https://www.scribblehub.com/read/622545-rapturous-rhapsody/chapter/1024720/",
        "fixed_chapter_index": 6,
        "expected": {
            "chapter_title": "Dream 7",
            "chapter_content_sample": "Hell, even Worm had a few.",
            "chapter_urls_count": 50,
            "first_chapter_url": "https://www.scribblehub.com/read/622545-rapturous-rhapsody/chapter/778136/",
            "fixed_chapter_url": "https://www.scribblehub.com/read/622545-rapturous-rhapsody/chapter/813143/",
            "next_toc_page_url": "?toc=2#content1",  # TODO - Decoder should return an absolute URL
        },
    },
    "novelcool.com": {
        "enabled": True,
        "sample_novel_url": "https://www.novelcool.com/novel/Shadow-Slave.html",
        "sample_chapter_url": "https://www.novelcool.com/chapter/Shadow-Slave-Chapter-2493-White-Walls/13642483/",
        "fixed_chapter_index": 200,
        "expected": {
            "chapter_title": "Shadow Slave  Chapter 2493– White Walls",
            "chapter_content_sample": "Morgan was not taking in the darkly stunning landscape, though. ",
            "chapter_urls_count_threshold": 2497,
            "first_chapter_url": "https://www.novelcool.com/chapter/Shadow-Slave-Chapter-1/7332148/",
            "fixed_chapter_url": "https://www.novelcool.com/chapter/Shadow-Slave-Chapter-201/7364433/",
        },
    },
    "foxaholic.com": {
        "enabled": True,
        "sample_novel_url": "https://www.foxaholic.com/novel/until-i-become-_____-in-the-game-world-i-reincarnated-into/",
        "sample_chapter_url": "https://www.foxaholic.com/novel/until-i-become-_____-in-the-game-world-i-reincarnated-into/extra-1/",
        "fixed_chapter_index": 24,
        "expected": {
            "chapter_title": "Extra 1 - Three Years Later Part I",
            "chapter_content_sample": "One such creature was the yellow sheep-like monster, classified as an E-rank, the weakest. It quietly lived at the base of the silvery white mountains.",
            "chapter_urls_count_threshold": 229,
            "first_chapter_url": "https://www.foxaholic.com/novel/until-i-become-_____-in-the-game-world-i-reincarnated-into/0-1/",
            "fixed_chapter_url": "https://www.foxaholic.com/novel/until-i-become-_____-in-the-game-world-i-reincarnated-into/23/",
        },
    },
    "empirenovel.com": {
        "enabled": True,
        "sample_novel_url": "https://www.empirenovel.com/novel/108-maidens-of-destiny",
        "sample_chapter_url": "https://www.empirenovel.com/novel/108-maidens-of-destiny/745",
        "fixed_chapter_index": 12,
        "expected": {
            "chapter_title": "Chapter 745: Huang Seeks Feng",
            "chapter_content_sample": "Li Shishi showed a bit of interest. The graceful woman’s legs stepped into the air, her phoenix brilliant as she took flight with her wings. Her slender waist seemed to dance. The true killing move was emerging, like a phoenix’s arrogant wings. Purple Thunder was immediately smashed. ",
            "chapter_urls_count": 30,
            "first_chapter_url": "https://www.empirenovel.com/novel/108-maidens-of-destiny/738",
            "fixed_chapter_url": "https://www.empirenovel.com/novel/108-maidens-of-destiny/750",
            "next_toc_page_url": "https://www.empirenovel.com/novel/108-maidens-of-destiny?page=2",
        },
    },
    "novelingua.com": {
        "enabled": True,
        "sample_novel_url": "https://novelingua.com/page-90/",
        "sample_chapter_url": "https://novelingua.com/finest-servant-chapter-026/",
        "fixed_chapter_index": 121,
        "expected": {
            "chapter_title": "Chapter 26 Cunningly Seizing Wealth and Power (Part 1)",
            "chapter_content_sample": "He arrived early at the Xiao family's entrance and saw that there were already countless diligent people gathered around two red lists, making a lot of noise.",
            "chapter_urls_count_threshold": 691,
            "first_chapter_url": "https://novelingua.com/page-107/",
            "fixed_chapter_url": "https://novelingua.com/finest-servant-chapter-122/",
        },
    },
    "nobadnovel.com": {
        "enabled": True,
        "sample_novel_url": "https://www.nobadnovel.com/series/as-long-as-i-outlast-you-all-ill-be-invincible",
        "sample_chapter_url": "https://www.nobadnovel.com/series/as-long-as-i-outlast-you-all-ill-be-invincible/chapter-350-back-in-time",
        "fixed_chapter_index": 35,
        "expected": {
            "chapter_title": "Back in Time",
            "chapter_content_sample": "These two Daos could be said to be entangled with each other.",
            "chapter_urls_count_threshold": 671,
            "first_chapter_url": "https://www.nobadnovel.com/series/as-long-as-i-outlast-you-all-ill-be-invincible/chapter-1-i-want-to-get-up",
            "fixed_chapter_url": "https://www.nobadnovel.com/series/as-long-as-i-outlast-you-all-ill-be-invincible/chapter-36-the-great-song-dynasty",
        },
    },
    "ncode.syosetu.com": {
        "enabled": True,
        "sample_novel_url": "https://ncode.syosetu.com/n0301hw/",
        "sample_chapter_url": "https://ncode.syosetu.com/n0301hw/62/",
        "fixed_chapter_index": 12,
        "expected": {
            "chapter_title": "静寂への依存",
            "chapter_content_sample": "計算も打算もない、驚くほど自然な距離感。",
            "chapter_urls_count": 100,
            "first_chapter_url": "https://ncode.syosetu.com/n0301hw/1/",
            "fixed_chapter_url": "https://ncode.syosetu.com/n0301hw/13/",
            "next_toc_page_url": "https://ncode.syosetu.com/n0301hw/?p=2",
        },
    },
    "kakuyomu.jp": {
        "enabled": True,
        "sample_novel_url": "https://kakuyomu.jp/works/16818093081705564239",
        "sample_chapter_url": "https://kakuyomu.jp/works/16818093081705564239/episodes/16818093081784714284",
        "fixed_chapter_index": 33,
        "expected": {
            "chapter_title": "その後の世界　綿野健の心理アセスメント",
            "chapter_content_sample": "　――尻のあたりから安い合成皮の臭いがする。この施設の椅子の座面素材ではない。車の趣味が悪いな。国産に乗ればいい。",
            "chapter_urls_count_threshold": 98,
            "first_chapter_url": "https://kakuyomu.jp/works/16818093081705564239/episodes/16818093081706378721",
            "fixed_chapter_url": "https://kakuyomu.jp/works/16818093081705564239/episodes/16818093081778304422",
        },
    },
    "noveltrust.com": {
        "enabled": True,
        "sample_novel_url": "https://noveltrust.com/book/shadow-slave",
        "sample_chapter_url": "https://noveltrust.com/book/shadow-slave/chapter-3025-true-peace",
        "fixed_chapter_index": 31,
        "expected": {
            "chapter_title": "Chapter 3025 True Peace",
            "chapter_content_sample": "Slowly, he cast his shadow sense outward,",
            "chapter_urls_count": 40,
            "first_chapter_url": "https://noveltrust.com/book/shadow-slave/chapter1-nightmare-begins",
            "fixed_chapter_url": "https://noveltrust.com/book/shadow-slave/chapter32-making-a-choice",
            "next_toc_page_url": "https://noveltrust.com/book/shadow-slave/2",
        },
    },
    "69shuba.com": {
        "enabled": True,
        "sample_novel_url": "https://69shuba.com/book/37684.htm",
        "sample_chapter_url": "https://www.69shuba.com/txt/37684/26556886",
        "fixed_chapter_index": 176,
        "expected": {
            "chapter_title": "第147章 147：行动（五）【求月票】",
            "chapter_content_sample": "仪态翩然，斯文儒雅，恍若谪仙。",
            "chapter_urls_count_threshold": 1626,
            "first_chapter_url": "https://www.69shuba.com/txt/37684/26098115",
            "fixed_chapter_url": "https://www.69shuba.com/txt/37684/26677927",
        },
    },
    "botitranslation.com": {
        "enabled": True,
        "sample_novel_url": "https://www.botitranslation.com/book/20346-pretending-to-cultivate-in-kindergarten",
        "sample_chapter_url": "https://api.mystorywave.com/story-wave-backend/api/v1/content/chapters/1630396",
        "fixed_chapter_index": 308,
        "expected": {
            "chapter_title": 'Chapter 80: What Does "Caring" Mean, Zhengran?',
            "chapter_content_sample": "She waved at Lin Zhengran before turning to wave at Han Wenwen and Jiang Xueli in the distance.",
            "chapter_urls_count_threshold": 378,
            "first_chapter_url": "https://api.mystorywave.com/story-wave-backend/api/v1/content/chapters/1623242",
            "fixed_chapter_url": "https://api.mystorywave.com/story-wave-backend/api/v1/content/chapters/1654610",
        },
    },
    "fucknovelpia.com": {
        "enabled": True,
        "sample_novel_url": "https://fucknovelpia.com/novel/the-main-heroines-are-trying-to-kill-me",
        "sample_chapter_url": "https://fucknovelpia.com/chapter.php?hash=f612fa9780452e83511bdfeb8c90f40e5c1c4e45&ch=0502",
        "fixed_chapter_index": 182,
        "expected": {
            "chapter_title": "Chapter 502",
            "chapter_content_sample": "At those words, the corners of Frey’s lips curled into his usual arrogant smirk.",
            "chapter_urls_count_threshold": 526,
            "first_chapter_url": "https://fucknovelpia.com/chapter.php?hash=f612fa9780452e83511bdfeb8c90f40e5c1c4e45&ch=0001",
            "fixed_chapter_url": "https://fucknovelpia.com/chapter.php?hash=f612fa9780452e83511bdfeb8c90f40e5c1c4e45&ch=0183",
        },
    },
    "novelarrow.com": {
        "enabled": True,
        "sample_novel_url": "https://novelarrow.com/novel/my-gene-evolves-infinitely",
        "sample_chapter_url": "https://novelarrow.com/chapter/my-gene-evolves-infinitely/chapter-749-completing-the-origin-core",
        "fixed_chapter_index": 265,
        "expected": {
            "chapter_title": "Chapter 749: Completing The Origin Core",
            "chapter_content_sample": "Nu Xing looked at Lu Yuan and said with a smile.",
            "chapter_urls_count_threshold": 780,
            "first_chapter_url": "https://novelarrow.com/chapter/my-gene-evolves-infinitely/chapter-1-awakening-boundless-potential",
            "fixed_chapter_url": "https://novelarrow.com/chapter/my-gene-evolves-infinitely/chapter-266-this-trump-card-is-enough-2",
        },
    },
}


@pytest.fixture(
    scope="class",
    params=[h for h in HOSTS_TEST_DATA.keys() if HOSTS_TEST_DATA[h]["enabled"]],
)
def host(request):
    return request.param


@pytest.fixture(scope="class")
def decoder(host):
    """Create a Decoder instance with the decode_guide for the specified host"""
    return Decoder(host=host, decode_guide_file=DECODE_GUIDE_PATH)


@pytest.fixture(scope="class")
def request_helper(host):
    config = ScraperConfig()
    config.set_host(host)

    request_config = config.config_options["request_config"]
    request_cookies = request_config.get("request_cookies", {})
    if host == "scribblehub.com":
        request_cookies = {"toc_show": "50"}
    helper = RequestHelper(
        request_timeout=120,
        time_between_retries=10,
        retries_number=6,
        cookies=request_cookies,
        time_between_requests=request_config.get("request_time_between_requests"),
    )

    if request_config.get("force_flaresolver"):
        helper.enable_flaresolverr(
            flaresolverr_url=request_config.get("flaresolver_url")
        )

    yield helper

    helper._post_cleanup()


@pytest.fixture(scope="class")
def toc_html(host, request_helper, decoder):
    """Fetch and cache HTML content from the TOC"""
    test_data = HOSTS_TEST_DATA[host]
    toc_main_url = decoder.toc_main_url_process(test_data["sample_novel_url"])
    return request_helper.get_url_content(url=toc_main_url)


@pytest.fixture(scope="class")
def chapter_html(host, request_helper):
    """Fetch and cache HTML content from the chapter"""
    test_data = HOSTS_TEST_DATA[host]
    return request_helper.get_url_content(url=test_data["sample_chapter_url"])


@pytest.mark.host_validation
class TestHostsValidation:
    """
    Parametrized tests for all enabled hosts.

    Each test validates that the decoder can extract:
    - Chapter title
    - Chapter content (checking for expected content sample)
    - Index URLs (checking minimum count)
    """

    def test_host_decode_guide_exists(self, decoder):
        """Verify that the host has a decode guide entry"""
        assert decoder.host == decoder.host
        assert decoder.decode_guide is not None

    def test_chapter_title_extraction(self, decoder, chapter_html):
        """
        Test that chapter title can be extracted and matches expected value
        """
        test_data = HOSTS_TEST_DATA[decoder.host]
        extracted_title = decoder.get_chapter_title(chapter_html)

        assert extracted_title is not None, "Chapter Title is empty"
        assert extracted_title == test_data["expected"]["chapter_title"]

    def test_chapter_content_extraction(self, decoder, chapter_html):
        """
        Test that chapter content can be extracted and contains expected sample
        """
        test_data = HOSTS_TEST_DATA[decoder.host]

        extracted_content = decoder.get_chapter_content(
            chapter_html,
            decoder.title_in_content(),
            decoder.get_chapter_title(chapter_html),
        )
        assert extracted_content is not None, "Chapter Content is empty"
        assert test_data["expected"]["chapter_content_sample"] in extracted_content

    def test_index_urls_count(self, decoder, toc_html):
        """
        Test that chapter URLs count
        If it does not have pagination, it should be above a minimum threshold
        """
        test_data = HOSTS_TEST_DATA[decoder.host]

        chapter_urls = decoder.get_chapter_urls(toc_html, test_data["sample_novel_url"])

        assert chapter_urls is not None
        if decoder.has_pagination():
            expected_count = test_data["expected"]["chapter_urls_count"]
            assert len(chapter_urls) == expected_count, (
                f"Expected {expected_count} URLs for {decoder.host}, got {len(chapter_urls)}"
            )
        else:
            expected_count_threshold = test_data["expected"][
                "chapter_urls_count_threshold"
            ]
            assert len(chapter_urls) >= expected_count_threshold, (
                f"Expected at least {expected_count_threshold} URLs for {decoder.host}, got {len(chapter_urls)}"
            )

    def test_next_toc_page_url_extraction(self, decoder, toc_html):
        """
        Test that next_toc_page_url can be extracted from TOC (only for paginated hosts)
        Skips if host doesn't have pagination configured.
        """
        if not decoder.has_pagination():
            pytest.skip(f"Host {decoder.host} does not have pagination configured")

        test_data = HOSTS_TEST_DATA[decoder.host]

        extracted_next_page = decoder.get_toc_next_page_url(toc_html)

        assert extracted_next_page is not None, (
            f"No Next TOC Page URL found for {decoder.host}"
        )
        assert extracted_next_page == test_data["expected"]["next_toc_page_url"], (
            f"Next page URL mismatch for {decoder.host}: got {extracted_next_page}, expected {test_data['expected']['next_toc_page_url']}"
        )

    def test_chapter_at_first_index_from_toc(self, decoder, toc_html):
        """
        Test that the chapter URL at the first index is as expected

        This test ensures that the same chapter URLs appear in the same positions,
        """
        test_data = HOSTS_TEST_DATA[decoder.host]

        chapter_urls = decoder.get_chapter_urls(toc_html, test_data["sample_novel_url"])

        assert chapter_urls is not None, f"No chapter URLs found for {decoder.host}"
        assert len(chapter_urls) > 0, f"Empty chapter URLs list for {decoder.host}"

        expected_first_chapter_url = test_data["expected"]["first_chapter_url"]
        assert chapter_urls[0] == expected_first_chapter_url, (
            f"First chapter URL mismatch for {decoder.host}: got {chapter_urls[0]}, expected {expected_first_chapter_url}"
        )

    def test_chapter_at_fixed_index_from_toc(self, decoder, toc_html):
        """
        Test that the chapter URL at a fixed index is as expected

        This test ensures that the same chapter URLs appear in the same positions,
        """
        test_data = HOSTS_TEST_DATA[decoder.host]

        chapter_urls = decoder.get_chapter_urls(toc_html, test_data["sample_novel_url"])

        fixed_chapter_url = chapter_urls[test_data["fixed_chapter_index"]]
        expected_fixed_chapter_url = test_data["expected"]["fixed_chapter_url"]
        assert fixed_chapter_url == expected_fixed_chapter_url, (
            f"Chapter URL mismatch for {decoder.host} at index {test_data['fixed_chapter_index']}: got {fixed_chapter_url}, expected {expected_fixed_chapter_url}"
        )
