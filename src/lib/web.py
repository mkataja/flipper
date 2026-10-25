import codecs
import logging
import re

from bs4 import BeautifulSoup

import config
from lib.http import try_get_response

url_regex = re.compile(
    r'(?:https?://)?'
    r'(?:(?:\d+\.\d+\.\d+\.\d+)'
    r'|(?:[a-z_-]+\.)+[a-z_-]+)'
    r'(?::\d+)?(?:(?:[/\\]?)[^ "]*[^ ,;.:">)])?',
    re.IGNORECASE
)


def get_title_text(url):
    try:
        response = try_get_response(url, headers={'User-Agent': config.USER_AGENT}, log_exception=False)
        if response is None:
            return None
        if response.status >= 400:
            logging.info(f"Not posting title for {url}, got status {response.status}")
            return None
        webpage = BeautifulSoup(response.data, features="html.parser")
    except Exception as e:
        # Doesn't really matter what went wrong, abort in any case
        logging.warning(f"Getting url title failed for {url} ({str(e)})")
        return None
    if not webpage or not webpage.title or not webpage.title.string:
        logging.info(f"No title found for {url}")
        return None
    title = webpage.title.string.strip()
    if re.search(r'\\\\u\d*', title):
        title = codecs.decode(title, 'unicode_escape')
    title = re.sub(r"\s{2,}", " ", title)
    # Some sites serve their 404 page with a 200 status
    if "404" in title and "not found" in title.lower():
        logging.info(f"Not posting title for {url}, it looks like an error page: {title}")
        return None
    return title
