import codecs
import logging
import re

from bs4 import BeautifulSoup

import config
from lib.http import try_request

url_regex = re.compile(
    r'(?:https?://)?'
    r'(?:(?:\d+\.\d+\.\d+\.\d+)'
    r'|(?:[\w-]+\.)+[\w-]+)'
    r'(?::\d+)?(?:(?:[/\\]?)[^ "]*[^ ,;.:">)])?',
    re.IGNORECASE
)


def get_title_text(url):
    try:
        markup = try_request(url, headers={'User-Agent': config.USER_AGENT}, log_exception=False)
        webpage = BeautifulSoup(markup, features="html.parser")
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
