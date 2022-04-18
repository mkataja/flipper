import codecs
import logging
import re
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

import config

url_regex = re.compile(
    r'(?:https?://)?'
    r'(?:(?:\d+\.\d+\.\d+\.\d+)'
    r'|(?:[\w-]+\.)+[\w-]+)'
    r'(?::\d+)?(?:(?:[/\\]?)[^ "]*[^ ,;.:">)])?',
    re.IGNORECASE
)


def get_title_text(url):
    request = Request(url, headers={'User-Agent': config.USER_AGENT})
    try:
        webpage = BeautifulSoup(urlopen(request, timeout=3))
    except Exception as e:
        # Doesn't really matter what went wrong, abort in any case
        logging.warning("Getting url title failed for {} ({})"
                        .format(url, str(e)))
        return None
    if not webpage or not webpage.title or not webpage.title.string:
        logging.info("No title found for {}".format(url))
        return None
    title = webpage.title.string.strip()
    if re.search(r'\\\\u\d*', title):
        title = codecs.decode(title, 'unicode_escape')
    return re.sub(r"\s{2,}", " ", title)
